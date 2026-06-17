"""Provisional baseline estimate -- a clearly-labeled ESTIMATE for buildings that
have metadata (type + area) but no uploaded consumption yet, so the first-value
loop is never empty. Superseded by the real baseline the moment consumption is
added (the caller only surfaces this when there are zero consumption rows).

ENERGY LOGIC (product-owner approved 2026-06-16):
  annual_kWh range = typical final-energy intensity (by building type) x floor area
  EUI range        = the typical intensity itself (kWh/m2/yr)
  cost range       = annual_kWh x electricity tariff (country, year)   [real factor]
  CO2 range        = annual_kWh x grid emission factor (country, year) [real factor]

The intensity ranges are ARCHETYPE assumptions (total final energy = heating +
electricity), EU typicals; a real building can vary +-30%+, hence a RANGE and an
explicit "estimated" label, never a single value. Cost/CO2 apply the platform's
real tariff + grid factors to the energy range, with the documented caveat that
they treat energy as electricity-equivalent -- mixed-fuel buildings will differ
once the actual fuel split is known from a bill.
"""
from app.services import reference_factors

# (low, high) total final-energy intensity in kWh/m2/yr by building type.
# Datacenter is intentionally omitted -- IT load dominates and an area-based
# estimate is not meaningful, so we show no number rather than a misleading one.
TYPICAL_INTENSITY_KWH_M2_YR: dict[str, tuple[float, float]] = {
    "Office": (120.0, 220.0),
    "Retail": (180.0, 320.0),
    "Hotel": (220.0, 380.0),
    "Healthcare": (250.0, 450.0),
    "Logistics": (40.0, 110.0),
    "Residential": (100.0, 240.0),  # recalibrated 2026-06-17 (Heizspiegel/RWI); aligned with estimation engine
    "Mixed": (120.0, 220.0),
}
_DEFAULT_RANGE = (120.0, 220.0)
_UNSUPPORTED_TYPES = {"Datacenter"}


def estimate_baseline(building, year: int) -> dict | None:
    """A provisional estimate dict, or None when we cannot estimate honestly
    (no floor area, or a building type we deliberately do not model)."""
    raw_area = getattr(building, "floor_area_m2", None)
    try:
        area = float(raw_area) if raw_area is not None else None
    except (TypeError, ValueError):
        area = None
    if not area or area <= 0:
        return None

    btype = getattr(building, "building_type", None)
    if btype in _UNSUPPORTED_TYPES:
        return None

    lo_i, hi_i = TYPICAL_INTENSITY_KWH_M2_YR.get(btype or "", _DEFAULT_RANGE)
    kwh_low = lo_i * area
    kwh_high = hi_i * area

    gf = reference_factors.grid_emission_factor(building.country_code, year)
    tf = reference_factors.electricity_tariff_avg(building.country_code, year)

    return {
        "basis": "estimated",
        "building_type": btype,
        "type_modeled": btype in TYPICAL_INTENSITY_KWH_M2_YR,
        "country_code": building.country_code,
        "year": year,
        "eui_low": round(lo_i, 0),
        "eui_high": round(hi_i, 0),
        "annual_kwh_low": round(kwh_low, 0),
        "annual_kwh_high": round(kwh_high, 0),
        "annual_cost_eur_low": round(kwh_low * tf.avg_eur_kwh, 0),
        "annual_cost_eur_high": round(kwh_high * tf.avg_eur_kwh, 0),
        "annual_co2_kg_low": round(kwh_low * gf.emission_factor_kg_kwh, 0),
        "annual_co2_kg_high": round(kwh_high * gf.emission_factor_kg_kwh, 0),
        "tariff_eur_kwh": tf.avg_eur_kwh,
        "grid_factor_kg_kwh": gf.emission_factor_kg_kwh,
    }
