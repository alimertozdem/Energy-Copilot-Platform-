#!/usr/bin/env python3
# =============================================================================
# edge-gateway/modbus_gateway.py
# Energy Copilot Platform - Tier-2 live Modbus TCP ingestion gateway
# =============================================================================
# Polls holding registers on one or more Modbus TCP devices (real meters/PLCs or
# a built-in mock), normalizes each reading via the shared ModbusAdapter, and
# forwards the standard event to a sink (Azure Event Hub in production).
#
# This is the Modbus counterpart to opcua_gateway.py. Modbus is POLL-based (no
# subscriptions), so the run loop reads each configured register every interval.
# It reuses the sink / batching / backoff / graceful-shutdown infrastructure
# from opcua_gateway (single source) and the ModbusAdapter from the shared
# adapter framework.
#
# CONFIG-DRIVEN sensor mapping: the adapter derives sensor_type/unit/scale from
# its REGISTER_MAP keyed by register address. We INJECT that map from our config
# (each point: register -> sensor_type + unit + scale), so no framework edit is
# needed and every site's register map is explicit.
#
# RUN MODES
#   python modbus_gateway.py --selftest
#       No pymodbus / no Azure. Pipes sample registers through adapter -> sink;
#       verifies register-map injection, scaling, batching, backoff, config +
#       platform-config parsing. (CI-friendly, runs anywhere.)
#
#   python modbus_gateway.py --sim [--seconds 6] [--batch 50]
#       Built-in MOCK Modbus device (no pymodbus). Proves the poll -> adapter ->
#       sink loop end-to-end with no hardware.
#
#   python modbus_gateway.py --config config.modbus.<site>.json [--seconds 0]
#       Production: per-site config (devices, register map, sink). Secrets from
#       env (sink.connection_env). Auto-reconnect with backoff.
#
#   python modbus_gateway.py --platform https://api.host --agent-token <T> [--building <UUID>]
#       Pull the device/point map from the platform (/agent/config) so the same
#       config entered in the web app drives the gateway. Token via env too:
#       --agent-token or AGENT_TOKEN.
#
#   python modbus_gateway.py --connect --host 192.168.1.50 --unit-id 1 \
#       --registers 3060:building_kwh:kW:1 3204:building_energy_kwh:kWh:0.01
#       Ad-hoc single device without a config file.
#
# DEPENDENCIES: pip install pymodbus azure-eventhub   (--selftest / --sim need neither)
# =============================================================================

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import pathlib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("modbus_gateway")

# Reuse the verified sink / batching / backoff / graceful-shutdown + json config
# loader from the OPC-UA gateway (single source of truth for that infrastructure).
from opcua_gateway import (  # noqa: E402
    StubSink,
    BufferedSink,
    make_sink,
    backoff_seconds,
    load_config,
    _serve,
)

# pymodbus is OPTIONAL at import time (only --connect / --config / --platform live
# reads need it). Deferring keeps --selftest / --sim runnable anywhere.
try:
    from pymodbus.client import ModbusTcpClient  # noqa: F401
    HAS_PYMODBUS = True
except Exception:
    HAS_PYMODBUS = False


