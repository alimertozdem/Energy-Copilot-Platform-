#!/usr/bin/env python3
# =============================================================================
# edge-gateway/mqtt_gateway.py
# Energy Copilot Platform - Tier-2 live MQTT 5.0 ingestion gateway
# =============================================================================
# MQTT (ISO/IEC 20922) is the emerging standard for new IoT deployments — smart
# meters, wireless sensors, cloud-connected devices. This gateway subscribes to
# each device's base topic, and for every JSON message extracts the configured
# points (point_ref = a key in the payload), normalizes via the shared
# MqttAdapter, and forwards to the same sink → Event Hub path.
#
# Like the other gateways it is config-driven and reuses the verified sink /
# batching / backoff / graceful-shutdown infrastructure from opcua_gateway. The
# MqttAdapter already honours an explicit sensor_type / building_id / unit in the
# payload, so the gateway passes the configured values straight through — no
# framework edit, no post-override.
#
# point_ref = the JSON key in the published payload, e.g. "temperature", "co2".
#
# RUN MODES
#   python mqtt_gateway.py --selftest      # adapter + config + platform (no paho)
#   python mqtt_gateway.py --sim           # built-in mock broker (no paho)
#   python mqtt_gateway.py --config config.mqtt.<site>.json
#   python mqtt_gateway.py --platform https://api.host --agent-token <T>
#   python mqtt_gateway.py --connect --broker mqtt.host --base-topic "building/+/climate" \
#       --points temperature:HVAC_temp:degC co2:CO2:ppm --building-id B003
#
# DEPENDENCIES: pip install paho-mqtt azure-eventhub   (--selftest / --sim need neither)
# =============================================================================

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import pathlib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mqtt_gateway")

from opcua_gateway import (  # noqa: E402
    StubSink,
    BufferedSink,
    make_sink,
    backoff_seconds,
    load_config,
    _serve,
)

try:
    import paho.mqtt.client as _mqtt  # noqa: F401
    HAS_PAHO = True
except Exception:
    HAS_PAHO = False


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
            return mod.MqttAdapter()
    raise FileNotFoundError(
        "MqttAdapter source not found; looked in: " + ", ".join(str(c) for c in candidates)
    )


class MqttGateway:
    """Adapter + sink. on_message() turns one JSON payload into 0..N normalized
    events — one per configured point whose key is present in the payload."""

    def __init__(self, sink, points: list):
        self.adapter = load_adapter()
        self.points = points
        self.sink = sink
        self.count = 0

    def on_message(self, topic: str, payload: dict) -> int:
        if not isinstance(payload, dict):
            return 0
        emitted = 0
        ts = payload.get("ts") or payload.get("timestamp")
        for p in self.points:
            key = p["point_ref"]
            if key not in payload:
                continue
            inner = {"value": payload[key], "sensor_type": p["sensor_type"]}
            if p.get("unit"):
                inner["unit"] = p["unit"]
            if ts:
                inner["ts"] = ts
            if p.get("building_id"):
                inner["building_id"] = p["building_id"]
            if p.get("device_id"):
                inner["device_id"] = p["device_id"]
            if p.get("zone"):
                inner["location"] = p["zone"]
            norm = self.adapter.normalize({"topic": topic, "payload": inner})
            self.sink.send(norm)
            self.count += 1
            emitted += 1
        return emitted

    def flush(self):
        if hasattr(self.sink, "flush"):
            self.sink.flush()


def build_run_args(cfg: dict) -> dict:
    if cfg.get("devices"):
        devices = cfg["devices"]
    else:
        devices = [{
            "name": cfg.get("name", "device"),
            "broker": cfg["broker"],
            "port": int(cfg.get("port", 1883)),
            "base_topic": cfg.get("base_topic", "#"),
            "points": cfg.get("points", []) or [],
        }]
    norm = []
    for d in devices:
        norm.append({
            "name": d.get("name", "device"),
            "broker": d["broker"],
            "port": int(d.get("port", 1883)),
            "base_topic": d.get("base_topic", "#"),
            "username": d.get("username") or None,
            "password": (os.environ.get(d["password_env"], "") if d.get("password_env") else d.get("password")) or None,
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
    """Keep only MQTT devices + their enabled points (point_ref = a payload key)."""
    bid = payload.get("building_id") or ""
    out = []
    for d in payload.get("devices", []) or []:
        if (d.get("protocol") or "").lower() != "mqtt":
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
            "broker": cc.get("broker", ""),
            "port": int(cc.get("port", 1883) or 1883),
            "base_topic": cc.get("base_topic", "#"),
            "username": None,
            "password": None,
            "points": points,
        })
    return out


