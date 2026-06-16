#!/usr/bin/env python3
# =============================================================================
# edge-gateway/run_agent.py
# Energy Copilot Platform - unified edge-agent launcher
# =============================================================================
# One command runs a building's WHOLE mixed-protocol fleet. It pulls the node
# map from the platform (/agent/config) ONCE with the building's agent token,
# groups the devices by protocol, and runs each protocol's gateway concurrently
# against a SHARED sink (one Event Hub connection for the site).
#
# It also sends a periodic /agent/heartbeat reporting the device ids it is
# running, so the platform flips those devices PENDING -> active + last_seen_at
# (the device cards in the web app turn green). The backend still never reaches
# the devices itself; "active" means "an on-site agent is collecting this device".
#
# Handles the four device/point-model protocols: Modbus, BACnet, MQTT, REST.
# (OPC-UA uses a node-id model + its own config and stays a separate command.)
#
# RUN MODES
#   python run_agent.py --selftest      # dispatch/plan + id collection (no deps)
#   python run_agent.py --sim           # built-in mixed fleet, all mock (no deps)
#   python run_agent.py --platform https://api.host --agent-token <T> \
#       --sink eventhub --eh-conn "<conn>" --eh-name iot-raw --seconds 0
#
# DEPENDENCIES: per protocol present — pip install pymodbus BAC0 paho-mqtt
#               (REST + heartbeat use only the stdlib). --selftest / --sim need none.
# =============================================================================

import argparse
import asyncio
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("run_agent")

from opcua_gateway import make_sink, _serve  # noqa: E402
import modbus_gateway  # noqa: E402
import bacnet_gateway  # noqa: E402
import mqtt_gateway  # noqa: E402
import rest_gateway  # noqa: E402

# (protocol, module, run-function attr, default poll interval seconds)
_PROTOCOLS = [
    ("modbus", modbus_gateway, "run_poll", 5),
    ("bacnet", bacnet_gateway, "run_poll", 10),
    ("mqtt", mqtt_gateway, "run_subscribe", 2),
    ("rest", rest_gateway, "run_poll", 30),
]

_HEARTBEAT_INTERVAL = 60  # seconds between status write-backs


def plan_from_config(payload: dict) -> list:
    """Group an /agent/config payload into per-protocol run plans.

    Returns [{protocol, module, run, interval, devices}] for each protocol that
    has at least one mappable device. Each module's own platform_config_to_devices
    filters + validates its protocol's devices (and carries each device id).
    """
    plan = []
    for proto, mod, run_attr, interval in _PROTOCOLS:
        devices = mod.platform_config_to_devices(payload)
        if devices:
            plan.append({
                "protocol": proto,
                "module": mod,
                "run": run_attr,
                "interval": interval,
                "devices": devices,
            })
    return plan


def collect_device_ids(plan: list) -> list:
    """All device ids across the plan (for the heartbeat status write-back)."""
    ids = []
    for item in plan:
        for d in item["devices"]:
            if d.get("id"):
                ids.append(d["id"])
    return ids