# -----------------------------------------------------------------------------
# Shared adapter (single source of truth). Vendored next to this file in the
# image (Dockerfile), else the repo notebook path for local dev.
# -----------------------------------------------------------------------------
def load_adapter():
    here = pathlib.Path(__file__).resolve().parent
    candidates = [
        here / "iot_adapter_framework.py",                                  # vendored (image)
        here.parent / "notebooks" / "iot" / "00_iot_adapter_framework.py",  # repo dev
    ]
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location("iot_adapter_framework", str(path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.ModbusAdapter()
    raise FileNotFoundError(
        "ModbusAdapter source not found; looked in: " + ", ".join(str(c) for c in candidates)
    )


# -----------------------------------------------------------------------------
# Core: register value -> raw dict -> adapter.normalize() -> sink
# -----------------------------------------------------------------------------
def register_to_raw(point: dict, raw_value, unit_id: int) -> dict:
    """Build the raw dict the ModbusAdapter expects for one register read.

    Optional building_id / device_id / zone are only included when set, so the
    adapter's `.get(key, default)` fallbacks work (a present-but-None key would
    otherwise defeat them)."""
    raw = {
        "slave_id": unit_id,
        "register_address": int(point["register"]),
        "raw_value": raw_value,
        "scale_factor": float(point.get("scale", 1.0) or 1.0),
    }
    if point.get("building_id"):
        raw["building_id"] = point["building_id"]
    if point.get("device_id"):
        raw["device_id"] = point["device_id"]
    if point.get("zone"):
        raw["location"] = point["zone"]
    return raw


class ModbusGateway:
    """One Modbus device: an adapter (with a config-injected register map) + the
    shared sink. ingest() normalizes one register read and forwards it."""

    def __init__(self, sink, points: list):
        self.adapter = load_adapter()
        # Inject the per-site register map (sensor_type / unit / scale per
        # register) so the adapter is fully config-driven, not REGISTER_MAP-bound.
        self.adapter.REGISTER_MAP = {
            int(p["register"]): {
                "sensor_type": p["sensor_type"],
                "unit": p.get("unit") or "unknown",
                "scale": float(p.get("scale", 1.0) or 1.0),
            }
            for p in points
        }
        self.points = points
        self.sink = sink
        self.count = 0

    def ingest(self, raw: dict) -> dict:
        normalized = self.adapter.normalize(raw)
        self.sink.send(normalized)
        self.count += 1
        return normalized

    def flush(self):
        if hasattr(self.sink, "flush"):
            self.sink.flush()


# -----------------------------------------------------------------------------
# Per-site config (declarative device + register map + sink). Secrets via env.
# -----------------------------------------------------------------------------
def build_run_args(cfg: dict) -> dict:
    """Resolve a config dict into concrete run args. Accepts either a top-level
    single device (host/port/unit_id/points) or a `devices` list."""
    if cfg.get("devices"):
        devices = cfg["devices"]
    else:
        devices = [{
            "name": cfg.get("name", "device"),
            "host": cfg["host"],
            "port": int(cfg.get("port", 502)),
            "unit_id": int(cfg.get("unit_id", 1)),
            "points": cfg.get("points", []) or [],
        }]
    # normalize device fields
    norm_devices = []
    for d in devices:
        norm_devices.append({
            "name": d.get("name", "device"),
            "host": d["host"],
            "port": int(d.get("port", 502)),
            "unit_id": int(d.get("unit_id", 1)),
            "points": d.get("points", []) or [],
        })
    sink_cfg = cfg.get("sink", {}) or {}
    if sink_cfg.get("connection_env"):
        eh_conn = os.environ.get(sink_cfg["connection_env"], "")
    else:
        eh_conn = sink_cfg.get("connection", "")
    return {
        "devices": norm_devices,
        "sink_type": sink_cfg.get("type", "stub"),
        "eh_name": sink_cfg.get("eventhub_name", ""),
        "eh_conn": eh_conn,
        "batch": int(cfg.get("batch", 0) or 0),
        "max_retries": int(cfg.get("max_retries", 0) or 0),
        "poll_seconds": int(cfg.get("poll_seconds", 5) or 5),
    }


# -----------------------------------------------------------------------------
# Platform pull: fetch the device/point map from the EnergyLens backend so the
# same config entered in the /connections web UI drives the gateway. Uses only
# stdlib urllib (no extra dependency). The agent authenticates with a building-
# scoped agent token (X-Agent-Token), NOT a user login.
# -----------------------------------------------------------------------------
def fetch_platform_config(base_url: str, agent_token: str, building_id: str = "") -> dict:
    import urllib.request

    url = base_url.rstrip("/") + "/agent/config"
    if building_id:
        url += "?building=" + urllib.parse.quote(building_id)
    req = urllib.request.Request(
        url, headers={"X-Agent-Token": agent_token, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310 (trusted platform URL)
        return json.loads(r.read().decode("utf-8"))


def platform_config_to_devices(payload: dict) -> list:
    """Map an /agent/config payload to gateway device specs, keeping only Modbus
    devices + their enabled points. Payload shape:
      { "building_id": "B005",
        "devices": [ { "name", "protocol", "connection_config": {host,port,unit_id},
                       "points": [ {point_ref, sensor_type, zone, unit, scale, enabled} ] } ] }
    """
    bid = payload.get("building_id") or ""
    out = []
    for d in payload.get("devices", []) or []:
        if (d.get("protocol") or "").lower() != "modbus":
            continue
        cc = d.get("connection_config") or {}
        points = []
        for p in d.get("points", []) or []:
            if p.get("enabled") is False:
                continue
            ref = str(p.get("point_ref", "")).strip()
            if not ref.lstrip("-").isdigit():
                logger.warning("skip non-numeric Modbus point_ref %r on %s", ref, d.get("name"))
                continue
            points.append({
                "register": int(ref),
                "sensor_type": p.get("sensor_type", "unknown"),
                "unit": p.get("unit"),
                "scale": p.get("scale", 1.0),
                "zone": p.get("zone"),
                "building_id": bid,
                "device_id": f"{bid}_{d.get('name', 'dev')}".replace(" ", "_"),
            })
        if not points:
            continue
        out.append({
            "id": d.get("id"),
            "name": d.get("name", "device"),
            "host": cc.get("host", ""),
            "port": int(cc.get("port", 502) or 502),
            "unit_id": int(cc.get("unit_id", 1) or 1),
            "points": points,
        })
    return out


# -----------------------------------------------------------------------------
# Modbus clients: a real pymodbus reader + a dependency-free mock (for --sim).
# Both expose read_register(register, unit_id) -> int | None.
# -----------------------------------------------------------------------------
class RealModbusClient:
    def __init__(self, host: str, port: int):
        self.host, self.port = host, port
        self._client = None

    def connect(self):
        from pymodbus.client import ModbusTcpClient
        self._client = ModbusTcpClient(self.host, port=self.port)
        if not self._client.connect():
            raise ConnectionError(f"Modbus connect failed: {self.host}:{self.port}")

    def read_register(self, register: int, unit_id: int):
        # pymodbus 3.x: read_holding_registers(address, count=1, slave=unit_id)
        rr = self._client.read_holding_registers(register, count=1, slave=unit_id)
        if rr is None or rr.isError() or not getattr(rr, "registers", None):
            return None
        return rr.registers[0]

    def close(self):
        try:
            if self._client:
                self._client.close()
        except Exception:
            pass


class MockModbusClient:
    """Deterministic-ish mock: returns a wandering value per register. No deps."""

    def __init__(self, host="mock", port=502):
        import random
        self._rand = random.Random(42)
        self._base = {}

    def connect(self):
        return True

    def read_register(self, register: int, unit_id: int):
        base = self._base.setdefault(register, 100 + (register % 500))
        return int(base * (0.85 + 0.30 * self._rand.random()))

    def close(self):
        pass


# -----------------------------------------------------------------------------
# Poll loop (async so it reuses _serve's graceful shutdown). Persistent client
# per device with reconnect + exponential backoff.
# -----------------------------------------------------------------------------
async def run_poll(devices: list, sink, seconds: int, interval: int,
                   max_retries: int = 0, mock: bool = False):
    # one gateway (adapter + register map) + one client per device, shared sink
    runners = []
    for spec in devices:
        gw = ModbusGateway(sink, spec["points"])
        client = MockModbusClient(spec["host"], spec["port"]) if mock \
            else RealModbusClient(spec["host"], spec["port"])
        runners.append({"spec": spec, "gw": gw, "client": client, "connected": False, "attempt": 0})

    total = 0
    elapsed = 0
    try:
        while seconds == 0 or elapsed < seconds:
            for r in runners:
                await _poll_one(r, max_retries)
            if hasattr(sink, "flush"):
                sink.flush()
            total = sum(rr["gw"].count for rr in runners)
            await asyncio.sleep(interval)
            elapsed += interval
    finally:
        for r in runners:
            r["client"].close()
        if hasattr(sink, "flush"):
            sink.flush()
    logger.info("POLL - stopped, %d events ingested across %d device(s)", total, len(runners))


async def _poll_one(runner: dict, max_retries: int):
    spec, gw, client = runner["spec"], runner["gw"], runner["client"]
    if not runner["connected"]:
        try:
            client.connect()
            runner["connected"] = True
            runner["attempt"] = 0
        except Exception as e:
            runner["attempt"] += 1
            wait = backoff_seconds(runner["attempt"])
            if max_retries and runner["attempt"] >= max_retries:
                logger.error("POLL - %s giving up after %d attempts (%s)",
                             spec["name"], runner["attempt"], str(e)[:80])
                return
            logger.warning("POLL - %s connect attempt %d failed (%s); retry in %.0fs",
                           spec["name"], runner["attempt"], str(e)[:80], wait)
            await asyncio.sleep(wait)
            return
    for p in spec["points"]:
        try:
            val = client.read_register(int(p["register"]), spec["unit_id"])
            if val is None:
                continue
            gw.ingest(register_to_raw(p, val, spec["unit_id"]))
        except Exception as e:
            logger.warning("POLL - %s read register %s failed (%s); will reconnect",
                           spec["name"], p.get("register"), str(e)[:80])
            runner["connected"] = False
            client.close()
            break


# -----------------------------------------------------------------------------
# --selftest : adapter pipeline + register-map injection + scaling + batching +
# backoff + config + platform-parse  (no pymodbus)
# -----------------------------------------------------------------------------
SAMPLE_POINTS = [
    {"register": 3060, "sensor_type": "building_kwh",        "unit": "kW",   "scale": 1.0,  "building_id": "B005", "device_id": "B005_MM"},
    {"register": 3204, "sensor_type": "building_energy_kwh", "unit": "kWh",  "scale": 0.01, "building_id": "B005", "device_id": "B005_MM"},
    {"register": 100,  "sensor_type": "HVAC_temp",           "unit": "degC", "scale": 0.1,  "building_id": "B001", "device_id": "B001_AHU"},
]
SAMPLE_READS = [(3060, 415), (3204, 1234567), (100, 215)]


def selftest():
    # 1) register-map injection + scaling + sensor_type/building_id
    gw = ModbusGateway(StubSink(), SAMPLE_POINTS)
    for reg, val in SAMPLE_READS:
        p = next(x for x in SAMPLE_POINTS if int(x["register"]) == reg)
        gw.ingest(register_to_raw(p, val, unit_id=1))
    evs = gw.sink.events
    assert evs[0]["sensor_type"] == "building_kwh" and evs[0]["building_id"] == "B005", evs[0]
    assert evs[0]["reading_value"] == 415.0, evs[0]                 # 415 * 1.0
    assert evs[1]["reading_value"] == round(1234567 * 0.01, 4), evs[1]   # scale 0.01
    assert evs[2]["sensor_type"] == "HVAC_temp" and evs[2]["reading_value"] == 21.5, evs[2]  # 215*0.1
    assert all(e["source_protocol"] == "Modbus" for e in evs)
    assert all(e["building_id"] != "UNKNOWN" for e in evs)

    # 2) buffered batching: max_batch=2 over 3 events -> buffer holds 1, flush drains
    stub = StubSink()
    buf = BufferedSink(stub, max_batch=2)
    gw2 = ModbusGateway(buf, SAMPLE_POINTS)
    for reg, val in SAMPLE_READS:
        p = next(x for x in SAMPLE_POINTS if int(x["register"]) == reg)
        gw2.ingest(register_to_raw(p, val, 1))
    assert len(stub.events) == 2, len(stub.events)   # one full batch flushed
    buf.close()
    assert len(stub.events) == 3 and buf._buf == []

    # 3) reconnect backoff curve (shared with opcua_gateway)
    assert backoff_seconds(1) == 2.0 and backoff_seconds(3) == 8.0 and backoff_seconds(10) == 60.0

    # 4) config loader (devices list) + per-point map honored
    cfg_path = pathlib.Path(__file__).resolve().parent / "config.modbus.example.json"
    if cfg_path.exists():
        ra = build_run_args(load_config(str(cfg_path)))
        assert len(ra["devices"]) >= 1 and ra["devices"][0]["host"], ra
        d0 = ra["devices"][0]
        assert len(d0["points"]) >= 1
        gw3 = ModbusGateway(StubSink(), d0["points"])
        p0 = d0["points"][0]
        gw3.ingest(register_to_raw(p0, 1000, d0["unit_id"]))
        assert gw3.sink.events[0]["sensor_type"] == p0["sensor_type"], gw3.sink.events[0]
        logger.info("SELFTEST - config loader OK (%d device(s); per-point map honored)", len(ra["devices"]))

    # 5) platform-config parser keeps only Modbus + numeric registers
    payload = {
        "building_id": "B005",
        "devices": [
            {"name": "Main meter", "protocol": "modbus",
             "connection_config": {"host": "10.0.0.5", "port": 502, "unit_id": 1},
             "points": [
                 {"point_ref": "3060", "sensor_type": "building_kwh", "unit": "kW", "scale": 1.0, "enabled": True},
                 {"point_ref": "AI:1", "sensor_type": "HVAC_temp", "enabled": True},   # non-numeric -> skipped
                 {"point_ref": "3204", "sensor_type": "building_energy_kwh", "enabled": False},  # disabled -> skipped
             ]},
            {"name": "AHU", "protocol": "bacnet", "connection_config": {}, "points": []},  # non-modbus -> skipped
        ],
    }
    devs = platform_config_to_devices(payload)
    assert len(devs) == 1 and devs[0]["host"] == "10.0.0.5", devs
    assert len(devs[0]["points"]) == 1 and devs[0]["points"][0]["register"] == 3060, devs[0]["points"]
    assert devs[0]["points"][0]["building_id"] == "B005"

    logger.info("SELFTEST OK - adapter+map (%d) + batching + backoff + config + platform-parse verified",
                gw.count)


# -----------------------------------------------------------------------------
# --connect ad-hoc register spec parsing: "REG:sensor_type[:unit[:scale]]"
# -----------------------------------------------------------------------------
def parse_register_specs(specs: list, building_id: str = "") -> list:
    points = []
    for s in specs:
        parts = s.split(":")
        reg = int(parts[0])
        sensor_type = parts[1] if len(parts) > 1 else "unknown"
        unit = parts[2] if len(parts) > 2 else None
        scale = float(parts[3]) if len(parts) > 3 else 1.0
        points.append({"register": reg, "sensor_type": sensor_type, "unit": unit,
                       "scale": scale, "building_id": building_id})
    return points


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def _run(devices, sink_type, eh_conn, eh_name, batch, seconds, interval, max_retries, mock):
    sink = make_sink(sink_type, eh_conn, eh_name, batch)
    npoints = sum(len(d["points"]) for d in devices)
    logger.info("MODBUS - %d device(s), %d point(s), sink=%s, batch=%d, every %ds%s",
                len(devices), npoints, sink.name, batch, interval, " (mock)" if mock else "")
    asyncio.run(_serve(run_poll(devices, sink, seconds, interval, max_retries, mock), sink))


def main():
    p = argparse.ArgumentParser(description="EnergyLens Modbus TCP ingestion gateway")
    p.add_argument("--selftest", action="store_true",
                   help="adapter + register-map + batching + backoff + config (no pymodbus)")
    p.add_argument("--sim", action="store_true", help="built-in mock Modbus device (no pymodbus)")
    p.add_argument("--connect", action="store_true", help="connect to a real Modbus device")
    p.add_argument("--config", metavar="PATH", help="per-site JSON config (devices, points, sink)")
    p.add_argument("--platform", metavar="BASE_URL", help="pull node-map from EnergyLens /agent/config")
    p.add_argument("--agent-token", default="", help="building-scoped agent token (or env AGENT_TOKEN)")
    p.add_argument("--building", default="", help="building UUID for --platform (optional)")
    p.add_argument("--host", default="", help="Modbus host/IP for --connect")
    p.add_argument("--port", type=int, default=502)
    p.add_argument("--unit-id", type=int, default=1, help="Modbus slave/unit id for --connect")
    p.add_argument("--registers", nargs="*", default=[],
                   help='--connect register specs "REG:sensor_type[:unit[:scale]]"')
    p.add_argument("--building-id", default="", help="building_id tag for --connect points")
    p.add_argument("--seconds", type=int, default=6, help="run duration; 0 = until stopped")
    p.add_argument("--interval", type=int, default=5, help="poll interval seconds")
    p.add_argument("--sink", choices=["stub", "eventhub"], default="stub")
    p.add_argument("--batch", type=int, default=0, help="buffer N events per send (0 = no batching)")
    p.add_argument("--eh-conn", default="", help="Event Hub connection string")
    p.add_argument("--eh-name", default="", help="Event Hub name")
    p.add_argument("--max-retries", type=int, default=0, help="reconnect cap (0 = forever)")
    a = p.parse_args()

    if a.selftest:
        selftest()
        return

    if a.sim:
        sim_devices = [{"name": "mock-meter", "host": "mock", "port": 502, "unit_id": 1,
                        "points": SAMPLE_POINTS}]
        _run(sim_devices, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval,
             a.max_retries, mock=True)
        return

    if a.platform:
        token = a.agent_token or os.environ.get("AGENT_TOKEN", "")
        if not token:
            raise SystemExit("--platform needs --agent-token or AGENT_TOKEN env")
        payload = fetch_platform_config(a.platform, token, a.building)
        devices = platform_config_to_devices(payload)
        if not devices:
            raise SystemExit("no Modbus devices with mappable points in the platform config")
        ra_batch = int(payload.get("batch", a.batch) or a.batch)
        _run(devices, a.sink, a.eh_conn, a.eh_name, ra_batch, a.seconds, a.interval, a.max_retries, mock=False)
        return

    if a.config:
        ra = build_run_args(load_config(a.config))
        _run(ra["devices"], ra["sink_type"], ra["eh_conn"], ra["eh_name"], ra["batch"],
             a.seconds, ra["poll_seconds"], ra["max_retries"], mock=False)
        return

    if a.connect:
        if not HAS_PYMODBUS:
            raise SystemExit("pymodbus not installed. `pip install pymodbus` for --connect/--config/--platform.")
        if not a.host or not a.registers:
            raise SystemExit("--connect needs --host and --registers")
        devices = [{"name": "device", "host": a.host, "port": a.port, "unit_id": a.unit_id,
                    "points": parse_register_specs(a.registers, a.building_id)}]
        _run(devices, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=False)
        return

    p.print_help()


if __name__ == "__main__":
    main()
