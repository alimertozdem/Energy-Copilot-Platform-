#!/usr/bin/env python3
"""Tests for the BACnet/IP ingestion gateway.

Runs under pytest:           pytest edge-gateway/test_bacnet_gateway.py -v
or standalone (no pytest):   python edge-gateway/test_bacnet_gateway.py
Neither needs BAC0 / Azure — the adapter pipeline + config + platform parser are
pure Python (the sensor_type is config-overridden, not heuristic-guessed).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bacnet_gateway as g  # noqa: E402


def test_override_and_fahrenheit_conversion():
    gw = g.BacnetGateway(g.StubSink(), g.SAMPLE_POINTS)
    for ref, val, units in g.SAMPLE_READS:
        p = next(x for x in g.SAMPLE_POINTS if x["object_ref"] == ref)
        gw.ingest(g.point_to_raw(p, val, units, device_instance=1001), sensor_type=p["sensor_type"])
    e = gw.sink.events
    assert e[0]["sensor_type"] == "HVAC_supply_temp"     # config override, not the heuristic
    assert e[0]["reading_value"] == 14.0 and e[0]["reading_unit"] == "C"   # 57.2F -> 14C
    assert e[0]["building_id"] == "B001"
    assert e[1]["sensor_type"] == "CO2" and e[1]["reading_value"] == 850.0
    assert all(x["source_protocol"] == "BACnet" for x in e)


def test_object_ref_parsing():
    assert g.parse_object_ref("AI:1") == ("analogInput", 1)
    assert g.parse_object_ref("MSV:3") == ("multiStateValue", 3)
    assert g.parse_object_ref("3060") is None
    assert g.parse_object_ref("AI:x") is None


def test_buffered_batching():
    stub = g.StubSink()
    buf = g.BufferedSink(stub, max_batch=2)
    gw = g.BacnetGateway(buf, g.SAMPLE_POINTS)
    for ref, val, units in g.SAMPLE_READS:
        p = next(x for x in g.SAMPLE_POINTS if x["object_ref"] == ref)
        gw.ingest(g.point_to_raw(p, val, units, 1001), sensor_type=p["sensor_type"])
    assert len(stub.events) == 2
    buf.close()
    assert buf._buf == []


def test_config_loader():
    cfg_path = pathlib.Path(__file__).resolve().parent / "config.bacnet.example.json"
    ra = g.build_run_args(g.load_config(str(cfg_path)))
    assert len(ra["devices"]) >= 1
    d0 = ra["devices"][0]
    assert d0["host"] and d0["device_instance"] and len(d0["points"]) >= 1


def test_platform_config_parser():
    payload = {
        "building_id": "B001",
        "devices": [
            {"name": "AHU-1", "protocol": "bacnet",
             "connection_config": {"host": "10.0.0.6", "device_instance": 1001, "port": 47808},
             "points": [
                 {"point_ref": "AI:1", "sensor_type": "HVAC_supply_temp", "unit": "degC", "enabled": True},
                 {"point_ref": "3060", "sensor_type": "building_kwh", "enabled": True},   # not a BACnet ref
                 {"point_ref": "AI:2", "sensor_type": "CO2", "enabled": False},           # disabled
             ]},
            {"name": "Meter", "protocol": "modbus", "connection_config": {}, "points": []},  # non-bacnet
        ],
    }
    devs = g.platform_config_to_devices(payload)
    assert len(devs) == 1 and devs[0]["host"] == "10.0.0.6" and devs[0]["device_instance"] == 1001
    assert len(devs[0]["points"]) == 1 and devs[0]["points"][0]["object_ref"] == "AI:1"
    assert devs[0]["points"][0]["building_id"] == "B001"


def test_object_spec_parser():
    pts = g.parse_object_specs(["AI:1:HVAC_temp:degC", "AV:3:CO2"], building_id="B001")
    assert pts[0]["object_ref"] == "AI:1" and pts[0]["sensor_type"] == "HVAC_temp" and pts[0]["unit"] == "degC"
    assert pts[1]["object_ref"] == "AV:3" and pts[1]["sensor_type"] == "CO2"
    assert pts[0]["building_id"] == "B001"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print("ALL %d TESTS PASSED" % len(tests))
