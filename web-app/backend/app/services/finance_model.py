"""finance_model.py — pure financial primitives for the Financing module.

NO DB, fully deterministic, sandbox-testable. SUPPORT, NOT ADVICE. Centralises:
  * German subsidy programmes (unit/area-aware, eligibility) — KfW 458, BAFA BEG EM.
  * The carbon-price trajectory (post-ETS2 postponement) as THREE scenarios.
  * Energy-price inflation.
  * Discounted cash flow — NPV + simple payback, with an explicit discount rate.
  * EPC-driven value uplift ("green premium") as an indicative RANGE.

Everything future-facing is returned as a RANGE — no false precision. The UI shows
the assumptions (see `assumptions()`), the currency stamp, and the "today vs scenario"
comparison so the user can see exactly what drives each number.

CURRENCY (verified 2026-06):
  * KfW 458 Heizungsförderung: 30% base → up to 70% (climate-speed +20%, income +30%,
    efficiency +5%); eligible cost capped €30,000 per dwelling unit.
  * BAFA BEG EM (envelope/controls): 15% base + 5% with iSFP = 20%; eligible cost
    €30,000/unit/yr, €60,000 with iSFP.
  * Carbon: 2026 BEHG/nEHS corridor €55-65/t; ETS2 POSTPONED — the corridor also holds
    in 2027, market-based pricing only from 2028. EU 2030 estimate €48-80/t; tighter-cap
    analyses run higher — bracketed by the scenarios below.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Discounting + inflation
# ---------------------------------------------------------------------------
DISCOUNT_RATE = 0.04          # real discount rate for building investments (stated)
GENERAL_INFLATION = 0.02      # CPI context for CapEx escalation
ENERGY_INFLATION = {          # real annual escalation of ENERGY prices, by scenario
    "conservative": 0.01,
    "base": 0.03,
    "high": 0.05,
}

# ---------------------------------------------------------------------------
# Carbon price trajectory (EUR / t CO2) — anchor points per scenario, interpolated.
# 2026-2027 = BEHG/nEHS corridor (ETS2 postponed); 2028+ = market-based ETS2.
# Scenarios bracket the wide post-2028 uncertainty.
# ---------------------------------------------------------------------------
CARBON_PRICE_NOW = 60.0       # 2026 corridor midpoint (55-65)
CARBON_ANCHORS: dict[str, dict[int, float]] = {
    "conservative": {2026: 60, 2027: 65, 2030: 80,  2040: 120, 2050: 150},
    "base":         {2026: 60, 2027: 65, 2030: 120, 2040: 200, 2050: 250},
    "high":         {2026: 60, 2027: 65, 2030: 180, 2040: 300, 2050: 350},
}
SCENARIOS = ("conservative", "base", "high")


def carbon_price(scenario: str, year: int) -> float:
    """Interpolated carbon price (EUR/t) for a scenario + year."""
    anchors = CARBON_ANCHORS.get(scenario, CARBON_ANCHORS["base"])
    years = sorted(anchors)
    if year <= years[0]:
        return float(anchors[years[0]])
    if year >= years[-1]:
        return float(anchors[years[-1]])
    for i in range(len(years) - 1):
        y0, y1 = years[i], years[i + 1]
        if y0 <= year <= y1:
            t = (year - y0) / (y1 - y0)
            return float(anchors[y0] + (anchors[y1] - anchors[y0]) * t)
    return float(anchors[years[-1]])


# ---------------------------------------------------------------------------
# Subsidy (unit / area-aware, with eligibility)
# ---------------------------------------------------------------------------
DWELLING_M2 = 75.0            # avg DE dwelling net floor area (units estimate)
RESIDENTIAL_TYPES = {"Residential", "MFH", "Wohngebäude"}


def estimate_units(building_type: str | None, floor_area_m2: float | None,
                   declared_units: int | None = None) -> int | None:
    """Residential dwelling-unit count. Declared wins; else estimate from floor area
    (clearly indicative). Non-residential -> None (per-unit cap does not apply)."""
    if declared_units and declared_units > 0:
        return int(declared_units)
    if (building_type in RESIDENTIAL_TYPES) and floor_area_m2 and floor_area_m2 > 0:
        return max(1, round(floor_area_m2 / DWELLING_M2))
    return None


def _measure_class(measure_type: str | None) -> str:
    t = (measure_type or "").lower()
    if any(k in t for k in ("hvac", "heat", "boiler", "pump", "chiller", "district")):
        return "heating"
    if any(k in t for k in ("envelope", "insul", "window", "glaz", "facade", "roof", "wall")):
        return "envelope"
    if any(k in t for k in ("control", "bms", "automation", "sensor", "hydraulic", "balanc")):
        return "controls"
    if any(k in t for k in ("solar", "pv", "photovolt")):
        return "renewables"
    return "other"


def estimate_subsidy(measure_type: str | None, capex_eur: float | None,
                     building_type: str | None, units: int | None,
                     has_isfp: bool = False) -> dict:
    """Indicative subsidy for a measure. Unit-aware for residential (cap × units),
    project-based for non-residential. Returns a RATE range + eligible cost + grant
    range; never a single false-precise number. SUPPORT, NOT ADVICE."""
    capex = float(capex_eur or 0.0)
    cls = _measure_class(measure_type)
    residential = building_type in RESIDENTIAL_TYPES
    n_units = units if (residential and units) else 1

    if cls == "renewables":
        return {"program": "EEG / separate", "scheme": "Solar PV", "eligible": False,
                "rate_low_pct": 0, "rate_high_pct": 0, "eligible_cost_eur": None,
                "grant_low_eur": None, "grant_high_eur": None, "units_basis": None,
                "note": "PV is funded via EEG feed-in / separate schemes, not BEG."}
    if cls == "other":
        return {"program": "—", "scheme": "Check eligibility", "eligible": False,
                "rate_low_pct": 0, "rate_high_pct": 0, "eligible_cost_eur": None,
                "grant_low_eur": None, "grant_high_eur": None, "units_basis": None,
                "note": "No standard BEG match — assess case by case."}

    if cls == "heating":
        program, scheme = "KfW 458", "Heizungsförderung — renewable heating"
        rate_low, rate_high = 30, 70
        per_unit_cap = 30000.0
    else:  # envelope / controls
        program, scheme = "BAFA BEG EM", "Envelope / system tech"
        rate_low, rate_high = 15, (20 if has_isfp else 15)
        per_unit_cap = (60000.0 if has_isfp else 30000.0)

    if residential:
        eligible_cost = min(capex, per_unit_cap * n_units) if capex > 0 else 0.0
        units_basis = n_units
        note = (f"Residential: eligible cost capped €{int(per_unit_cap):,}/unit × "
                f"{n_units} unit(s)" + (" (iSFP-raised)" if has_isfp and cls != 'heating' else "") + ".")
    else:
        # Non-residential BEG (NWG): project-based, no per-Wohneinheit cap. Use the
        # full CapEx as the eligible base (annual project caps apply — verify live).
        eligible_cost = capex
        units_basis = None
        note = "Non-residential BEG (NWG): project-based; verify the annual project cap."

    grant_low = (rate_low / 100.0) * eligible_cost if eligible_cost > 0 else None
    grant_high = (rate_high / 100.0) * eligible_cost if eligible_cost > 0 else None
    return {
        "program": program, "scheme": scheme, "eligible": True,
        "rate_low_pct": rate_low, "rate_high_pct": rate_high,
        "eligible_cost_eur": round(eligible_cost) if eligible_cost else None,
        "grant_low_eur": round(grant_low) if grant_low is not None else None,
        "grant_high_eur": round(grant_high) if grant_high is not None else None,
        "units_basis": units_basis,
        "note": note,
    }


# ---------------------------------------------------------------------------
# Discounted cash flow: NPV + payback, with energy inflation + carbon escalation
# ---------------------------------------------------------------------------
def simple_payback(capex_net: float, annual_saving_eur: float) -> float | None:
    if annual_saving_eur is None or annual_saving_eur <= 0:
        return None
    return round(capex_net / annual_saving_eur, 1)


def npv_case(capex_net: float, annual_energy_saving_eur: float, annual_co2_t: float,
             lifetime: int, scenario: str, start_year: int,
             discount_rate: float = DISCOUNT_RATE) -> dict:
    """Discounted NPV of a measure over its lifetime under one scenario. Annual savings
    = energy saving escalated by energy inflation + carbon saving valued at the scenario
    carbon price for that year. Returns NPV, discounted payback, lifetime totals."""
    e_infl = ENERGY_INFLATION.get(scenario, ENERGY_INFLATION["base"])
    energy0 = float(annual_energy_saving_eur or 0.0)
    co2_t = float(annual_co2_t or 0.0)
    cap = float(capex_net or 0.0)

    npv = -cap
    cumulative = -cap
    disc_payback = None
    nominal_total = 0.0
    for t in range(1, max(1, lifetime) + 1):
        year = start_year + t
        energy_t = energy0 * ((1 + e_infl) ** (t - 1))
        carbon_t = co2_t * carbon_price(scenario, year)
        saving_t = energy_t + carbon_t
        nominal_total += saving_t
        npv += saving_t / ((1 + discount_rate) ** t)
        cumulative += saving_t
        if disc_payback is None and cumulative >= 0:
            disc_payback = t
    return {
        "scenario": scenario,
        "npv_eur": round(npv),
        "discounted_payback_years": disc_payback,
        "lifetime_saving_eur": round(nominal_total),
        "first_year_carbon_value_eur": round(co2_t * carbon_price(scenario, start_year + 1)),
    }


# ---------------------------------------------------------------------------
# EPC-driven value uplift ("green premium") — indicative %, not a EUR figure.
# ---------------------------------------------------------------------------
_EPC_LETTERS = ["A+", "A", "B", "C", "D", "E", "F", "G", "H"]
# Indicative value uplift per EPC band improvement (% of asset value). Literature on
# the "green premium / brown discount" is wide and market-specific; we use a
# deliberately conservative band and label it an estimate.
VALUE_UPLIFT_PCT_PER_BAND = (1.0, 2.5)   # low, high % per band
VALUE_UPLIFT_CAP_PCT = 15.0              # cap the cumulative claim


def _epc_index(cls: str | None) -> int | None:
    if not cls:
        return None
    c = str(cls).strip().upper()
    c = "A+" if c.startswith("A+") else c[:1]
    return _EPC_LETTERS.index(c) if c in _EPC_LETTERS else None


def value_uplift(epc_now: str | None, epc_after: str | None) -> dict:
    """Indicative property value uplift from an EPC-class improvement. Returns a %
    range only (no EUR — that needs the owner's valuation). 'Estimate', clearly."""
    i0, i1 = _epc_index(epc_now), _epc_index(epc_after)
    if i0 is None or i1 is None or i1 >= i0:
        return {"band_jump": 0, "uplift_low_pct": 0.0, "uplift_high_pct": 0.0,
                "note": "No EPC-class improvement modelled (or class unknown)."}
    jump = i0 - i1
    low = min(VALUE_UPLIFT_CAP_PCT, jump * VALUE_UPLIFT_PCT_PER_BAND[0])
    high = min(VALUE_UPLIFT_CAP_PCT, jump * VALUE_UPLIFT_PCT_PER_BAND[1])
    return {
        "band_jump": jump,
        "uplift_low_pct": round(low, 1),
        "uplift_high_pct": round(high, 1),
        "note": (f"Indicative: {jump} EPC-band improvement. The 'green premium / brown "
                 "discount' is market-specific — applied to your own valuation. Estimate, not a guarantee."),
    }


def assumptions() -> dict:
    """Everything the method panel needs to be transparent."""
    return {
        "rates_verified": "2026-06",
        "discount_rate_pct": round(DISCOUNT_RATE * 100, 1),
        "general_inflation_pct": round(GENERAL_INFLATION * 100, 1),
        "energy_inflation_pct": {k: round(v * 100, 1) for k, v in ENERGY_INFLATION.items()},
        "carbon_now_eur_t": round(CARBON_PRICE_NOW),
        "carbon_2030_eur_t": {s: round(carbon_price(s, 2030)) for s in SCENARIOS},
        "carbon_note": "2026-2027 BEHG/nEHS corridor (ETS2 postponed); market-based ETS2 from 2028. EU 2030 estimate €48-80/t; base/high reflect tighter-cap analyses.",
        "subsidy_note": "KfW 458 30-70% (€30k/unit cap); BAFA BEG EM 15-20% (€30k/unit, €60k with iSFP). Apply BEFORE signing.",
        "value_uplift_note": f"{VALUE_UPLIFT_PCT_PER_BAND[0]}-{VALUE_UPLIFT_PCT_PER_BAND[1]}% value uplift per EPC band (indicative, capped {round(VALUE_UPLIFT_CAP_PCT)}%).",
    }
