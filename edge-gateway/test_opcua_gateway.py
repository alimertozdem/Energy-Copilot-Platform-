#!/usr/bin/env python3
"""Tests for the OPC-UA ingestion gateway.

Runs under pytest:           pytest edge-gateway/test_opcua_gateway.py -v
or standalone (no pytest):   python edge-gateway/test_opcua_gateway.py
Neither needs asyncua / Azure — the adapter pipeline + config loader are pure.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import opcua_gateway as g  # noqa: E402


def test_adapter_pipeline():
    gw = g.OpcUaGateway(g.StubSink())
    for (nid, bn, val, st, unit) in g.SAMPLE_NODES:
        gw.ingest(g.datavalue_to_raw(nid, bn, val, status=st, eu_unit=unit))
    e = gw.sink.events
    assert e[0]["building_id"] == "B005" and e[0]["sensor_type"] == "chiller_cop"
    assert e[1]["sensor_type"] == "HVAC_supply_temp" and e[1]["reading_unit"] == "C"
    assert e[2]["sensor_type"] == "pv_ac_power"
    assert e[3]["reading_quality"] == 50            # Uncertain StatusCode
    assert all(x["source_protocol"] == "OPC-UA" for x in e)


def test_buffered_batching():
    stub = g.StubSink()
    buf = g.BufferedSink(stub, max_batch=2)
    gw = g.OpcUaGateway(buf)
    for (nid, bn, val, st, unit) in g.SAMPLE_NODES:
        gw.ingest(g.datavalue_to_raw(nid, bn, val, status=st, eu_unit=unit))
    assert len(stub.events) == 4
    buf.close()
    assert buf._buf == []


def test_backoff_curve():
    assert g.backoff_seconds(1) == 2.0
    assert g.backoff_seconds(2) == 4.0
    assert g.backoff_seconds(3) == 8.0
    assert g.backoff_seconds(10) == 60.0          # capped


def test_config_loader_and_override():
    cfg_path = pathlib.Path(__file__).resolve().parent / "config.example.json"
    ra = g.build_run_args(g.load_config(str(cfg_path)))
    assert ra["server_url"].startswith("opc.tcp://")
    assert len(ra["node_ids"]) >= 1
    first = ra["node_ids"][0]
    m = ra["node_meta"][first]
    raw = g.datavalue_to_raw(first, m.get("browse_name", ""), 4.0,
                             sensor_type=m.get("sensor_type"),
                             building_id=m.get("building_id"), eu_unit=m.get("unit"))
    norm = g.OpcUaGateway(g.StubSink()).adapter.normalize(raw)
    if m.get("sensor_type"):
        assert norm["sensor_type"] == m["sensor_type"]
    if m.get("building_id"):
        assert norm["building_id"] == m["building_id"]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print("ALL %d TESTS PASSED" % len(tests))
