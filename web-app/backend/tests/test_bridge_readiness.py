"""Unit tests for the bridge-readiness assessment (Access Layer 3).

Pure-compute, no DB. Verifies the data-tier-aware gating: a building unlocks
exactly the pages its data earns, with honest reasons — never a blanket "all
pages". Thresholds under test are the documented assumptions in the service
(trends ~6 mo, benchmark ~3 mo + area + type, forecast ~12 mo).
"""
from app.services import bridge_readiness as br


def _by_key(result: dict) -> dict[str, str]:
    """Map page key -> status for easy assertions."""
    return {p["key"]: p["status"] for p in result["pages"]}


def _base(**over):
    """A baseline call with everything off; override per test."""
    kw = dict(
        building_type=None,
        floor_area_m2=None,
        pv_capacity_kwp=None,
        epc_class=None,
        consumption_months=0,
        has_cost=False,
        has_device=False,
        iot_enabled=False,
        battery_enabled=False,
    )
    kw.update(over)
    return br.assess_readiness(**kw)


def test_empty_building_cannot_request():
    r = _base()
    assert r["overall_tier"] == "empty"
    assert r["can_request"] is False
    assert _by_key(r)["overview"] == br.LOCKED
    assert r["ready_pages"] == 0
    assert r["total_pages"] == 10


def test_baseline_csv_rich_history():
    r = _base(consumption_months=14, floor_area_m2=2500.0, building_type="Office", has_cost=True)
    s = _by_key(r)
    assert r["overall_tier"] == "baseline"
    assert r["can_request"] is True
    # Earned by 14 months + area + type:
    assert s["overview"] == br.READY
    assert s["trends"] == br.READY
    assert s["benchmark"] == br.READY
    assert s["recommendations"] == br.READY
    assert s["sustainability"] == br.READY
    # 14 >= 12 -> monthly forecast is partial (hourly needs a live feed):
    assert s["forecast"] == br.PARTIAL
    # No sensors / battery / solar:
    assert s["hvac"] == br.LOCKED
    assert s["iot"] == br.LOCKED
    assert s["battery"] == br.LOCKED
    assert s["solar"] == br.LOCKED


def test_short_history_gates_trends_and_benchmark():
    r = _base(consumption_months=2, building_type="Retail", floor_area_m2=900.0)
    s = _by_key(r)
    assert s["overview"] == br.READY  # >=1 month
    assert s["trends"] == br.LOCKED  # <3 months
    assert s["benchmark"] == br.LOCKED  # <3 months
    assert s["recommendations"] == br.PARTIAL  # >=1 but <3
    assert s["forecast"] == br.LOCKED  # <12
    assert r["overall_tier"] == "baseline"


def test_partial_trends_band():
    r = _base(consumption_months=4)
    assert _by_key(r)["trends"] == br.PARTIAL  # 3..5 inclusive


def test_iot_device_unlocks_monitoring_tier():
    r = _base(consumption_months=12, iot_enabled=True, has_device=True)
    s = _by_key(r)
    assert r["overall_tier"] == "monitoring"
    assert s["hvac"] == br.READY
    assert s["iot"] == br.READY


def test_iot_module_without_device_is_partial():
    r = _base(consumption_months=3, iot_enabled=True, has_device=False)
    s = _by_key(r)
    assert s["iot"] == br.PARTIAL
    assert s["hvac"] == br.PARTIAL
    assert any("Connect a device" in b for b in r["blocking"])


def test_full_tier_with_battery():
    r = _base(consumption_months=12, iot_enabled=True, has_device=True, battery_enabled=True)
    s = _by_key(r)
    assert r["overall_tier"] == "full"
    assert s["battery"] == br.PARTIAL  # module on, needs tariff/solar config


def test_solar_ready_with_pv_and_data():
    r = _base(consumption_months=6, pv_capacity_kwp=120.0)
    assert _by_key(r)["solar"] == br.READY


def test_device_only_can_request_without_uploads():
    # A live device but no uploaded baseline -> still something to bridge.
    r = _base(consumption_months=0, iot_enabled=True, has_device=True)
    assert r["can_request"] is True


if __name__ == "__main__":  # allow `python tests/test_bridge_readiness.py`
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
