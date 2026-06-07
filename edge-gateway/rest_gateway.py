#!/usr/bin/env python3
# =============================================================================
# edge-gateway/rest_gateway.py
# Energy Copilot Platform - Tier-2 live REST API ingestion gateway
# =============================================================================
# REST/HTTP-JSON is the catch-all for cloud-connected devices, sub-meters with
# web dashboards, and any vendor exposing an HTTP endpoint. This gateway GETs
# each device endpoint every --interval, extracts the configured points
# (point_ref = a field or dotted path in the JSON response), normalizes via the
# shared RestApiAdapter, and forwards to the same sink → Event Hub path.
#
# Poll-based like modbus_gateway. Uses only the Python stdlib (urllib) for the
# live HTTP GET — NO extra dependency — and reuses the verified sink / batching /
# backoff / graceful-shutdown infrastructure from opcua_gateway. The
# RestApiAdapter already honours explicit fields, so configured sensor_type /
# building_id / unit pass straight through (no framework edit).
#
# point_ref = a field (or dotted path) in the JSON response, e.g. "activePower"
#   or "data.meter.power".
#
# RUN MODES
#   python rest_gateway.py --selftest      # adapter + extract + config + platform (no deps)
#   python rest_gateway.py --sim           # built-in mock endpoint (no network)
#   python rest_gateway.py --config config.rest.<site>.json
#   python rest_gateway.py --platform https://api.host --agent-token <T>
#   python rest_gateway.py --connect --endpoint https://meter/api/readings \
#       --points activePower:building_kwh:kW --building-id B004
#
# DEPENDENCIES: pip install azure-eventhub   (only for --sink eventhub; HTTP uses stdlib)
# =============================================================================

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import pathlib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("rest_gateway")

from opcua_gateway import (  # noqa: E402
    StubSink,
    BufferedSink,
    make_sink,
    backoff_seconds,
    load_config,
    _serve,
)


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
            return mod.RestApiAdapter()
    raise FileNotFoundError(
        "RestApiAdapter source not found; looked in: " + ", ".join(str(c) for c in candidates)
    )


def extract_path(obj, path):
    """Read a field or dotted path ('data.meter.power') from a JSON object."""
    cur = obj
    for part in str(path).split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


class RestGateway:
    """Adapter + sink. poll_once(response) emits one normalized event per
    configured point whose field is present in the JSON response."""

    def __init__(self, sink, points: list):
        self.adapter = load_adapter()
        self.points = points
        self.sink = sink
        self.count = 0

    def poll_once(self, response: dict) -> int:
        ts = None
        if isinstance(response, dict):
            ts = response.get("measuredAt") or response.get("timestamp")
        emitted = 0
        for p in self.points:
            val = extract_path(response, p["point_ref"])
            if val is None:
                continue
            raw = {"value": val, "sensor_type": p["sensor_type"]}
            if p.get("unit"):
                raw["unit"] = p["unit"]
            if ts:
                raw["timestamp"] = ts
            if p.get("building_id"):
                raw["building_id"] = p["building_id"]
            if p.get("device_id"):
                raw["device_id"] = p["device_id"]
            if p.get("zone"):
                raw["location"] = p["zone"]
            norm = self.adapter.normalize(raw)
            self.sink.send(norm)
            self.count += 1
            emitted += 1
        return emitted

    def flush(self):
        if hasattr(self.sink, "flush"):
            self.sink.flush()