# -----------------------------------------------------------------------------
# Live + mock subscription. Both deliver (topic, payload-dict) to gw.on_message.
# -----------------------------------------------------------------------------
async def run_subscribe(devices: list, sink, seconds: int, interval: int,
                        max_retries: int = 0, mock: bool = False):
    gateways = [(spec, MqttGateway(sink, spec["points"])) for spec in devices]

    if mock:
        await _run_mock(gateways, sink, seconds, interval)
        return

    if not HAS_PAHO:
        raise SystemExit("paho-mqtt not installed. `pip install paho-mqtt` for --connect/--config/--platform.")
    import paho.mqtt.client as mqtt

    clients = []
    for spec, gw in gateways:
        c = mqtt.Client()
        if spec.get("username"):
            c.username_pw_set(spec["username"], spec.get("password") or None)

        def _make_cb(g):
            def _on_message(_cli, _userdata, msg):
                try:
                    payload = json.loads(msg.payload.decode("utf-8"))
                except Exception:
                    return
                g.on_message(msg.topic, payload)
            return _on_message

        c.on_message = _make_cb(gw)
        attempt = 0
        while True:
            try:
                c.connect(spec["broker"], spec["port"], 60)
                break
            except Exception as e:
                attempt += 1
                wait = backoff_seconds(attempt)
                if max_retries and attempt >= max_retries:
                    raise
                logger.warning("MQTT - %s connect attempt %d failed (%s); retry in %.0fs",
                               spec["name"], attempt, str(e)[:80], wait)
                await asyncio.sleep(wait)
        c.subscribe(spec["base_topic"])
        c.loop_start()
        clients.append(c)
        logger.info("MQTT - subscribed %s to %s", spec["name"], spec["base_topic"])

    elapsed = 0
    try:
        while seconds == 0 or elapsed < seconds:
            if hasattr(sink, "flush"):
                sink.flush()
            await asyncio.sleep(interval)
            elapsed += interval
    finally:
        for c in clients:
            c.loop_stop()
            c.disconnect()
        if hasattr(sink, "flush"):
            sink.flush()
    total = sum(gw.count for _, gw in gateways)
    logger.info("MQTT - stopped, %d events ingested", total)


async def _run_mock(gateways, sink, seconds, interval):
    import random
    rnd = random.Random(5)
    elapsed = 0
    try:
        while seconds == 0 or elapsed < seconds:
            for spec, gw in gateways:
                payload = {"ts": "2026-06-05T12:00:00Z"}
                for p in spec["points"]:
                    payload[p["point_ref"]] = round(20 + 60 * rnd.random(), 2)
                gw.on_message(spec["base_topic"].replace("+", "B000").replace("#", "x"), payload)
            if hasattr(sink, "flush"):
                sink.flush()
            await asyncio.sleep(interval)
            elapsed += interval
    finally:
        if hasattr(sink, "flush"):
            sink.flush()
    total = sum(gw.count for _, gw in gateways)
    logger.info("MQTT - mock stopped, %d events ingested", total)


# -----------------------------------------------------------------------------
# --selftest
# -----------------------------------------------------------------------------
SAMPLE_POINTS = [
    {"point_ref": "temperature", "sensor_type": "HVAC_temp", "unit": "degC", "building_id": "B003", "device_id": "B003_Z1", "zone": "Floor 2"},
    {"point_ref": "co2",         "sensor_type": "CO2",       "unit": "ppm",  "building_id": "B003", "zone": "Floor 2"},
]
SAMPLE_MESSAGE = ("building/B003/climate", {"temperature": 21.7, "co2": 740, "ts": "2026-06-05T12:00:00Z"})


