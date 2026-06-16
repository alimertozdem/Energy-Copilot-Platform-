"""Heating & envelope assessment (building grain, Postgres-native).

Powers the web-app Heating & HVAC page WITHOUT Fabric -- so it works for buildings
still pending a bridge (the wedge: small/mid DE Hausverwaltung, no sensors yet).
It assembles the demand side (how much heat the building needs), the supply side
(fuel cost/CO2), the envelope vs GEG, and per-measure retrofit ROI.

ENERGY LOGIC -- reuses APPROVED sources, does NOT invent:
  * Heating share by type  -> notebook 11 HVAC engine `heating_sens`
    (Office .35, Retail .28, Logistics .42, Hotel .40, Healthcare .22, Education .48,
     Datacenter .02; DEFAULT .35). Residential .60 = stated assumption (space-heating
     dominated DE MFH; not in the notebook table).
  * Fabric transmission saving -> docs/strategy/residential-retrofit-calculations.md
    (energy-domain approved 2026-06-11):  kWh/yr = dU x A x Gt x 24 / 1000 / eta
    with Gt = 3500 Kd (German 20/15 ref), eta = 0.90 (condensing gas).
  * Operational saving 10% (ITG Dresden 7-11%, hydraulic balancing + heating curve).
  * U-before (1970s unrenovated) + U-after (GEG) + per-m2 CapEx + subsidies all from
    the same approved doc. Heat pump = fuel switch via JAZ 3.0 (not a % saving).
  * Element areas estimated from floor area via archetype ratios derived from the
    doc's worked example (facade 0.48, roof/top-floor 0.17, windows 0.13 of floor).

Every figure is SCREENING-GRADE / indicative -- the UI must say so. A building-
specific audit (real areas, U-values, hydraulics) replaces these before commitment.
"""
from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
from typing import Any

from app.services import reference_factors

# --- approved constants ----------------------------------------------------

# notebook 11 heating_sens (annual heating share of total final energy) + Residential.
HEATING_SENS: dict[str, float] = {
    "Office": 0.35, "Retail": 0.28, "Logistics": 0.42, "Hotel": 0.40,
    "Healthcare": 0.22, "Education": 0.48, "Datacenter": 0.02, "Residential": 0.60,
    "Mixed": 0.35,
}
_DEFAULT_SENS = 0.35

# Provisional total EUI midpoints (kWh/m2/yr) — approved baseline_estimate ranges.
_EUI_MID: dict[str, float] = {
    "Office": 170, "Retail": 250, "Hotel": 300, "Healthcare": 350,
    "Logistics": 75, "Residential": 135, "Mixed": 170,
}
_DEFAULT_EUI = 170.0

GT = 3500.0            # Gradtagzahl (Kd), German 20/15 reference
ETA_GAS = 0.90        # condensing-gas seasonal efficiency
JAZ = 3.0             # air-source heat-pump seasonal performance (fuel switch)
GAS_PRICE = 0.11      # EUR/kWh (2026 working price)
HP_ELEC_PRICE = 0.25  # EUR/kWh (heat-pump tariff)
GAS_CO2 = 0.201       # kg CO2 / kWh (natural gas)
CARBON_PRICE_T = 55.0 # EUR / t CO2 (nEHS today; ~149 by 2030)

# GEG Anlage 7 component U-limits (W/m2K) — also the retrofit "after" targets.
GEG_LIMIT = {"wall": 0.24, "roof": 0.20, "window": 1.30}
# Retrofit "after" U-values (approved doc; <= GEG limit).
U_AFTER = {"wall": 0.22, "roof": 0.20, "window": 0.95}
# 1970s-unrenovated "before" U-values used when the building's own value is missing.
U_BEFORE_DEFAULT = {"wall": 1.2, "roof": 0.8, "window": 2.7}
# Element area as a fraction of floor area (archetype, from the doc's worked example).
AREA_RATIO = {"wall": 0.48, "roof": 0.17, "window": 0.13}
# Gross CapEx per m2 of ELEMENT (EUR), derived from the doc example; envelope subsidy 20%.
CAPEX_PER_M2 = {"wall": 160.0, "roof": 40.0, "window": 443.0}
ENVELOPE_SUBSIDY = 0.20  # BAFA BEG + iSFP bonus
OP_CAPEX_PER_M2_FLOOR = 7.0  # hydraulic balancing + curve, per m2 floor (not subsidised)


