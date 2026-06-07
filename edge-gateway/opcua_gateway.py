#!/usr/bin/env python3
# =============================================================================
# edge-gateway/opcua_gateway.py
# Energy Copilot Platform - F-full: live OPC-UA / SCADA ingestion gateway
# =============================================================================
# Connects to an OPC-UA server (real PLC or simulator), subscribes to monitored
# nodes, normalizes each value change via the shared OpcUaAdapter, and forwards
# the standard event to a sink (Azure Event Hub in production; stub for testing).
#
# This is the LIVE counterpart to the adapter library
# (notebooks/iot/00_iot_adapter_framework.py). The adapter = pure transform;
# this gateway = the live session (connect, subscribe, push).
#
# RUN MODES
#   python opcua_gateway.py --selftest
#       No asyncua / no Azure. Pipes sample DataValues through the adapter ->
#       sink; verifies buffered batching, reconnect backoff, and the config
#       loader + per-node overrides. (CI-friendly.)
#
#   python opcua_gateway.py --sim [--seconds 6] [--batch 50]
#       Needs `pip install asyncua`. Simulated OPC-UA server + live subscription.
#
#   python opcua_gateway.py --config config.<site>.json [--seconds 0]
#       Production: per-site config (server, TLS+auth, node map, sink). Secrets
#       read from env (password_env, sink.connection_env). Auto-reconnect.
#
#   python opcua_gateway.py --connect opc.tcp://host:4840 --nodes "ns=2;s=..." ...
#       Ad-hoc connect without a config file.
#
# DEPENDENCIES: pip install asyncua azure-eventhub   (--selftest needs neither)
# =============================================================================

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import pathlib
import signal
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("opcua_gateway")

# asyncua is OPTIONAL at import time (only --sim / --connect / --config need it).
# Deferring the import keeps --selftest runnable anywhere (CI, no PyPI access).
try:
    from asyncua import Server, Client, ua
    HAS_ASYNCUA = True
except Exception:
    HAS_ASYNCUA = False


# -----------------------------------------------------------------------------
# Shared adapter (single source of truth). Container-friendly resolution:
# prefer a vendored copy next to this file (Dockerfile COPYs it in), else fall
# back to the repo notebook path for local development.
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
            return mod.OpcUaAdapter()
    raise FileNotFoundError(
        "OpcUaAdapter source not found; looked in: " + ", ".join(str(c) for c in candidates)
    )


# -----------------------------------------------------------------------------
# Sinks  (send one + send_batch many + close)
# -----------------------------------------------------------------------------
class StubSink:
    """Test sink: collect + log normalized events. No external dependency."""
    name = "stub"

    def __init__(self):
        self.events = []

    def send(self, event: dict):
        self.events.append(event)
        logger.info("→ %s", json.dumps(event, ensure_ascii=False))

    def send_batch(self, events: list):
        self.events.extend(events)
        logger.info("→ batch of %d events", len(events))

    def close(self):
        pass


class EventHubSink:
    """Production sink: Azure Event Hub. azure-eventhub imported lazily so that
    --selftest never requires it."""
    name = "eventhub"

    def __init__(self, conn_str: str, eh_name: str):
        from azure.eventhub import EventHubProducerClient, EventData
        self._EventData = EventData
        self._producer = EventHubProducerClient.from_connection_string(
            conn_str, eventhub_name=eh_name
        )

    def send(self, event: dict):
        self.send_batch([event])

    def send_batch(self, events: list):
        if not events:
            return
        batch = self._producer.create_batch()
        for e in events:
            batch.add(self._EventData(json.dumps(e, ensure_ascii=False)))
        self._producer.send_batch(batch)

    def close(self):
        try:
            self._producer.close()
        except Exception:
            pass


class BufferedSink:
    """Wrap a target sink; accumulate events and flush in batches (count-based +
    explicit flush()/close()). Cuts Event Hub round-trips under load. The async
    run loops call flush() once per second so events never linger."""

    def __init__(self, target, max_batch: int = 50):
        self.target = target
        self.max_batch = max(1, int(max_batch))
        self._buf = []

    @property
    def name(self):
        return f"buffered({self.target.name})"

    def send(self, event: dict):
        self._buf.append(event)
        if len(self._buf) >= self.max_batch:
            self.flush()

    def flush(self):
        if self._buf:
            self.target.send_batch(self._buf)
            self._buf = []

    def close(self):
        self.flush()
        self.target.close()


