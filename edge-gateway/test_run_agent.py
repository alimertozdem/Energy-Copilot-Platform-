#!/usr/bin/env python3
"""Tests for the unified agent launcher dispatch (no protocol deps)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import run_agent as g  # noqa: E402


def test_plan_mixed_fleet():
    plan = g.plan_from_config(g.SIM_PAYLOAD)
    assert {p["protocol"] for p in plan} == {"modbus", "bacnet", "mqtt", "rest"}
    by = {p["protocol"]: p for p in plan}
    assert by["modbus"]["devices"][0]["host"] == "10.0.0.5"
    assert by["bacnet"]["devices"][0]["device_instance"] == 1001
    assert by["mqtt"]["devices"][0]["broker"] == "mqtt.local"
    assert by["rest"]["devices"][0]["endpoint"].startswith("https://")


def test_plan_single_protocol():
    p = g.plan_from_config({"building_id": "X", "devices": [g.SIM_PAYLOAD["devices"][0]]})
    assert len(p) == 1 and p[0]["protocol"] == "modbus"


def test_plan_empty_and_unknown():
    assert g.plan_from_config({"devices": []}) == []
    assert g.plan_from_config({"devices": [{"protocol": "zwave", "points": []}]}) == []


def test_plan_skips_unmappable_points():
    # a BACnet device whose only point is a non-object-ref -> no points -> skipped
    cfg = {"building_id": "X", "devices": [
        {"name": "x", "protocol": "bacnet", "connection_config": {"host": "h"},
         "points": [{"point_ref": "3060", "sensor_type": "x", "enabled": True}]}]}
    assert g.plan_from_config(cfg) == []


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print("ALL %d TESTS PASSED" % len(tests))