def _f(v: Any) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _is_gas(building) -> bool:
    if getattr(building, "has_gas_heating", None) is True:
        return True
    hs = (getattr(building, "heating_system", None) or "").lower()
    return hs in {"gas_boiler", "gas", "oil"}


def _is_heat_pump(building) -> bool:
    return (getattr(building, "heating_system", None) or "").lower() == "heat_pump"


def assess(building, consumption_annual_kwh: float | None) -> dict:
    """Full heating assessment for one building. consumption_annual_kwh = measured
    total annual energy when available (from uploaded bills), else None."""
    area = _f(getattr(building, "floor_area_m2", None))
    btype = getattr(building, "building_type", None) or "Mixed"
    country = getattr(building, "country_code", None)
    year = datetime.now(dt_timezone.utc).year
    sens = HEATING_SENS.get(btype, _DEFAULT_SENS)

    # --- demand (heating energy AS METERED in the building's fuel) --------
    if consumption_annual_kwh and consumption_annual_kwh > 0:
        total_kwh = float(consumption_annual_kwh)
        heating_kwh = total_kwh * sens                 # measured total is already metered fuel
        demand_basis = "measured"
    elif area and area > 0:
        total_kwh = area * _EUI_MID.get(btype, _DEFAULT_EUI)
        thermal_demand = total_kwh * sens              # archetype HEAT demand (thermal)
        # convert to METERED fuel: heat pump draws electricity (/JAZ); else gas-equiv (/eta)
        heating_kwh = (thermal_demand / JAZ) if _is_heat_pump(building) else (thermal_demand / ETA_GAS)
        demand_basis = "estimated"
    else:
        total_kwh = 0.0
        heating_kwh = 0.0
        demand_basis = "unknown"
    heating_eui = (heating_kwh / area) if area else None

    # --- fuel model -------------------------------------------------------
    # heating_kwh is the heating energy AS METERED in the building's fuel (gas kWh
    # for gas; electricity kWh for a heat pump). Cost/CO2 = metered energy x the
    # fuel price/factor. Fabric measures reduce THERMAL demand; we convert that to
    # the metered fuel saved per the building's system (so HP savings are /JAZ,
    # not gas-fuel-equivalent — fixes a ~3x overstatement for non-gas heat).
    gas = _is_gas(building)
    hp = _is_heat_pump(building)
    gf = reference_factors.grid_emission_factor(country, year)
    if hp:
        fuel_type, price, factor = "heat_pump", HP_ELEC_PRICE, gf.emission_factor_kg_kwh
    elif gas:
        fuel_type, price, factor = "gas", GAS_PRICE, GAS_CO2
    else:
        # district / biomass / electric / unknown -> gas-equivalent proxy (DE heat
        # is gas-dominated; conservative, avoids overstating retrofit savings).
        fuel_type = getattr(building, "heating_system", None) or "other"
        price, factor = GAS_PRICE, GAS_CO2

    heat_cost = heating_kwh * price
    heat_co2 = heating_kwh * factor

    def _fuel_saved_from_thermal(thermal_kwh: float) -> float:
        """Metered fuel / electricity saved by reducing heat demand by thermal_kwh."""
        if hp:
            return thermal_kwh / JAZ      # electricity drawn by the pump
        return thermal_kwh / ETA_GAS      # gas-equivalent fuel

    # --- envelope vs GEG --------------------------------------------------
    u_now = {
        "wall": _f(getattr(building, "wall_u_value", None)),
        "roof": _f(getattr(building, "roof_u_value", None)),
        "window": _f(getattr(building, "window_u_value", None)),
    }
    envelope = []
    for el in ("wall", "roof", "window"):
        cur = u_now[el]
        limit = GEG_LIMIT[el]
        status = "unknown" if cur is None else ("pass" if cur <= limit else "fail")
        envelope.append({"element": el, "u_current": cur, "u_target": limit, "status": status})

    # --- measures ---------------------------------------------------------
    measures: list[dict] = []
    co2_price_kwh = CARBON_PRICE_T / 1000.0  # EUR per kg

    def add_measure(key, label, tier, fuel_saved_kwh, capex_gross, subsidy, note=""):
        fuel_saved_kwh = max(0.0, fuel_saved_kwh)
        saving_eur = fuel_saved_kwh * price
        saving_co2 = fuel_saved_kwh * factor
        capex_net = capex_gross * (1.0 - subsidy)
        annual_value = saving_eur + saving_co2 * co2_price_kwh
        payback = (capex_net / annual_value) if annual_value > 0 else None
        measures.append({
            "key": key, "label": label, "tier": tier,
            "saving_kwh": round(fuel_saved_kwh), "saving_eur": round(saving_eur),
            "saving_co2_kg": round(saving_co2), "capex_gross": round(capex_gross),
            "capex_net": round(capex_net),
            "payback_years": round(payback, 1) if payback else None, "note": note,
        })

    # T0 operational -- 10% of the metered heating energy
    if heating_kwh > 0 and area:
        add_measure("operational", "Hydraulic balancing + heating curve", "T0",
                    heating_kwh * 0.10, area * OP_CAPEX_PER_M2_FLOOR, 0.0,
                    "Empirical 7-11% (ITG Dresden); fastest payback.")

    # T1/T2 fabric measures (thermal demand reduction -> metered fuel saved)
    if area:
        for el, tier in (("roof", "T1"), ("wall", "T2"), ("window", "T2")):
            u_after = U_AFTER[el]
            cur = u_now[el] if u_now[el] is not None else U_BEFORE_DEFAULT[el]
            if cur <= u_after:
                continue
            d_u = cur - u_after
            el_area = area * AREA_RATIO[el]
            thermal = d_u * el_area * GT * 24.0 / 1000.0
            fuel_saved = _fuel_saved_from_thermal(thermal)
            assumed = " (U assumed: 1970s)" if u_now[el] is None else ""
            label = {"wall": "Facade insulation (WDVS)", "roof": "Top-floor / roof insulation",
                     "window": "Triple-glazed windows"}[el]
            add_measure(f"fabric_{el}", label, tier, fuel_saved,
                        el_area * CAPEX_PER_M2[el], ENVELOPE_SUBSIDY,
                        f"dU {d_u:.2f} x {round(el_area)} m2{assumed}")

    # Heat-pump fuel switch (only when currently on gas/oil)
    if gas and heating_kwh > 0 and area:
        thermal = heating_kwh * ETA_GAS   # gas fuel -> delivered heat
        elec = thermal / JAZ              # electricity the pump would draw
        new_cost = elec * HP_ELEC_PRICE
        new_co2 = elec * gf.emission_factor_kg_kwh
        save_eur = heating_kwh * GAS_PRICE - new_cost
        save_co2 = heating_kwh * GAS_CO2 - new_co2
        capex_gross = area * 140.0
        capex_net = capex_gross * 0.50
        annual_value = save_eur + save_co2 * co2_price_kwh
        payback = (capex_net / annual_value) if annual_value > 0 else None
        measures.append({
            "key": "heat_pump", "label": "Switch to air-source heat pump", "tier": "T2",
            "saving_kwh": None, "saving_eur": round(save_eur), "saving_co2_kg": round(save_co2),
            "capex_gross": round(capex_gross), "capex_net": round(capex_net),
            "payback_years": round(payback, 1) if payback else None,
            "note": "Fuel switch (JAZ 3.0); the big CO2 + regulation lever, not a % saving.",
        })

    measures.sort(key=lambda m: (m["payback_years"] is None, m["payback_years"] or 1e9))

    return {
        "demand": {
            "heating_kwh": round(heating_kwh),
            "heating_eui_kwh_m2": round(heating_eui, 1) if heating_eui else None,
            "heating_share_pct": round(sens * 100),
            "total_kwh": round(total_kwh),
            "basis": demand_basis,
        },
        "supply": {
            "fuel_type": fuel_type,
            "heat_cost_eur": round(heat_cost),
            "heat_co2_kg": round(heat_co2),
            "price_eur_kwh": round(price, 3),
            "co2_factor_kg_kwh": round(factor, 3),
        },
        "envelope": envelope,
        "measures": measures,
        "package": {
            "realistic_reduction_low_pct": 50,
            "realistic_reduction_high_pct": 65,
            "note": "Measures are not additive — each lowers the load the next acts on. A full package realistically reaches 50-65% heating reduction.",
        },
        "assumptions": {
            "method": "Transmission: dU x A x Gt x 24 / 1000 / eta (Gt=3500, eta=0.90). Operational 7-11%. HP via JAZ 3.0.",
            "grade": "Screening-grade / indicative — a building audit replaces these before commitment.",
            "subsidy": "Envelope -20% (BAFA BEG + iSFP); heat pump -50% (KfW up to 70%).",
            "prices": f"Gas {GAS_PRICE} EUR/kWh, HP elec {HP_ELEC_PRICE}, carbon {round(CARBON_PRICE_T)} EUR/t.",
        },
    }