def make_sink(target: str, eh_conn: str = "", eh_name: str = "", batch: int = 0):
    base = EventHubSink(eh_conn, eh_name) if target == "eventhub" else StubSink()
    if batch and batch > 1:
        return BufferedSink(base, max_batch=batch)
    return base


# -----------------------------------------------------------------------------
# Core: DataValue -> raw dict -> adapter.normalize() -> sink
# -----------------------------------------------------------------------------
def datavalue_to_raw(node_id, browse_name, value, status="Good", source_ts=None,
                     eu_unit=None, building_id=None, sensor_type=None):
    """Build the raw dict the OpcUaAdapter expects. Optional sensor_type /
    building_id come from per-site config and override the adapter's heuristics
    (real PLC browse names are often cryptic)."""
    raw = {
        "node_id": node_id,
        "browse_name": browse_name,
        "value": value,
        "status_code": status,
    }
    if source_ts is not None:
        raw["source_timestamp"] = source_ts
    if eu_unit is not None:
        raw["eu_unit"] = eu_unit
    if building_id is not None:
        raw["building_id"] = building_id
    if sensor_type is not None:
        raw["sensor_type"] = sensor_type
    return raw


class OpcUaGateway:
    """Holds the adapter + sink; ingest() normalizes one reading and forwards it."""

    def __init__(self, sink):
        self.adapter = load_adapter()
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


def backoff_seconds(attempt: int, base: float = 2.0, cap: float = 60.0) -> float:
    """Exponential backoff with a ceiling. attempt starts at 1: 2,4,8,...,cap."""
    return min(cap, base * (2 ** max(0, attempt - 1)))


# -----------------------------------------------------------------------------
# Per-site config (declarative node map + security + sink). Secrets via env.
# -----------------------------------------------------------------------------
def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_run_args(cfg: dict) -> dict:
    """Resolve a config dict into concrete run args. Secrets are read from env
    (password_env, sink.connection_env) and never stored in the file."""
    nodes = cfg.get("nodes", []) or []
    node_ids = [n["node_id"] for n in nodes]
    node_meta = {}
    for n in nodes:
        node_meta[n["node_id"]] = {
            "browse_name": n.get("browse_name", ""),
            "unit": n.get("unit"),
            "sensor_type": n.get("sensor_type"),
            "building_id": n.get("building_id"),
        }
    sink_cfg = cfg.get("sink", {}) or {}
    if sink_cfg.get("connection_env"):
        eh_conn = os.environ.get(sink_cfg["connection_env"], "")
    else:
        eh_conn = sink_cfg.get("connection", "")
    if cfg.get("password_env"):
        password = os.environ.get(cfg["password_env"], "")
    else:
        password = cfg.get("password", "")
    return {
        "server_url": cfg["server_url"],
        "security": cfg.get("security") or None,
        "username": cfg.get("username") or None,
        "password": password or None,
        "sink_type": sink_cfg.get("type", "stub"),
        "eh_name": sink_cfg.get("eventhub_name", ""),
        "eh_conn": eh_conn,
        "batch": int(cfg.get("batch", 0) or 0),
        "max_retries": int(cfg.get("max_retries", 0) or 0),
        "node_ids": node_ids,
        "node_meta": node_meta,
    }


# -----------------------------------------------------------------------------
# --selftest : adapter pipeline + batching + backoff + config loader (no asyncua)
# -----------------------------------------------------------------------------
SAMPLE_NODES = [
    # node_id,                            browse_name,                            value, status,      unit
    ("ns=2;s=B005.Chiller1.COP",          "Chiller Coefficient of Performance",   4.3,   "Good",      "ratio"),
    ("ns=2;s=B001.AHU1.SupplyAirTemp",    "AHU Supply Air Temperature",           14.2,  "Good",      "degC"),
    ("ns=2;s=B007.PV.Inverter1.Power",    "PV Inverter AC Power",                 41.5,  "Good",      "kW"),
    ("ns=2;s=B009.Chiller2.COP",          "Chiller Coefficient of Performance",   2.1,   "Uncertain", "ratio"),
]


