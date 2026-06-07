#!/usr/bin/env python3
# =============================================================================
# edge-gateway/bacnet_gateway.py
# Energy Copilot Platform - Tier-2 live BACnet/IP ingestion gateway
# =============================================================================
# BACnet/IP (ASHRAE 135) is THE building-automation standard in German
# commercial buildings (AHUs, chillers, heat pumps, controllers). This gateway
# polls the configured objects on each device, normalizes each reading via the
# shared BacnetAdapter, and forwards the standard event to a sink (Event Hub).
#
# Like modbus_gateway.py it is config-driven and reuses the verified sink /
# batching / backoff / graceful-shutdown infrastructure from opcua_gateway. The
# adapter derives sensor_type from a free-text description heuristic; because our
# /connections config carries an EXPLICIT sensor_type per object, the gateway
# OVERRIDES the adapter's guess with the configured value after normalize (the
# adapter still handles value/unit conversion + quality). No framework edit.
#
# point_ref format: "<objtype>:<instance>", e.g. "AI:1" (analogInput 1),
#   "AV:3" (analogValue 3), "BI:2" (binaryInput 2), "MSV:1" (multiStateValue 1).
#
# RUN MODES
#   python bacnet_gateway.py --selftest      # adapter + override + config + platform (no deps)
#   python bacnet_gateway.py --sim           # built-in MOCK device (no BAC0)
#   python bacnet_gateway.py --config config.bacnet.<site>.json
#   python bacnet_gateway.py --platform https://api.host --agent-token <T>
#   python bacnet_gateway.py --connect --host 192.168.1.60 --device-instance 1001 \
#       --objects AI:1:HVAC_supply_temp AI:2:CO2 --building-id B001
#
# DEPENDENCIES: pip install BAC0 azure-eventhub   (--selftest / --sim need neither)
# =============================================================================

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import pathlib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bacnet_gateway")

# Reuse the verified sink / batching / backoff / graceful-shutdown + config loader.
from opcua_gateway import (  # noqa: E402
    StubSink,
    BufferedSink,
    make_sink,
    backoff_seconds,
    load_config,
    _serve,
)

# BAC0 is OPTIONAL at import time (only --connect / --config / --platform live
# reads need it). --selftest / --sim use a dependency-free mock.
try:
    import BAC0  # noqa: F401
    HAS_BAC0 = True
except Exception:
    HAS_BAC0 = False

# BACnet object-type short codes -> ASHRAE object names.
_OBJ_TYPE = {
    "AI": "analogInput", "AO": "analogOutput", "AV": "analogValue",
    "BI": "binaryInput", "BO": "binaryOutput", "BV": "binaryValue",
    "MSV": "multiStateValue", "MSI": "multiStateInput",
}


def parse_object_ref(ref):
    """'AI:1' -> ('analogInput', 1); returns None if not a valid object ref."""
    parts = str(ref).strip().split(":")
    if len(parts) != 2:
        return None
    otype = _OBJ_TYPE.get(parts[0].strip().upper())
    inst = parts[1].strip()
    if not otype or not inst.lstrip("-").isdigit():
        return None
    return (otype, int(inst))


