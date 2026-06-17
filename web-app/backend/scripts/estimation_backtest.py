"""Estimation engine backtest / sanity harness (BMAD Implementation + §5).

Pure functions (no DB / Fabric / network). Run from the backend root:
    PYTHONPATH=. python scripts/estimation_backtest.py

Checks: ordered+positive bands; plausible points; seasonal partial-bill
annualisation (not flat x12); 12-month -> basis='actual'; GEG EPC-class anchor;
footprint -> very_low; Datacenter -> unavailable.
Calibrated 2026-06-17 research pass (Residential band/heat_frac, GEG EPC, HDD 18C).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.estimation.engine import EngineInput, estimate  # noqa: E402


def show(label, res):
    if not res.available:
        print(f"  {label:34s}: UNAVAILABLE ({res.reason})")
        return res
    heat = round(res.eui_point * 0, 1)  # placeholder; printed below per-case if needed
    print(f"  {label:34s}: [{res.confidence}/{res.basis}] "
          f"EUI {res.eui_low}-{res.eui_point}-{res.eui_high} kWh/m2/yr | "
          f"{res.annual_kwh_point} kWh | EUR {res.annual_cost_eur_point} | "
          f"{res.annual_co2_kg_point} kgCO2 | area={res.area_m2}({res.area_basis}) | "
          f"[{res.cost_basis}] {res.method}")
    assert res.eui_low <= res.eui_point <= res.eui_high, "band not ordered"
    if res.annual_kwh_point is not None:
        assert res.annual_kwh_low <= res.annual_kwh_point <= res.annual_kwh_high
    return res


def main():
    print("=== EnergyLens estimation engine — backtest / sanity (calibrated) ===")

    # B011 — 1970s Berlin MFH, gas, no bills. Unrenovated -> upper band.
    r = show("B011 Residential 1972 (no bill)",
             estimate(EngineInput(building_type="Residential", floor_area_m2=2400,
                                  construction_year=1972, country_code="DE",
                                  climate_zone="moderate", has_gas_heating=True)))
    assert 140 <= r.eui_point <= 260, r.eui_point
    heating_dhw = r.eui_point * 0.72
    assert 145 <= heating_dhw <= 190, heating_dhw   # ~ Heizspiegel "high/too high" MFH
    print(f"      -> implied heating+DHW EUI ~{heating_dhw:.0f} kWh/m2/yr (Heizspiegel unrenov. ~150-200)")

    # B001 — Berlin office ~2014, gas
    show("B001 Office 2014 (no bill)",
         estimate(EngineInput(building_type="Office", floor_area_m2=5000,
                              construction_year=2014, country_code="DE", has_gas_heating=True)))

    # Partial bill: 3 winter months — must annualise < flat x4 (winter is high)
    r3 = show("B011 + 3 winter bills",
              estimate(EngineInput(building_type="Residential", floor_area_m2=2400,
                                   construction_year=1972, country_code="DE", climate_zone="moderate",
                                   has_gas_heating=True,
                                   bills=[("2025-01", 60000, None), ("2025-02", 52000, None),
                                          ("2025-03", 44000, None)])))
    assert r3.annual_kwh_point < (60000 + 52000 + 44000) * 4

    # 12 months -> actual, lands on the true run-rate
    twelve = [(f"2025-{m:02d}", v, None) for m, v in zip(
        range(1, 13), [60000, 52000, 44000, 28000, 16000, 9000,
                       7000, 7500, 14000, 28000, 46000, 58000])]
    r12 = show("B011 + 12 bills (actual)",
               estimate(EngineInput(building_type="Residential", floor_area_m2=2400,
                                    construction_year=1972, country_code="DE",
                                    has_gas_heating=True, bills=twelve)))
    assert r12.basis == "actual"
    assert abs(r12.annual_kwh_point - sum(v for _, v, _ in twelve)) < 1

    # GEG EPC-class anchor (A6): class D ~ 100-130 kWh/m2/yr final energy
    rd = show("Residential EPC class D (no bill)",
              estimate(EngineInput(building_type="Residential", floor_area_m2=2400,
                                   country_code="DE", epc_class="D", has_gas_heating=True)))
    assert 100 <= rd.eui_point <= 165, rd.eui_point   # pulled toward the GEG-D band

    # Oil-heated building -> fuel_split_oil
    ro = show("Office oil-heated",
              estimate(EngineInput(building_type="Office", floor_area_m2=5000,
                                   construction_year=1990, country_code="DE",
                                   heating_system="oil boiler")))
    assert ro.cost_basis == "fuel_split_oil", ro.cost_basis

    # Footprint fallback (no area) -> very_low
    rf = show("Office footprint->area",
              estimate(EngineInput(building_type="Office", construction_year=2014, country_code="DE",
                                   footprint_m2=1000, floors_above_ground=5)))
    assert rf.area_basis == "footprint" and rf.confidence == "very_low"

    # Datacenter -> not modeled
    rdc = show("Datacenter (unsupported)",
               estimate(EngineInput(building_type="Datacenter", floor_area_m2=1000, country_code="DE")))
    assert not rdc.available

    print("=== all sanity asserts passed ===")


if __name__ == "__main__":
    main()