def selftest():
    # 1) adapter pipeline correctness
    gw = OpcUaGateway(StubSink())
    logger.info("SELFTEST - piping %d sample OPC-UA DataValues through adapter -> sink",
                len(SAMPLE_NODES))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for (nid, bn, val, st, unit) in SAMPLE_NODES:
        gw.ingest(datavalue_to_raw(nid, bn, val, status=st, source_ts=now, eu_unit=unit))
    evs = gw.sink.events
    assert evs[0]["building_id"] == "B005" and evs[0]["sensor_type"] == "chiller_cop", evs[0]
    assert evs[1]["building_id"] == "B001" and evs[1]["sensor_type"] == "HVAC_supply_temp", evs[1]
    assert evs[2]["building_id"] == "B007" and evs[2]["sensor_type"] == "pv_ac_power", evs[2]
    assert evs[3]["reading_quality"] == 50, evs[3]            # Uncertain -> 50
    assert all(e["source_protocol"] == "OPC-UA" for e in evs)
    assert all(e["building_id"] != "UNKNOWN" for e in evs)

    # 2) buffered batching: max_batch=2 over 4 events -> 2 flushes, buffer empty
    stub = StubSink()
    buf = BufferedSink(stub, max_batch=2)
    gw2 = OpcUaGateway(buf)
    for (nid, bn, val, st, unit) in SAMPLE_NODES:
        gw2.ingest(datavalue_to_raw(nid, bn, val, status=st, eu_unit=unit))
    assert len(stub.events) == 4, len(stub.events)
    buf.close()
    assert len(stub.events) == 4 and buf._buf == []

    # 3) reconnect backoff curve
    assert backoff_seconds(1) == 2.0 and backoff_seconds(2) == 4.0
    assert backoff_seconds(3) == 8.0 and backoff_seconds(10) == 60.0

    # 4) config loader + per-node override honored
    cfg_path = pathlib.Path(__file__).resolve().parent / "config.example.json"
    if cfg_path.exists():
        ra = build_run_args(load_config(str(cfg_path)))
        assert ra["server_url"].startswith("opc.tcp://"), ra["server_url"]
        assert len(ra["node_ids"]) >= 1
        first = ra["node_ids"][0]
        m = ra["node_meta"][first]
        raw = datavalue_to_raw(first, m.get("browse_name", ""), 4.0,
                               eu_unit=m.get("unit"),
                               building_id=m.get("building_id"),
                               sensor_type=m.get("sensor_type"))
        norm = OpcUaGateway(StubSink()).adapter.normalize(raw)
        if m.get("sensor_type"):
            assert norm["sensor_type"] == m["sensor_type"], norm
        if m.get("building_id"):
            assert norm["building_id"] == m["building_id"], norm
        logger.info("SELFTEST - config loader OK (%d nodes; per-node override honored)",
                    len(ra["node_ids"]))

    logger.info("SELFTEST OK - adapter pipeline (%d) + batching + backoff + config verified",
                gw.count)


# -----------------------------------------------------------------------------
# asyncua data-change -> raw (shared by --sim and --connect)
# -----------------------------------------------------------------------------
def _datachange_to_raw(node, val, data, meta):
    nid = node.nodeid.to_string()
    m = meta.get(nid, {})
    status, src_ts = "Good", None
    try:
        dv = data.monitored_item.Value
        if dv.StatusCode is not None:
            status = dv.StatusCode.name
        if dv.SourceTimestamp:
            src_ts = dv.SourceTimestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass
    return datavalue_to_raw(nid, m.get("browse_name", ""), val, status=status, source_ts=src_ts,
                            eu_unit=m.get("unit"), sensor_type=m.get("sensor_type"),
                            building_id=m.get("building_id"))


# -----------------------------------------------------------------------------
# --sim : simulated OPC-UA server + subscribing client (needs asyncua)
# -----------------------------------------------------------------------------
SIM_NODES = [
    # string identifier,          browse_name,                            base value, unit
    ("B005.Chiller1.COP",         "Chiller Coefficient of Performance",   4.3,  "ratio"),
    ("B001.AHU1.SupplyAirTemp",   "AHU Supply Air Temperature",           14.2, "degC"),
    ("B007.PV.Inverter1.Power",   "PV Inverter AC Power",                 41.5, "kW"),
]