def report_heartbeat(base_url: str, token: str, device_ids: list) -> dict:
    """POST /agent/heartbeat with the device ids being collected (stdlib only)."""
    import urllib.request

    url = base_url.rstrip("/") + "/agent/heartbeat"
    data = json.dumps({"device_ids": device_ids}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"X-Agent-Token": token, "Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310 (trusted platform URL)
        return json.loads(r.read().decode("utf-8"))


async def _heartbeat_loop(base_url: str, token: str, device_ids: list, interval: int, seconds: int):
    elapsed = 0
    while seconds == 0 or elapsed < seconds:
        try:
            res = report_heartbeat(base_url, token, device_ids)
            logger.info("AGENT - heartbeat ok: %s device(s) marked active", res.get("updated", "?"))
        except Exception as e:
            logger.warning("AGENT - heartbeat failed (%s)", str(e)[:80])
        await asyncio.sleep(interval)
        elapsed += interval


async def run_all(plan: list, sink, seconds: int, mock: bool = False, heartbeat: dict | None = None):
    """Run every planned protocol gateway concurrently against the shared sink,
    plus an optional heartbeat loop (status write-back)."""
    coros = []
    for item in plan:
        run_fn = getattr(item["module"], item["run"])
        npoints = sum(len(d["points"]) for d in item["devices"])
        logger.info("AGENT - %s: %d device(s), %d point(s), every %ds%s",
                    item["protocol"], len(item["devices"]), npoints, item["interval"],
                    " (mock)" if mock else "")
        coros.append(run_fn(item["devices"], sink, seconds, item["interval"], 0, mock))
    if heartbeat and heartbeat.get("device_ids"):
        coros.append(_heartbeat_loop(
            heartbeat["base_url"], heartbeat["token"], heartbeat["device_ids"],
            heartbeat.get("interval", _HEARTBEAT_INTERVAL), seconds))
    if not coros:
        logger.warning("AGENT - nothing to run (no devices in the config)")
        return
    await asyncio.gather(*coros)


# Built-in mixed fleet for --sim (one device per protocol; all mock).
SIM_PAYLOAD = {
    "building_id": "B001",
    "devices": [
        {"id": "11111111-1111-1111-1111-111111111111", "name": "Main meter", "protocol": "modbus",
         "connection_config": {"host": "10.0.0.5", "port": 502, "unit_id": 1},
         "points": [{"point_ref": "3060", "sensor_type": "building_kwh", "unit": "kW", "enabled": True}]},
        {"id": "22222222-2222-2222-2222-222222222222", "name": "AHU-1", "protocol": "bacnet",
         "connection_config": {"host": "10.0.0.6", "device_instance": 1001, "port": 47808},
         "points": [{"point_ref": "AI:1", "sensor_type": "HVAC_supply_temp", "unit": "degC", "enabled": True}]},
        {"id": "33333333-3333-3333-3333-333333333333", "name": "Zone sensor", "protocol": "mqtt",
         "connection_config": {"broker": "mqtt.local", "port": 1883, "base_topic": "building/+/climate"},
         "points": [{"point_ref": "temperature", "sensor_type": "HVAC_temp", "unit": "degC", "enabled": True}]},
        {"id": "44444444-4444-4444-4444-444444444444", "name": "Cloud sub-meter", "protocol": "rest_api",
         "connection_config": {"endpoint": "https://api.example.com/r", "auth_header": "Bearer x"},
         "points": [{"point_ref": "activePower", "sensor_type": "building_kwh", "unit": "kW", "enabled": True}]},
    ],
}


def selftest():
    plan = plan_from_config(SIM_PAYLOAD)
    protos = {p["protocol"] for p in plan}
    assert protos == {"modbus", "bacnet", "mqtt", "rest"}, protos
    by = {p["protocol"]: p for p in plan}
    assert by["modbus"]["devices"][0]["host"] == "10.0.0.5"
    assert by["bacnet"]["devices"][0]["device_instance"] == 1001
    assert by["mqtt"]["devices"][0]["broker"] == "mqtt.local"
    assert by["rest"]["devices"][0]["endpoint"].startswith("https://")
    # device ids flow through for the heartbeat status write-back
    ids = collect_device_ids(plan)
    assert len(ids) == 4 and all(ids), ids
    assert "11111111-1111-1111-1111-111111111111" in ids
    # single-protocol config only plans that protocol
    only_modbus = {"building_id": "B002", "devices": [SIM_PAYLOAD["devices"][0]]}
    p2 = plan_from_config(only_modbus)
    assert len(p2) == 1 and p2[0]["protocol"] == "modbus"
    assert collect_device_ids(p2) == ["11111111-1111-1111-1111-111111111111"]
    # empty / unknown-protocol config plans nothing
    assert plan_from_config({"devices": [{"protocol": "zwave", "points": []}]}) == []
    logger.info("SELFTEST OK - dispatch plans %d protocol(s) + %d device id(s) for heartbeat",
                len(plan), len(ids))


def main():
    p = argparse.ArgumentParser(description="EnergyLens unified edge-agent launcher")
    p.add_argument("--selftest", action="store_true", help="dispatch/plan + id collection (no deps)")
    p.add_argument("--sim", action="store_true", help="built-in mixed fleet, all mock (no deps)")
    p.add_argument("--platform", metavar="BASE_URL", help="EnergyLens API base for /agent/config")
    p.add_argument("--agent-token", default="", help="building-scoped agent token (or AGENT_TOKEN)")
    p.add_argument("--building", default="", help="building UUID (optional)")
    p.add_argument("--seconds", type=int, default=6, help="run duration; 0 = until stopped")
    p.add_argument("--sink", choices=["stub", "eventhub", "http", "tee"], default="stub")
    p.add_argument("--ingest-url", default="", help="explicit /ingest/telemetry URL (else derived from --platform)")
    p.add_argument("--batch", type=int, default=0)
    p.add_argument("--eh-conn", default="")
    p.add_argument("--eh-name", default="")
    a = p.parse_args()

    if a.selftest:
        selftest()
        return

    if a.sim:
        plan = plan_from_config(SIM_PAYLOAD)
        sink = make_sink(a.sink, a.eh_conn, a.eh_name, a.batch)
        logger.info("AGENT - SIM mixed fleet: %d protocol(s)", len(plan))
        asyncio.run(_serve(run_all(plan, sink, a.seconds, mock=True), sink))
        return

    if a.platform:
        token = a.agent_token or os.environ.get("AGENT_TOKEN", "")
        if not token:
            raise SystemExit("--platform needs --agent-token or AGENT_TOKEN env")
        payload = modbus_gateway.fetch_platform_config(a.platform, token, a.building)
        plan = plan_from_config(payload)
        if not plan:
            raise SystemExit("no runnable devices in the platform config")
        device_ids = collect_device_ids(plan)
        ingest_url = a.ingest_url or (a.platform.rstrip("/") + "/ingest/telemetry")
        sink = make_sink(a.sink, a.eh_conn, a.eh_name, a.batch,
                         ingest_url=ingest_url, agent_token=token)
        heartbeat = {"base_url": a.platform, "token": token, "device_ids": device_ids,
                     "interval": _HEARTBEAT_INTERVAL}
        logger.info("AGENT - building %s: running %s (%d device(s) heartbeated)",
                    payload.get("building_id", "?"), ", ".join(i["protocol"] for i in plan), len(device_ids))
        asyncio.run(_serve(run_all(plan, sink, a.seconds, mock=False, heartbeat=heartbeat), sink))
        return

    p.print_help()


if __name__ == "__main__":
    main()