def http_get_json(endpoint: str, auth_header: str = "", timeout: int = 15):
    import urllib.request

    headers = {"Accept": "application/json"}
    if auth_header:
        headers["Authorization"] = auth_header
    req = urllib.request.Request(endpoint, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (operator-configured endpoint)
        return json.loads(r.read().decode("utf-8"))


def build_run_args(cfg: dict) -> dict:
    if cfg.get("devices"):
        devices = cfg["devices"]
    else:
        devices = [{
            "name": cfg.get("name", "device"),
            "endpoint": cfg["endpoint"],
            "auth_env": cfg.get("auth_env"),
            "points": cfg.get("points", []) or [],
        }]
    norm = []
    for d in devices:
        auth = os.environ.get(d["auth_env"], "") if d.get("auth_env") else d.get("auth_header", "")
        norm.append({
            "name": d.get("name", "device"),
            "endpoint": d["endpoint"],
            "auth_header": auth or "",
            "points": d.get("points", []) or [],
        })
    sink_cfg = cfg.get("sink", {}) or {}
    eh_conn = os.environ.get(sink_cfg["connection_env"], "") if sink_cfg.get("connection_env") \
        else sink_cfg.get("connection", "")
    return {
        "devices": norm,
        "sink_type": sink_cfg.get("type", "stub"),
        "eh_name": sink_cfg.get("eventhub_name", ""),
        "eh_conn": eh_conn,
        "batch": int(cfg.get("batch", 0) or 0),
        "max_retries": int(cfg.get("max_retries", 0) or 0),
        "poll_seconds": int(cfg.get("poll_seconds", 30) or 30),
    }


def fetch_platform_config(base_url: str, agent_token: str, building_id: str = "") -> dict:
    import urllib.parse
    import urllib.request

    url = base_url.rstrip("/") + "/agent/config"
    if building_id:
        url += "?building=" + urllib.parse.quote(building_id)
    req = urllib.request.Request(url, headers={"X-Agent-Token": agent_token, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def platform_config_to_devices(payload: dict) -> list:
    """Keep only REST devices + their enabled points (point_ref = a JSON field)."""
    bid = payload.get("building_id") or ""
    out = []
    for d in payload.get("devices", []) or []:
        if (d.get("protocol") or "").lower() != "rest_api":
            continue
        cc = d.get("connection_config") or {}
        points = []
        for p in d.get("points", []) or []:
            if p.get("enabled") is False:
                continue
            ref = str(p.get("point_ref", "")).strip()
            if not ref:
                continue
            points.append({
                "point_ref": ref,
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
            "endpoint": cc.get("endpoint", ""),
            "auth_header": cc.get("auth_header", ""),
            "points": points,
        })
    return out


# -----------------------------------------------------------------------------
# Poll loop (async; reuses _serve). One HTTP GET per device per interval.
# -----------------------------------------------------------------------------
async def run_poll(devices: list, sink, seconds: int, interval: int,
                   max_retries: int = 0, mock: bool = False):
    gateways = [(spec, RestGateway(sink, spec["points"])) for spec in devices]
    attempts = {spec["name"]: 0 for spec in devices}
    total = 0
    elapsed = 0
    try:
        while seconds == 0 or elapsed < seconds:
            for spec, gw in gateways:
                try:
                    resp = _mock_response(spec) if mock else http_get_json(spec["endpoint"], spec.get("auth_header", ""))
                    gw.poll_once(resp)
                    attempts[spec["name"]] = 0
                except Exception as e:
                    attempts[spec["name"]] += 1
                    wait = backoff_seconds(attempts[spec["name"]])
                    if max_retries and attempts[spec["name"]] >= max_retries:
                        logger.error("REST - %s giving up after %d attempts (%s)",
                                     spec["name"], attempts[spec["name"]], str(e)[:80])
                        continue
                    logger.warning("REST - %s GET failed (%s); backing off %.0fs",
                                   spec["name"], str(e)[:80], wait)
                    await asyncio.sleep(wait)
            if hasattr(sink, "flush"):
                sink.flush()
            total = sum(gw.count for _, gw in gateways)
            await asyncio.sleep(interval)
            elapsed += interval
    finally:
        if hasattr(sink, "flush"):
            sink.flush()
    logger.info("REST - stopped, %d events ingested across %d device(s)", total, len(devices))


def _mock_response(spec) -> dict:
    import random
    resp = {"measuredAt": "2026-06-05T12:00:00Z"}
    for p in spec["points"]:
        # write the value at the (possibly dotted) point_ref path
        cur = resp
        parts = str(p["point_ref"]).split(".")
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = round(10 + 80 * random.random(), 2)
    return resp


# -----------------------------------------------------------------------------
# --selftest
# -----------------------------------------------------------------------------
SAMPLE_POINTS = [
    {"point_ref": "activePower", "sensor_type": "building_kwh", "unit": "kW",   "building_id": "B004", "device_id": "B004_MAIN", "zone": "Main DB"},
    {"point_ref": "data.temp",   "sensor_type": "HVAC_temp",    "unit": "degC", "building_id": "B004"},
]
SAMPLE_RESPONSE = {"activePower": 45.2, "data": {"temp": 21.0}, "measuredAt": "2026-06-05T12:00:00Z"}


def selftest():
    # 1) field + dotted-path extraction; explicit sensor_type/building_id honored
    gw = RestGateway(StubSink(), SAMPLE_POINTS)
    emitted = gw.poll_once(SAMPLE_RESPONSE)
    assert emitted == 2, emitted
    e = gw.sink.events
    assert e[0]["sensor_type"] == "building_kwh" and e[0]["reading_value"] == 45.2, e[0]
    assert e[0]["building_id"] == "B004" and e[0]["reading_unit"] == "kW", e[0]
    assert e[1]["sensor_type"] == "HVAC_temp" and e[1]["reading_value"] == 21.0, e[1]   # dotted path
    assert all(x["source_protocol"] == "REST" for x in e)

    # 2) extract_path
    assert extract_path({"a": {"b": 3}}, "a.b") == 3
    assert extract_path({"a": 1}, "a.b") is None and extract_path({}, "x") is None

    # 3) missing field -> skipped
    gw2 = RestGateway(StubSink(), SAMPLE_POINTS)
    assert gw2.poll_once({"activePower": 10.0}) == 1

    # 4) batching + backoff
    stub = StubSink()
    buf = BufferedSink(stub, max_batch=2)
    gw3 = RestGateway(buf, SAMPLE_POINTS)
    gw3.poll_once(SAMPLE_RESPONSE)
    assert len(stub.events) == 2
    buf.close()
    assert buf._buf == []
    assert backoff_seconds(1) == 2.0 and backoff_seconds(10) == 60.0

    # 5) config loader
    cfg_path = pathlib.Path(__file__).resolve().parent / "config.rest.example.json"
    if cfg_path.exists():
        ra = build_run_args(load_config(str(cfg_path)))
        assert len(ra["devices"]) >= 1 and ra["devices"][0]["endpoint"]
        logger.info("SELFTEST - config loader OK (%d device(s))", len(ra["devices"]))

    # 6) platform-config parser keeps only rest_api devices
    payload = {
        "building_id": "B004",
        "devices": [
            {"name": "Cloud meter", "protocol": "rest_api",
             "connection_config": {"endpoint": "https://api.example.com/r", "auth_header": "Bearer x"},
             "points": [
                 {"point_ref": "activePower", "sensor_type": "building_kwh", "unit": "kW", "enabled": True},
                 {"point_ref": "temp", "sensor_type": "HVAC_temp", "enabled": False},
             ]},
            {"name": "Meter", "protocol": "modbus", "connection_config": {}, "points": []},
        ],
    }
    devs = platform_config_to_devices(payload)
    assert len(devs) == 1 and devs[0]["endpoint"] == "https://api.example.com/r", devs
    assert len(devs[0]["points"]) == 1 and devs[0]["points"][0]["point_ref"] == "activePower"
    assert devs[0]["points"][0]["building_id"] == "B004"

    logger.info("SELFTEST OK - RestApiAdapter (%d) + extract + batching + backoff + config + platform verified", gw.count)


def parse_point_specs(specs: list, building_id: str = "") -> list:
    """--connect point specs: 'FIELD:sensor_type[:unit]'  e.g. 'activePower:building_kwh:kW'."""
    points = []
    for s in specs:
        parts = s.split(":")
        points.append({
            "point_ref": parts[0],
            "sensor_type": parts[1] if len(parts) > 1 else "unknown",
            "unit": parts[2] if len(parts) > 2 else None,
            "building_id": building_id,
        })
    return points


def _run(devices, sink_type, eh_conn, eh_name, batch, seconds, interval, max_retries, mock):
    sink = make_sink(sink_type, eh_conn, eh_name, batch)
    npoints = sum(len(d["points"]) for d in devices)
    logger.info("REST - %d endpoint(s), %d point(s), sink=%s, batch=%d, every %ds%s",
                len(devices), npoints, sink.name, batch, interval, " (mock)" if mock else "")
    asyncio.run(_serve(run_poll(devices, sink, seconds, interval, max_retries, mock), sink))


def main():
    p = argparse.ArgumentParser(description="EnergyLens REST API ingestion gateway")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--sim", action="store_true", help="built-in mock endpoint (no network)")
    p.add_argument("--connect", action="store_true", help="poll a real HTTP endpoint")
    p.add_argument("--config", metavar="PATH")
    p.add_argument("--platform", metavar="BASE_URL")
    p.add_argument("--agent-token", default="")
    p.add_argument("--building", default="")
    p.add_argument("--endpoint", default="", help="HTTP JSON endpoint for --connect")
    p.add_argument("--auth-header", default="", help="Authorization header value for --connect")
    p.add_argument("--points", nargs="*", default=[], help='--connect specs "FIELD:sensor_type[:unit]"')
    p.add_argument("--building-id", default="")
    p.add_argument("--seconds", type=int, default=6)
    p.add_argument("--interval", type=int, default=30)
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
        sim = [{"name": "mock-meter", "endpoint": "mock", "auth_header": "", "points": SAMPLE_POINTS}]
        _run(sim, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=True)
        return
    if a.platform:
        token = a.agent_token or os.environ.get("AGENT_TOKEN", "")
        if not token:
            raise SystemExit("--platform needs --agent-token or AGENT_TOKEN env")
        devices = platform_config_to_devices(fetch_platform_config(a.platform, token, a.building))
        if not devices:
            raise SystemExit("no REST devices with points in the platform config")
        _run(devices, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=False)
        return
    if a.config:
        ra = build_run_args(load_config(a.config))
        _run(ra["devices"], ra["sink_type"], ra["eh_conn"], ra["eh_name"], ra["batch"],
             a.seconds, ra["poll_seconds"], ra["max_retries"], mock=False)
        return
    if a.connect:
        if not a.endpoint or not a.points:
            raise SystemExit("--connect needs --endpoint and --points")
        devices = [{"name": "device", "endpoint": a.endpoint, "auth_header": a.auth_header,
                    "points": parse_point_specs(a.points, a.building_id)}]
        _run(devices, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=False)
        return
    p.print_help()


if __name__ == "__main__":
    main()
