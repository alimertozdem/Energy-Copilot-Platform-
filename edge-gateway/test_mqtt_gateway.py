#!/usr/bin/env python3
"""Tests for the MQTT ingestion gateway (no paho / Azure)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mqtt_gateway as g  # noqa: E402


def test_payload_to_events():
    gw = g.MqttGateway(g.StubSink(), g.SAMPLE_POINTS)
    topic, payload = g.SAMPLE_MESSAGE
    assert gw.on_message(topic, payload) == 2
    e = gw.sink.events
    assert e[0]["sensor_type"] == "HVAC_temp" and e[0]["reading_value"] == 21.7
    assert e[0]["reading_unit"] == "C" and e[0]["building_id"] == "B003"
    assert e[1]["sensor_type"] == "CO2" and e[1]["reading_value"] == 740.0
    assert all(x["source_protocol"] == "MQTT" for x in e)


def test_partial_payload():
    gw = g.MqttGateway(g.StubSink(), g.SAMPLE_POINTS)
    assert gw.on_message("building/B003/climate", {"temperature": 19.0}) == 1


def test_batching_backoff():
    stub = g.StubSink()
    buf = g.BufferedSink(stub, max_batch=2)
    gw = g.MqttGateway(buf, g.SAMPLE_POINTS)
    gw.on_message(*g.SAMPLE_MESSAGE)
    assert len(stub.events) == 2
    buf.close()
    assert buf._buf == []
    assert g.backoff_seconds(1) == 2.0 and g.backoff_seconds(10) == 60.0


def test_config_loader():
    ra = g.build_run_args(g.load_config(str(pathlib.Path(__file__).resolve().parent / "config.mqtt.example.json")))
    assert len(ra["devices"]) >= 1 and ra["devices"][0]["broker"]


def test_platform_parser():
    payload = {"building_id": "B003", "devices": [
        {"name": "Zone", "protocol": "mqtt",
         "connection_config": {"broker": "mqtt.local", "port": 1883, "base_topic": "building/+/climate"},
         "points": [{"point_ref": "temperature", "sensor_type": "HVAC_temp", "enabled": True},
                    {"point_ref": "co2", "sensor_type": "CO2", "enabled": False}]},
        {"name": "M", "protocol": "rest_api", "connection_config": {}, "points": []}]}
    devs = g.platform_config_to_devices(payload)
    assert len(devs) == 1 and devs[0]["broker"] == "mqtt.local"
    assert len(devs[0]["points"]) == 1 and devs[0]["points"][0]["building_id"] == "B003"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print("ALL %d TESTS PASSED" % len(tests))
