"""Heating & envelope assessment (building grain, Postgres-native).

Powers the web-app Heating & HVAC page WITHOUT Fabric -- so it works for buildings
still pending a bridge (the wedge: small/mid DE Hausverwaltung, no sensors yet).
It assembles the demand side (how much heat the building needs), the supply side
(fuel cost/CO2), the envelope vs GEG, per-measure retrofit ROI, AND a sequenced
retrofit package (the decision artifact).

ENERGY LOGIC -- reuses APPROVED sources, does NOT invent:
  * Heating share by type  -> notebook 11 HVAC engine `heating_sens`
    (Office .35, Retail .28, Logistics .42, Hotel .40, Healthcare .22, Education .48,
     Datacenter .02; DEFAULT .35). Residential .60 = stated assumption (space-heating
     dominated DE MFH; not in the notebook table).
  * Fabric transmission saving (GROSS) -> docs/strategy/residential-retrofit-calculations.md
    (energy-domain approved 2026-06-11):  kWh/yr = dU x A x Gt x 24 / 1000 / eta
    with Gt = 3500 Kd (German 20/15 ref), eta = 0.90 (condensing gas). This GROSS
    transmission-loss reduction is preserved exactly (doc-validated) and reported
    in each measure's `saving_kwh_gross`.
  * DELIVERED saving = GROSS x gain-utilisation factor. A pure transmission-loss
    figure overstates the *delivered-energy* saving, because internal + solar gains
    already cover part of the load (strongly so in offices / data centres). The
    type-based utilisation factor (GAIN_UTIL) is a screening heuristic that nets this
    out and is intentionally conservative (lowers savings). It also corrects using a
    residential Gt for high-internal-gain non-residential stock.
  * Fabric savings are capped so no single measure -- and no package -- can exceed
    the building's addressable thermal demand (you cannot save more heat than you use;
    ventilation/infiltration + DHW + residual are not fixed by the envelope).
  * Operational saving 7-11% (ITG Dresden), hydraulic balancing + heating curve;
    BAFA Heizungsoptimierung subsidy applies.
  * U-before (1970s unrenovated) + U-after (GEG) + per-m2 CapEx + subsidies from the
    same approved doc. Heat pump = fuel switch via JAZ 3.0 (not a % saving).
  * Element areas estimated from floor area via archetype ratios (facade 0.48,
    roof/top-floor 0.17, windows 0.13 of floor).

Every figure is SCREENING-GRADE / indicative -- the UI says so, and shows a range.
A building-specific audit (real areas, U-values, hydraulics, metered fuel) replaces
these before commitment.
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
DISTRICT_PRICE = 0.13 # EUR/kWh (DE Fernwaerme working price)
GAS_CO2 = 0.201       # kg CO2 / kWh (natural gas)
DISTRICT_CO2 = 0.20   # kg CO2 / kWh (DE district-heat mix, conservative proxy)
CARBON_PRICE_T = 55.0 # EUR / t CO2 (nEHS today; ~149 by 2030)

# Gain-utilisation factor: delivered-energy saving as a fraction of the GROSS
# transmission-loss reduction. <1 because internal/solar gains already cover part of
# the load (high in offices/data centres, lower in residential). Screening heuristic;
# conservative (lowers savings). Also corrects residential-Gt use for non-residential.
GAIN_UTIL: dict[str, float] = {
    "Office": 0.65, "Retail": 0.70, "Healthcare": 0.70, "Education": 0.70,
    "Hotel": 0.75, "Logistics": 0.80, "Datacenter": 0.50, "Residential": 0.85,
    "Mixed": 0.72,
}
_DEFAULT_UTIL = 0.72
# Share of thermal demand the envelope can address (rest = ventilation/infiltration,
# DHW, residual). Caps any single fabric measure and the package.
FABRIC_ADDRESSABLE_SHARE = 0.68
# Realistic ceiling for a full deep-retrofit heating reduction.
PACKAGE_MAX_REDUCTION = 0.72

# Uncertainty band (+/-) on screening figures: wider when estimated, tighter when metered.
RANGE_EST = 0.25
RANGE_MEAS = 0.10

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
OP_CAPEX_PER_M2_FLOOR = 3.0  # hydraulic balancing + curve, per m2 floor (realistic commercial)
OP_SUBSIDY = 0.15            # BAFA Heizungsoptimierung (Einzelmassnahme)


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
    util = GAIN_UTIL.get(btype, _DEFAULT_UTIL)
    hp = _is_heat_pump(building)
    gas = _is_gas(building)

    # --- demand (heating energy AS METERED in the building's fuel) --------
    if consumption_annual_kwh and consumption_annual_kwh > 0:
        total_kwh = float(consumption_annual_kwh)
        heating_kwh = total_kwh * sens                 # measured total is already metered fuel
        demand_basis = "measured"
    elif area and area > 0:
        total_kwh = area * _EUI_MID.get(btype, _DEFAULT_EUI)
        thermal_demand = total_kwh * sens              # archetype HEAT demand (thermal)
        # convert to METERED fuel: heat pump draws electricity (/JAZ); else gas-equiv (/eta)
        heating_kwh = (thermal_demand / JAZ) if hp else (thermal_demand / ETA_GAS)
        demand_basis = "estimated"
    else:
        total_kwh = 0.0
        heating_kwh = 0.0
        demand_basis = "unknown"
    heating_eui = (heating_kwh / area) if area else None
    # Delivered heat demand (thermal), unified across measured/estimated. Used to cap
    # fabric measures and to sequence the package on the actual load.
    thermal_demand_kwh = heating_kwh * (JAZ if hp else ETA_GAS)
    fabric_cap_kwh = FABRIC_ADDRESSABLE_SHARE * thermal_demand_kwh  # thermal

    # --- fuel model -------------------------------------------------------
    # heating_kwh is the heating energy AS METERED in the building's fuel. Cost/CO2 =
    # metered energy x the fuel price/factor. Fabric measures reduce THERMAL demand;
    # we convert that to the metered fuel saved per the building's system (HP /JAZ,
    # else /eta -- fixes a ~3x overstatement for non-gas heat).
    gf = reference_factors.grid_emission_factor(country, year)
    fuel_assumed = False
    if hp:
        fuel_type, price, factor = "heat_pump", HP_ELEC_PRICE, gf.emission_factor_kg_kwh
    elif gas:
        fuel_type, price, factor = "gas", GAS_PRICE, GAS_CO2
    else:
        # Unknown / non-gas. DE commercial stock is largely district heat (Fernwaerme);
        # small/residential more likely gas. Surface the assumption so the user can fix it.
        explicit = getattr(building, "heating_system", None)
        if explicit:
            # Honour the fuel the user set (district/biomass/electric/etc.).
            fuel_type = explicit
            if "district" in explicit.lower() or "fern" in explicit.lower():
                price, factor = DISTRICT_PRICE, DISTRICT_CO2
            else:
                price, factor = GAS_PRICE, GAS_CO2
        else:
            # Unknown fuel: default to gas (most common DE fuel, conservative on cost)
            # but flag it loudly so the user sets the real carrier. We do NOT guess
            # district vs gas from building type -- that would impose an unverified
            # assumption; instead we surface it and recompute when the fuel is set.
            fuel_type, price, factor, fuel_assumed = "gas", GAS_PRICE, GAS_CO2, True

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

    def make_measure(key, label, tier, fuel_saved_kwh, capex_gross, subsidy,
                     note="", gross_fuel_kwh=None, thermal_useful=0.0):
        fuel_saved_kwh = max(0.0, fuel_saved_kwh)
        saving_eur = fuel_saved_kwh * price
        saving_co2 = fuel_saved_kwh * factor
        capex_net = capex_gross * (1.0 - subsidy)
        annual_value = saving_eur + saving_co2 * co2_price_kwh
        payback = (capex_net / annual_value) if annual_value > 0 else None
        return {
            "key": key, "label": label, "tier": tier,
            "saving_kwh": round(fuel_saved_kwh),
            "saving_kwh_gross": round(gross_fuel_kwh) if gross_fuel_kwh is not None else None,
            "saving_eur": round(saving_eur), "saving_co2_kg": round(saving_co2),
            "capex_gross": round(capex_gross), "capex_net": round(capex_net),
            "payback_years": round(payback, 1) if payback else None, "note": note,
            "_thermal_useful": thermal_useful, "_capex_net": capex_net,
        }

    # T0 operational -- 10% of the metered heating energy; BAFA Heizungsoptimierung subsidy.
    if heating_kwh > 0 and area:
        op_thermal = thermal_demand_kwh * 0.10
        measures.append(make_measure(
            "operational", "Hydraulic balancing + heating curve", "T0",
            heating_kwh * 0.10, area * OP_CAPEX_PER_M2_FLOOR, OP_SUBSIDY,
            "Empirical 7-11% (ITG Dresden); BAFA Heizungsoptimierung -15%.",
            gross_fuel_kwh=heating_kwh * 0.10, thermal_useful=op_thermal))

    # T1/T2 fabric measures (thermal demand reduction -> delivered fuel saved)
    if area and thermal_demand_kwh > 0:
        for el, tier in (("roof", "T1"), ("wall", "T2"), ("window", "T2")):
            u_after = U_AFTER[el]
            cur = u_now[el] if u_now[el] is not None else U_BEFORE_DEFAULT[el]
            if cur <= u_after:
                continue
            d_u = cur - u_after
            el_area = area * AREA_RATIO[el]
            thermal_gross = d_u * el_area * GT * 24.0 / 1000.0     # doc-validated GROSS
            thermal_useful = min(thermal_gross * util, fabric_cap_kwh)  # delivered, gains + cap
            fuel_saved = _fuel_saved_from_thermal(thermal_useful)
            assumed = " (U assumed: 1970s)" if u_now[el] is None else ""
            label = {"wall": "Facade insulation (WDVS)", "roof": "Top-floor / roof insulation",
                     "window": "Triple-glazed windows"}[el]
            note = (f"dU {d_u:.2f} x {round(el_area)} m2{assumed} · "
                    f"transmission -{round(thermal_gross/1000)} MWh, delivered after gains")
            measures.append(make_measure(
                f"fabric_{el}", label, tier, fuel_saved,
                el_area * CAPEX_PER_M2[el], ENVELOPE_SUBSIDY, note,
                gross_fuel_kwh=_fuel_saved_from_thermal(thermal_gross),
                thermal_useful=thermal_useful))

    # Heat-pump fuel switch (only when currently on gas/oil) -- not a % saving.
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
            "saving_kwh": None, "saving_kwh_gross": None,
            "saving_eur": round(save_eur), "saving_co2_kg": round(save_co2),
            "capex_gross": round(capex_gross), "capex_net": round(capex_net),
            "payback_years": round(payback, 1) if payback else None,
            "note": "Fuel switch (JAZ 3.0); the big CO2 + regulation lever, not a % saving.",
            "_thermal_useful": 0.0, "_capex_net": capex_net,
        })

    measures.sort(key=lambda m: (m["payback_years"] is None, m["payback_years"] or 1e9))

    # --- sequenced retrofit package (the decision artifact) ---------------
    # Each demand-reducing measure acts on the REMAINING load (non-additive). Fuel
    # switch is excluded from the reduction stack (it changes carrier, not demand).
    package = _build_package(
        measures, thermal_demand_kwh, heating_kwh, area, heating_eui,
        price, factor, co2_price_kwh, _fuel_saved_from_thermal)

    # strip internal helper keys
    for m in measures:
        m.pop("_thermal_useful", None)
        m.pop("_capex_net", None)

    # --- uncertainty band -------------------------------------------------
    band = RANGE_MEAS if demand_basis == "measured" else RANGE_EST

    return {
        "demand": {
            "heating_kwh": round(heating_kwh),
            "heating_kwh_low": round(heating_kwh * (1 - band)),
            "heating_kwh_high": round(heating_kwh * (1 + band)),
            "heating_eui_kwh_m2": round(heating_eui, 1) if heating_eui else None,
            "heating_share_pct": round(sens * 100),
            "total_kwh": round(total_kwh),
            "basis": demand_basis,
            "band_pct": round(band * 100),
        },
        "supply": {
            "fuel_type": fuel_type,
            "fuel_assumed": fuel_assumed,
            "heat_cost_eur": round(heat_cost),
            "heat_co2_kg": round(heat_co2),
            "price_eur_kwh": round(price, 3),
            "co2_factor_kg_kwh": round(factor, 3),
        },
        "envelope": envelope,
        "measures": measures,
        "package": package,
        "assumptions": {
            "method": "Transmission GROSS: dU x A x Gt x 24 / 1000 / eta (Gt=3500, eta=0.90); delivered = GROSS x gain-utilisation. Operational 7-11%. HP via JAZ 3.0.",
            "grade": "Screening-grade / indicative — a building audit replaces these before commitment.",
            "subsidy": "Envelope -20% (BAFA BEG + iSFP); operational -15% (BAFA Heizungsoptimierung); heat pump -50% (KfW up to 70%).",
            "prices": f"Gas {GAS_PRICE}, district {DISTRICT_PRICE}, HP elec {HP_ELEC_PRICE} EUR/kWh; carbon {round(CARBON_PRICE_T)} EUR/t.",
            "gains": f"Gain-utilisation {util:.2f} for {btype} (internal/solar gains already cover part of the load). Fabric capped at {round(FABRIC_ADDRESSABLE_SHARE*100)}% of thermal demand.",
        },
    }


def _build_package(measures, thermal_demand_kwh, heating_kwh, area, heating_eui,
                   price, factor, co2_price_kwh, fuel_saved_from_thermal) -> dict:
    """Sequence demand-reducing measures on the remaining load; report cumulative
    capex/saving/EUI per step + the full-package outcome, clamped to a realistic
    ceiling. Returns a JSON-safe dict (no internal keys)."""
    reducers = [m for m in measures if m["key"] != "heat_pump" and m.get("_thermal_useful", 0) > 0]
    has_fabric = any(m["key"].startswith("fabric_") for m in reducers)
    # Literature band: full deep retrofit 50-65% (envelope + operational); operational-
    # only (envelope already at/below GEG) 7-11% (ITG Dresden).
    low_pct, high_pct = (50, 65) if has_fabric else (7, 11)
    base = {
        "realistic_reduction_low_pct": low_pct,
        "realistic_reduction_high_pct": high_pct,
        "note": "Measures are not additive — each lowers the load the next acts on. Sequenced cheapest-payback-first below.",
        "steps": [],
        "full": None,
    }
    if not reducers or thermal_demand_kwh <= 0 or not area:
        return base

    # natural compounded reduction (1 - product of (1 - frac_i))
    fracs = [min(0.95, m["_thermal_useful"] / thermal_demand_kwh) for m in reducers]
    natural = 1.0
    for fr in fracs:
        natural *= (1.0 - fr)
    natural_reduction = 1.0 - natural
    scale = min(1.0, PACKAGE_MAX_REDUCTION / natural_reduction) if natural_reduction > 0 else 1.0

    remaining = thermal_demand_kwh
    cum_fuel_saved = 0.0
    cum_capex_net = 0.0
    steps = []
    for m, fr in zip(reducers, fracs):
        step_thermal = remaining * fr * scale
        remaining -= step_thermal
        cum_fuel_saved += fuel_saved_from_thermal(step_thermal)
        cum_capex_net += m["_capex_net"]
        saving_eur = cum_fuel_saved * price
        saving_co2 = cum_fuel_saved * factor
        annual_value = saving_eur + saving_co2 * co2_price_kwh
        payback = (cum_capex_net / annual_value) if annual_value > 0 else None
        eui_after = ((heating_kwh - cum_fuel_saved) / area) if area else None
        steps.append({
            "key": m["key"], "label": m["label"], "tier": m["tier"],
            "cumulative_reduction_pct": round((1.0 - remaining / thermal_demand_kwh) * 100),
            "cumulative_capex_net": round(cum_capex_net),
            "cumulative_saving_eur": round(saving_eur),
            "cumulative_co2_saved_kg": round(saving_co2),
            "heating_eui_after": round(eui_after, 1) if eui_after is not None else None,
            "payback_years": round(payback, 1) if payback else None,
        })

    last = steps[-1]
    base["steps"] = steps
    base["full"] = {
        "reduction_pct": last["cumulative_reduction_pct"],
        "capex_net": last["cumulative_capex_net"],
        "saving_eur": last["cumulative_saving_eur"],
        "co2_saved_kg": last["cumulative_co2_saved_kg"],
        "payback_years": last["payback_years"],
        "eui_before": round(heating_eui, 1) if heating_eui else None,
        "eui_after": last["heating_eui_after"],
    }
    return base
