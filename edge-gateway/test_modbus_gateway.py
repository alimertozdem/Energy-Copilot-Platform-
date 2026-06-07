#!/usr/bin/env python3
"""Tests for the Modbus TCP ingestion gateway.

Runs under pytest:           pytest edge-gateway/test_modbus_gateway.py -v
or standalone (no pytest):   python edge-gateway/test_modbus_gateway.py
Neither needs pymodbus / Azure — the adapter pipeline + config + platform parser
are pure Python (the register-map is injected from config, not hardware).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modbus_gateway as g  # noqa: E402


def test_register_map_injection_and_scaling():
    gw = g.ModbusGateway(g.StubSink(), g.SAMPLE_POINTS)
    for reg, val in g.SAMPLE_READS:
        p = next(x for x in g.SAMPLE_POINTS if int(x["register"]) == reg)
        gw.ingest(g.register_to_raw(p, val, unit_id=1))
    e = gw.sink.events
    assert e[0]["sensor_type"] == "building_kwh" and e[0]["building_id"] == "B005"
    assert e[0]["reading_value"] == 415.0                      # 415 * 1.0
    assert e[1]["reading_value"] == round(1234567 * 0.01, 4)   # scale 0.01
    assert e[2]["sensor_type"] == "HVAC_temp" and e[2]["reading_value"] == 21.5   # 215 * 0.1, degC->C
    assert all(x["source_protocol"] == "Modbus" for x in e)


def test_buffered_batching():
    stub = g.StubSink()
    buf = g.BufferedSink(stub, max_batch=2)
    gw = g.ModbusGateway(buf, g.SAMPLE_POINTS)
    for reg, val in g.SAMPLE_READS:
        p = next(x for x in g.SAMPLE_POINTS if int(x["register"]) == reg)
        gw.ingest(g.register_to_raw(p, val, 1))
    assert len(stub.events) == 2          # one full batch of 2 flushed; 1 buffered
    buf.close()
    assert len(stub.events) == 3 and buf._buf == []


def test_backoff_curve():
    assert g.backoff_seconds(1) == 2.0
    assert g.backoff_seconds(3) == 8.0
    assert g.backoff_seconds(10) == 60.0          # capped


def test_config_loader():
    cfg_path = pathlib.Path(__file__).resolve().parent / "config.modbus.example.json"
    ra = g.build_run_args(g.load_config(str(cfg_path)))
    assert len(ra["devices"]) >= 1
    d0 = ra["devices"][0]
    assert d0["host"] and len(d0["points"]) >= 1
    gw = g.ModbusGateway(g.StubSink(), d0["points"])
    p0 = d0["points"][0]
    gw.ingest(g.register_to_raw(p0, 1000, d0["unit_id"]))
    assert gw.sink.events[0]["sensor_type"] == p0["sensor_type"]


def test_platform_config_parser():
    payload = {
        "building_id": "B005",
        "devices": [
            {"name": "Main meter", "protocol": "modbus",
             "connection_config": {"host": "10.0.0.5", "port": 502, "unit_id": 1},
             "points": [
                 {"point_ref": "3060", "sensor_type": "building_kwh", "unit": "kW", "scale": 1.0, "enabled": True},
                 {"point_ref": "AI:1", "sensor_type": "HVAC_temp", "enabled": True},          # non-numeric
                 {"point_ref": "3204", "sensor_type": "building_energy_kwh", "enabled": False},  # disabled
             ]},
            {"name": "AHU", "protocol": "bacnet", "connection_config": {}, "points": []},     # non-modbus
        ],
    }
    devs = g.platform_config_to_devices(payload)
    assert len(devs) == 1 and devs[0]["host"] == "10.0.0.5"
    assert len(devs[0]["points"]) == 1 and devs[0]["points"][0]["register"] == 3060
    assert devs[0]["points"][0]["building_id"] == "B005"


def test_register_spec_parser():
    pts = g.parse_register_specs(["3060:building_kwh:kW:1", "100:HVAC_temp"], building_id="B005")
    assert pts[0]["register"] == 3060 and pts[0]["scale"] == 1.0 and pts[0]["unit"] == "kW"
    assert pts[1]["register"] == 100 and pts[1]["sensor_type"] == "HVAC_temp"
    assert pts[0]["building_id"] == "B005"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print("ALL %d TESTS PASSED" % len(tests))