def selftest():
    # 1) one payload -> two normalized events, explicit sensor_type/building_id honored
    gw = MqttGateway(StubSink(), SAMPLE_POINTS)
    topic, payload = SAMPLE_MESSAGE
    emitted = gw.on_message(topic, payload)
    assert emitted == 2, emitted
    e = gw.sink.events
    assert e[0]["sensor_type"] == "HVAC_temp" and e[0]["reading_value"] == 21.7, e[0]
    assert e[0]["reading_unit"] == "C" and e[0]["building_id"] == "B003", e[0]
    assert e[1]["sensor_type"] == "CO2" and e[1]["reading_value"] == 740.0, e[1]
    assert all(x["source_protocol"] == "MQTT" for x in e)

    # 2) a payload missing a key only emits the present ones
    gw2 = MqttGateway(StubSink(), SAMPLE_POINTS)
    assert gw2.on_message("building/B003/climate", {"temperature": 19.0}) == 1

    # 3) batching + backoff
    stub = StubSink()
    buf = BufferedSink(stub, max_batch=2)
    gw3 = MqttGateway(buf, SAMPLE_POINTS)
    gw3.on_message(topic, payload)            # 2 events -> one batch flush
    assert len(stub.events) == 2
    buf.close()
    assert buf._buf == []
    assert backoff_seconds(1) == 2.0 and backoff_seconds(10) == 60.0

    # 4) config loader
    cfg_path = pathlib.Path(__file__).resolve().parent / "config.mqtt.example.json"
    if cfg_path.exists():
        ra = build_run_args(load_config(str(cfg_path)))
        assert len(ra["devices"]) >= 1 and ra["devices"][0]["broker"]
        logger.info("SELFTEST - config loader OK (%d device(s))", len(ra["devices"]))

    # 5) platform-config parser keeps only MQTT devices
    payload2 = {
        "building_id": "B003",
        "devices": [
            {"name": "Zone sensor", "protocol": "mqtt",
             "connection_config": {"broker": "mqtt.local", "port": 1883, "base_topic": "building/+/climate"},
             "points": [
                 {"point_ref": "temperature", "sensor_type": "HVAC_temp", "unit": "degC", "enabled": True},
                 {"point_ref": "co2", "sensor_type": "CO2", "enabled": False},   # disabled
             ]},
            {"name": "Meter", "protocol": "modbus", "connection_config": {}, "points": []},
        ],
    }
    devs = platform_config_to_devices(payload2)
    assert len(devs) == 1 and devs[0]["broker"] == "mqtt.local", devs
    assert len(devs[0]["points"]) == 1 and devs[0]["points"][0]["point_ref"] == "temperature"
    assert devs[0]["points"][0]["building_id"] == "B003"

    logger.info("SELFTEST OK - MqttAdapter (%d) + batching + backoff + config + platform verified", gw.count)


def parse_point_specs(specs: list, building_id: str = "") -> list:
    """--connect point specs: 'KEY:sensor_type[:unit]'  e.g. 'temperature:HVAC_temp:degC'."""
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
    logger.info("MQTT - %d device(s), %d point(s), sink=%s, batch=%d%s",
                len(devices), npoints, sink.name, batch, " (mock)" if mock else "")
    asyncio.run(_serve(run_subscribe(devices, sink, seconds, interval, max_retries, mock), sink))


def main():
    p = argparse.ArgumentParser(description="EnergyLens MQTT ingestion gateway")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--sim", action="store_true", help="built-in mock broker (no paho)")
    p.add_argument("--connect", action="store_true", help="connect to a real MQTT broker")
    p.add_argument("--config", metavar="PATH")
    p.add_argument("--platform", metavar="BASE_URL")
    p.add_argument("--agent-token", default="")
    p.add_argument("--building", default="")
    p.add_argument("--broker", default="", help="MQTT broker host for --connect")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--base-topic", default="#", help="topic to subscribe for --connect")
    p.add_argument("--points", nargs="*", default=[], help='--connect specs "KEY:sensor_type[:unit]"')
    p.add_argument("--building-id", default="")
    p.add_argument("--seconds", type=int, default=6)
    p.add_argument("--interval", type=int, default=2)
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
        sim = [{"name": "mock-zone", "broker": "mock", "port": 1883,
                "base_topic": "building/+/climate", "username": None, "password": None,
                "points": SAMPLE_POINTS}]
        _run(sim, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=True)
        return
    if a.platform:
        token = a.agent_token or os.environ.get("AGENT_TOKEN", "")
        if not token:
            raise SystemExit("--platform needs --agent-token or AGENT_TOKEN env")
        devices = platform_config_to_devices(fetch_platform_config(a.platform, token, a.building))
        if not devices:
            raise SystemExit("no MQTT devices with points in the platform config")
        _run(devices, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=False)
        return
    if a.config:
        ra = build_run_args(load_config(a.config))
        _run(ra["devices"], ra["sink_type"], ra["eh_conn"], ra["eh_name"], ra["batch"],
             a.seconds, a.interval, ra["max_retries"], mock=False)
        return
    if a.connect:
        if not a.broker or not a.points:
            raise SystemExit("--connect needs --broker and --points")
        devices = [{"name": "device", "broker": a.broker, "port": a.port,
                    "base_topic": a.base_topic, "username": None, "password": None,
                    "points": parse_point_specs(a.points, a.building_id)}]
        _run(devices, a.sink, a.eh_conn, a.eh_name, a.batch, a.seconds, a.interval, a.max_retries, mock=False)
        return
    p.print_help()


if __name__ == "__main__":
    main()