async def run_sim(seconds: int, gateway: "OpcUaGateway"):
    import random
    url = "opc.tcp://0.0.0.0:4840/energylens/sim/"

    server = Server()
    await server.init()
    server.set_endpoint(url)
    idx = await server.register_namespace("http://energylens.eu/opcua/sim")
    objs = server.nodes.objects

    meta = {}          # nodeid_str -> {browse_name, unit}
    bases = {}         # nodeid_str -> base value
    nodes = []
    for (ident, bn, base, unit) in SIM_NODES:
        var = await objs.add_variable(ua.NodeId(ident, idx), bn, float(base))
        await var.set_writable()
        nid_str = var.nodeid.to_string()
        meta[nid_str] = {"browse_name": bn, "unit": unit}
        bases[nid_str] = float(base)
        nodes.append(var)

    gw = gateway

    class _Handler:
        def datachange_notification(self, node, val, data):
            gw.ingest(_datachange_to_raw(node, val, data, meta))

    async with server:
        client = Client(url.replace("0.0.0.0", "127.0.0.1"))
        await client.connect()
        try:
            sub = await client.create_subscription(500, _Handler())
            await sub.subscribe_data_change(nodes)
            logger.info("SIM - server up, client subscribed to %d nodes; ticking %ds",
                        len(nodes), seconds)
            for _ in range(seconds):
                await asyncio.sleep(1.0)
                for var in nodes:
                    base = bases[var.nodeid.to_string()]
                    await var.write_value(round(base * (0.85 + 0.30 * random.random()), 3))
                gw.flush()
            await sub.delete()
        finally:
            await client.disconnect()
    gw.flush()
    logger.info("SIM - done, %d events ingested", gw.count)


# -----------------------------------------------------------------------------
# --connect / --config : real OPC-UA server, TLS/auth + auto-reconnect
# -----------------------------------------------------------------------------
async def run_connect(url, node_ids, gateway, seconds,
                      security=None, user=None, password=None, node_meta=None):
    client = Client(url)
    if security:
        await client.set_security_string(security)   # "Policy,Mode,cert.der,key.pem[,server.der]"
    if user:
        client.set_user(user)
    if password:
        client.set_password(password)
    await client.connect()
    try:
        nodes = [client.get_node(nid) for nid in node_ids]
        meta = dict(node_meta or {})
        for n in nodes:
            nid = n.nodeid.to_string()
            if nid not in meta:
                meta[nid] = {"browse_name": "", "unit": None, "sensor_type": None, "building_id": None}
            if not meta[nid].get("browse_name"):
                try:
                    meta[nid]["browse_name"] = (await n.read_browse_name()).Name
                except Exception:
                    meta[nid]["browse_name"] = ""
        gw = gateway

        class _Handler:
            def datachange_notification(self, node, val, data):
                gw.ingest(_datachange_to_raw(node, val, data, meta))

        sub = await client.create_subscription(1000, _Handler())
        await sub.subscribe_data_change(nodes)
        logger.info("CONNECT - subscribed to %d nodes on %s%s%s",
                    len(nodes), url, " (secured)" if security else "",
                    (" for %ds" % seconds) if seconds else " (until stopped)")
        if seconds:
            for _ in range(seconds):
                await asyncio.sleep(1.0)
                gw.flush()
        else:
            while True:                       # run until killed; flush each second
                await asyncio.sleep(1.0)
                gw.flush()
        await sub.delete()
    finally:
        await client.disconnect()
        gateway.flush()
    logger.info("CONNECT - session ended, %d events ingested", gateway.count)