def load_adapter():
    here = pathlib.Path(__file__).resolve().parent
    candidates = [
        here / "iot_adapter_framework.py",
        here.parent / "notebooks" / "iot" / "00_iot_adapter_framework.py",
    ]
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location("iot_adapter_framework", str(path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.BacnetAdapter()
    raise FileNotFoundError(
        "BacnetAdapter source not found; looked in: " + ", ".join(str(c) for c in candidates)
    )


def point_to_raw(point: dict, value, units, device_instance: int) -> dict:
    """Build the raw dict the BacnetAdapter expects for one object read."""
    parsed = parse_object_ref(point["object_ref"])
    otype, oinst = parsed if parsed else ("analogInput", -1)
    raw = {
        "device_instance": device_instance,
        "object_type": otype,
        "object_instance": oinst,
        "value": value,
        "units": units or point.get("unit") or "unknown",
        "description": point.get("zone") or "",
    }
    if point.get("building_id"):
        raw["building_id"] = point["building_id"]
    if point.get("device_id"):
        raw["device_id"] = point["device_id"]
    if point.get("zone"):
        raw["location"] = point["zone"]
    return raw


class BacnetGateway:
    """Adapter + sink. ingest() normalizes one object read, then OVERRIDES the
    adapter's heuristic sensor_type with the configured one."""

    def __init__(self, sink, points: list):
        self.adapter = load_adapter()
        self.points = points
        self.sink = sink
        self.count = 0

    def ingest(self, raw: dict, sensor_type: str | None = None) -> dict:
        norm = self.adapter.normalize(raw)
        if sensor_type:
            norm["sensor_type"] = sensor_type
        self.sink.send(norm)
        self.count += 1
        return norm

    def flush(self):
        if hasattr(self.sink, "flush"):
            self.sink.flush()


def build_run_args(cfg: dict) -> dict:
    if cfg.get("devices"):
        devices = cfg["devices"]
    else:
        devices = [{
            "name": cfg.get("name", "device"),
            "host": cfg["host"],
            "device_instance": int(cfg.get("device_instance", 0)),
            "port": int(cfg.get("port", 47808)),
            "points": cfg.get("points", []) or [],
        }]
    norm_devices = []
    for d in devices:
        norm_devices.append({
            "name": d.get("name", "device"),
            "host": d["host"],
            "device_instance": int(d.get("device_instance", 0)),
            "port": int(d.get("port", 47808)),
            "points": d.get("points", []) or [],
        })
    sink_cfg = cfg.get("sink", {}) or {}
    eh_conn = os.environ.get(sink_cfg["connection_env"], "") if sink_cfg.get("connection_env") \
        else sink_cfg.get("connection", "")
    return {
        "devices": norm_devices,
        "sink_type": sink_cfg.get("type", "stub"),
        "eh_name": sink_cfg.get("eventhub_name", ""),
        "eh_conn": eh_conn,
        "batch": int(cfg.get("batch", 0) or 0),
        "max_retries": int(cfg.get("max_retries", 0) or 0),
        "poll_seconds": int(cfg.get("poll_seconds", 10) or 10),
    }


def fetch_platform_config(base_url: str, agent_token: str, building_id: str = "") -> dict:
    import urllib.parse
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
    """Keep only BACnet devices + their enabled, valid-object-ref points."""
    bid = payload.get("building_id") or ""
    out = []
    for d in payload.get("devices", []) or []:
        if (d.get("protocol") or "").lower() != "bacnet":
            continue
        cc = d.get("connection_config") or {}
        points = []
        for p in d.get("points", []) or []:
            if p.get("enabled") is False:
                continue
            ref = str(p.get("point_ref", "")).strip()
            if parse_object_ref(ref) is None:
                logger.warning("skip non-BACnet point_ref %r on %s", ref, d.get("name"))
                continue
            points.append({
                "object_ref": ref,
                "sensor_type": p.get("sensor_type", "unknown"),
                "unit": p.get("unit"),
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
            "device_instance": int(cc.get("device_instance", 0) or 0),
            "port": int(cc.get("port", 47808) or 47808),
            "points": points,
        })
    return out


# -----------------------------------------------------------------------------
# Clients: real BAC0 reader + dependency-free mock (for --sim).
# read_object(object_ref, unit_hint) -> (value, units) | (None, None)
# -----------------------------------------------------------------------------
class RealBacnetClient:
    def __init__(self, host: str, device_instance: int, port: int = 47808):
        self.host, self.device_instance, self.port = host, device_instance, port
        self._bac = None

    def connect(self):
        import BAC0
        self._bac = BAC0.lite()

    def read_object(self, object_ref: str, unit_hint=None):
        parsed = parse_object_ref(object_ref)
        if parsed is None:
            return None, None
        otype, oinst = parsed
        val = self._bac.read(f"{self.host} {otype} {oinst} presentValue")
        try:
            units = self._bac.read(f"{self.host} {otype} {oinst} units")
        except Exception:
            units = unit_hint or "unknown"
        return val, str(units)

    def close(self):
        try:
            if self._bac:
                self._bac.disconnect()
        except Exception:
            pass


class MockBacnetClient:
    """Dependency-free mock BACnet device for --sim. Echoes the configured unit."""

    def __init__(self, host="mock", device_instance=0, port=47808):
        import random
        self._rand = random.Random(11)
        self._base = {}

    def connect(self):
        return True

    def read_object(self, object_ref: str, unit_hint=None):
        base = self._base.setdefault(object_ref, 20.0 + (hash(object_ref) % 30))
        val = round(base * (0.9 + 0.2 * self._rand.random()), 2)
        return val, (unit_hint or "degrees_celsius")

    def close(self):
        pass


# -----------------------------------------------------------------------------
# Poll loop (async; reuses _serve graceful shutdown). One client per device.
# -----------------------------------------------------------------------------
async def run_poll(devices: list, sink, seconds: int, interval: int,
                   max_retries: int = 0, mock: bool = False):
    runners = []
    for spec in devices:
        gw = BacnetGateway(sink, spec["points"])
        client = MockBacnetClient(spec["host"], spec["device_instance"]) if mock \
            else RealBacnetClient(spec["host"], spec["device_instance"], spec["port"])
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
            val, units = client.read_object(p["object_ref"], p.get("unit"))
            if val is None:
                continue
            gw.ingest(point_to_raw(p, val, units, spec["device_instance"]),
                      sensor_type=p.get("sensor_type"))
        except Exception as e:
            logger.warning("POLL - %s read %s failed (%s); will reconnect",
                           spec["name"], p.get("object_ref"), str(e)[:80])
            runner["connected"] = False
            client.close()
            break


# -----------------------------------------------------------------------------
# --selftest
# -----------------------------------------------------------------------------
SAMPLE_POINTS = [
    {"object_ref": "AI:1", "sensor_type": "HVAC_supply_temp", "unit": "degC", "building_id": "B001", "device_id": "B001_AHU", "zone": "AHU-1"},
    {"object_ref": "AI:2", "sensor_type": "CO2",              "unit": "ppm",  "building_id": "B001", "zone": "Return air"},
]
SAMPLE_READS = [("AI:1", 57.2, "degrees_fahrenheit"), ("AI:2", 850, "ppm")]


def selftest():
    # 1) sensor_type override + value/unit conversion (F -> C) + building_id
    gw = BacnetGateway(StubSink(), SAMPLE_POINTS)
    for ref, val, units in SAMPLE_READS:
        p = next(x for x in SAMPLE_POINTS if x["object_ref"] == ref)
        gw.ingest(point_to_raw(p, val, units, device_instance=1001), sensor_type=p["sensor_type"])
    e = gw.sink.events
    assert e[0]["sensor_type"] == "HVAC_supply_temp", e[0]      # config override, not heuristic
    assert e[0]["reading_value"] == 14.0 and e[0]["reading_unit"] == "C", e[0]   # 57.2F -> 14C
    assert e[0]["building_id"] == "B001", e[0]
    assert e[1]["sensor_type"] == "CO2" and e[1]["reading_value"] == 850.0, e[1]
    assert all(x["source_protocol"] == "BACnet" for x in e)

    # 2) object-ref parsing
    assert parse_object_ref("AI:1") == ("analogInput", 1)
    assert parse_object_ref("MSV:3") == ("multiStateValue", 3)
    assert parse_object_ref("3060") is None and parse_object_ref("AI:x") is None

    # 3) batching + backoff
    stub = StubSink()
    buf = BufferedSink(stub, max_batch=2)
    gw2 = BacnetGateway(buf, SAMPLE_POINTS)
    for ref, val, units in SAMPLE_READS:
        p = next(x for x in SAMPLE_POINTS if x["object_ref"] == ref)
        gw2.ingest(point_to_raw(p, val, units, 1001), sensor_type=p["sensor_type"])
    assert len(stub.events) == 2
    buf.close()
    assert buf._buf == []
    assert backoff_seconds(1) == 2.0 and backoff_seconds(10) == 60.0

    # 4) config loader
    cfg_path = pathlib.Path(__file__).resolve().parent / "config.bacnet.example.json"
    if cfg_path.exists():
        ra = build_run_args(load_config(str(cfg_path)))
        assert len(ra["devices"]) >= 1 and ra["devices"][0]["host"]
        d0 = ra["devices"][0]
        gw3 = BacnetGateway(StubSink(), d0["points"])
        p0 = d0["points"][0]
        gw3.ingest(point_to_raw(p0, 21.0, "degrees_celsius", d0["device_instance"]),
                   sensor_type=p0["sensor_type"])
        assert gw3.sink.events[0]["sensor_type"] == p0["sensor_type"]
        logger.info("SELFTEST - config loader OK (%d device(s))", len(ra["devices"]))

    # 5) platform-config parser keeps only BACnet + valid object refs
    payload = {
        "building_id": "B001",
        "devices": [
            {"name": "AHU-1", "protocol": "bacnet",
             "connection_config": {"host": "10.0.0.6", "device_instance": 1001, "port": 47808},
             "points": [
                 {"point_ref": "AI:1", "sensor_type": "HVAC_supply_temp", "unit": "degC", "enabled": True},
                 {"point_ref": "3060", "sensor_type": "building_kwh", "enabled": True},     # not a BACnet ref
                 {"point_ref": "AI:2", "sensor_type": "CO2", "enabled": False},             # disabled
             ]},
            {"name": "Meter", "protocol": "modbus", "connection_config": {}, "points": []},  # non-bacnet
        ],
    }
    devs = platform_config_to_devices(payload)
    assert len(devs) == 1 and devs[0]["host"] == "10.0.0.6" and devs[0]["device_instance"] == 1001, devs
    assert len(devs[0]["points"]) == 1 and devs[0]["points"][0]["object_ref"] == "AI:1", devs[0]["points"]
    assert devs[0]["points"][0]["building_id"] == "B001"

    logger.info("SELFTEST OK - adapter+override (%d) + F->C + parse + batching + backoff + config + platform verified",
                gw.count)


def parse_object_specs(specs: list, building_id: str = "") -> list:
    """--connect object specs: 'OBJREF:sensor_type[:unit]'  e.g. 'AI:1:HVAC_temp:degC'."""
    points = []
    for s in specs:
        parts = s.split(":")
        # object ref is the first TWO colon-separated tokens (e.g. AI:1)
        object_ref = f"{parts[0]}:{parts[1]}"
        sensor_type = parts[2] if len(parts) > 2 else "unknown"
        unit = parts[3] if len(parts) > 3 else None
        points.append({"object_ref": object_ref, "sensor_type": sensor_type,
                       "unit": unit, "building_id": building_id})
    return points


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def _run(devices, sink_type, eh_conn, eh_name, batch, seconds, interval, max_retries, mock):
    sink = make_sink(sink_type, eh_conn, eh_name, batch)
    npoints = sum(len(d["points"]) for d in devices)
    logger.info("BACnet - %d device(s), %d object(s), sink=%s, batch=%d, every %ds%s",
                len(devices), npoints, sink.name, batch, interval, " (mock)" if mock else "")
    asyncio.run(_serve(run_poll(devices, sink, seconds, interval, max_retries, mock), sink))


def main():
    p = argparse.ArgumentParser(description="EnergyLens BACnet/IP ingestion gateway")
    p.add_argument("--selftest", action="store_true",
                   help="adapter + override + parse + batching + backoff + config (no BAC0)")
    p.add_argument("--sim", action="store_true", help="built-in mock BACnet device (no BAC0)")
    p.add_argument("--connect", action="store_true", help="connect to a real BACnet device")
    p.add_argument("--config", metavar="PATH", help="per-site JSON config")
    p.add_argument("--platform", metavar="BASE_URL", help="pull node-map from EnergyLens /agent/config")
    p.add_argument("--agent-token", default="", help="building-scoped agent token (or env AGENT_TOKEN)")
    p.add_argument("--building", default="", help="building UUID for --platform (optional)")
    p.add_argument("--host", default="", help="BACnet device IP for --connect")
    p.add_argument("--device-instance", type=int, default=0)
    p.add_argument("--port", type=int, default=47808)
    p.add_argument("--objects", nargs="*", default=[],
                   help='--connect object specs "OBJREF:sensor_type[:unit]" e.g. AI:1:HVAC_temp')
    p.add_argument("--building-id", default="", help="building_id tag for --connect objects")
    p.add_argument("--seconds", type=int, default=6)
    p.add_argument("--interval", type=int, default=10, help="poll interval seconds")
    p.add_argument("--sink", choices=["stub", "eventhub"], default="stub")
    p.add_argument("--batch", type=int, default=0)
    p.add_argument("--eh-conn", default="")
    p.add_argument("--eh-name", default="")
    p.add_argument("--max-retries", type=int, default=0)
    a = p.parse_args()

    if a.selftest:
        selftest()
        return

    if a.sim:
        sim_devices = [{"name": "mock-ahu", "host": "mock", "device_instance": 1001,
                        "port": 47808, "points": SAMPLE_POINTS}]
        _run(sim_devices, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=True)
        return

    if a.platform:
        token = a.agent_token or os.environ.get("AGENT_TOKEN", "")
        if not token:
            raise SystemExit("--platform needs --agent-token or AGENT_TOKEN env")
        payload = fetch_platform_config(a.platform, token, a.building)
        devices = platform_config_to_devices(payload)
        if not devices:
            raise SystemExit("no BACnet devices with mappable objects in the platform config")
        _run(devices, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=False)
        return

    if a.config:
        ra = build_run_args(load_config(a.config))
        _run(ra["devices"], ra["sink_type"], ra["eh_conn"], ra["eh_name"], ra["batch"],
             a.seconds, ra["poll_seconds"], ra["max_retries"], mock=False)
        return

    if a.connect:
        if not HAS_BAC0:
            raise SystemExit("BAC0 not installed. `pip install BAC0` for --connect/--config/--platform.")
        if not a.host or not a.objects:
            raise SystemExit("--connect needs --host and --objects")
        devices = [{"name": "device", "host": a.host, "device_instance": a.device_instance,
                    "port": a.port, "points": parse_object_specs(a.objects, a.building_id)}]
        _run(devices, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=False)
        return

    p.print_help()


if __name__ == "__main__":
    main()
