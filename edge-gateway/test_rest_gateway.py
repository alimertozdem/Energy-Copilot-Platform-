#!/usr/bin/env python3
"""Tests for the REST API ingestion gateway (stdlib only)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rest_gateway as g  # noqa: E402


def test_response_to_events():
    gw = g.RestGateway(g.StubSink(), g.SAMPLE_POINTS)
    assert gw.poll_once(g.SAMPLE_RESPONSE) == 2
    e = gw.sink.events
    assert e[0]["sensor_type"] == "building_kwh" and e[0]["reading_value"] == 45.2
    assert e[0]["building_id"] == "B004" and e[0]["reading_unit"] == "kW"
    assert e[1]["sensor_type"] == "HVAC_temp" and e[1]["reading_value"] == 21.0   # dotted path
    assert all(x["source_protocol"] == "REST" for x in e)


def test_extract_path():
    assert g.extract_path({"a": {"b": 3}}, "a.b") == 3
    assert g.extract_path({"a": 1}, "a.b") is None
    assert g.extract_path({}, "x") is None


def test_partial_response():
    gw = g.RestGateway(g.StubSink(), g.SAMPLE_POINTS)
    assert gw.poll_once({"activePower": 10.0}) == 1


def test_batching_backoff():
    stub = g.StubSink()
    buf = g.BufferedSink(stub, max_batch=2)
    gw = g.RestGateway(buf, g.SAMPLE_POINTS)
    gw.poll_once(g.SAMPLE_RESPONSE)
    assert len(stub.events) == 2
    buf.close()
    assert buf._buf == []
    assert g.backoff_seconds(1) == 2.0 and g.backoff_seconds(10) == 60.0


def test_config_loader():
    ra = g.build_run_args(g.load_config(str(pathlib.Path(__file__).resolve().parent / "config.rest.example.json")))
    assert len(ra["devices"]) >= 1 and ra["devices"][0]["endpoint"]


def test_platform_parser():
    payload = {"building_id": "B004", "devices": [
        {"name": "Cloud", "protocol": "rest_api",
         "connection_config": {"endpoint": "https://api/r", "auth_header": "Bearer x"},
         "points": [{"point_ref": "activePower", "sensor_type": "building_kwh", "enabled": True},
                    {"point_ref": "temp", "sensor_type": "HVAC_temp", "enabled": False}]},
        {"name": "M", "protocol": "modbus", "connection_config": {}, "points": []}]}
    devs = g.platform_config_to_devices(payload)
    assert len(devs) == 1 and devs[0]["endpoint"] == "https://api/r"
    assert len(devs[0]["points"]) == 1 and devs[0]["points"][0]["building_id"] == "B004"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print("ALL %d TESTS PASSED" % len(tests))