async def run_connect_resilient(url, node_ids, gateway, seconds, security=None,
                                user=None, password=None, max_retries=0, node_meta=None):
    """Retry connect with exponential backoff. max_retries=0 => retry forever."""
    attempt = 0
    while True:
        attempt += 1
        try:
            await run_connect(url, node_ids, gateway, seconds, security, user, password, node_meta)
            return
        except Exception as e:
            wait = backoff_seconds(attempt)
            if max_retries and attempt >= max_retries:
                logger.error("CONNECT - giving up after %d attempts (%s)", attempt, str(e)[:80])
                raise
            logger.warning("CONNECT - attempt %d failed (%s); retrying in %.0fs",
                           attempt, str(e)[:80], wait)
            await asyncio.sleep(wait)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Graceful shutdown: on SIGTERM/SIGINT, cancel the run task so the run-loop
# finally-blocks disconnect cleanly. sink.close() here is synchronous and always
# runs, so a (buffered) sink flushes its pending events instead of losing them.
# -----------------------------------------------------------------------------
async def _serve(coro, sink):
    loop = asyncio.get_running_loop()
    task = asyncio.ensure_future(coro)

    def _request_stop():
        logger.info("shutdown signal received - stopping gateway")
        task.cancel()

    for sig in (getattr(signal, "SIGTERM", None), getattr(signal, "SIGINT", None)):
        if sig is None:
            continue
        try:
            loop.add_signal_handler(sig, _request_stop)
        except (NotImplementedError, RuntimeError):
            pass  # e.g. Windows / not the main thread

    try:
        await task
    except asyncio.CancelledError:
        logger.info("gateway run cancelled - cleaning up")
    finally:
        sink.close()


def main():
    p = argparse.ArgumentParser(description="EnergyLens OPC-UA / SCADA ingestion gateway")
    p.add_argument("--selftest", action="store_true",
                   help="adapter pipeline + batching + backoff + config (no asyncua)")
    p.add_argument("--sim", action="store_true",
                   help="simulated OPC-UA server + subscribe (needs asyncua)")
    p.add_argument("--connect", metavar="URL", help="connect to a real OPC-UA server URL")
    p.add_argument("--config", metavar="PATH", help="per-site JSON config (server, security, nodes, sink)")
    p.add_argument("--seconds", type=int, default=6, help="run duration; 0 = until stopped (connect/config)")
    p.add_argument("--sink", choices=["stub", "eventhub"], default="stub")
    p.add_argument("--batch", type=int, default=0, help="buffer N events per send (0 = no batching)")
    p.add_argument("--eh-conn", default="", help="Event Hub connection string")
    p.add_argument("--eh-name", default="", help="Event Hub name")
    p.add_argument("--nodes", nargs="*", default=[], help="node ids for --connect")
    p.add_argument("--security", default="", help='asyncua security string "Policy,Mode,cert,key"')
    p.add_argument("--user", default="", help="OPC-UA username")
    p.add_argument("--password", default="", help="OPC-UA password")
    p.add_argument("--max-retries", type=int, default=0, help="--connect retry cap (0 = forever)")
    a = p.parse_args()

    if a.selftest:
        selftest()
        return

    if not HAS_ASYNCUA:
        raise SystemExit("asyncua not installed. `pip install asyncua` for --sim/--connect/--config, "
                         "or run --selftest (no dependency).")

    # --config: declarative per-site run
    if a.config:
        ra = build_run_args(load_config(a.config))
        sink = make_sink(ra["sink_type"], ra["eh_conn"], ra["eh_name"], ra["batch"])
        gw = OpcUaGateway(sink)
        logger.info("CONFIG - %s: %d nodes, sink=%s, batch=%d",
                    ra["server_url"], len(ra["node_ids"]), sink.name, ra["batch"])
        asyncio.run(_serve(run_connect_resilient(
            ra["server_url"], ra["node_ids"], gw, a.seconds,
            ra["security"], ra["username"], ra["password"],
            ra["max_retries"], ra["node_meta"]), sink))
        return

    sink = make_sink(a.sink, a.eh_conn, a.eh_name, a.batch)
    gw = OpcUaGateway(sink)
    if a.sim:
        asyncio.run(_serve(run_sim(a.seconds, gw), sink))
    elif a.connect:
        asyncio.run(_serve(run_connect_resilient(
            a.connect, a.nodes, gw, a.seconds,
            a.security or None, a.user or None, a.password or None, a.max_retries), sink))
    else:
        p.print_help()
        sink.close()


if __name__ == "__main__":
    main()
