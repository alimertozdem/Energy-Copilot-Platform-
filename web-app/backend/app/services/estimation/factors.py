"""Climate (HDD) normals + heating-fuel screening factors for the engine.

HDD_REF + normals = A2; heating-fuel price/EF for the cost-CO2 fuel-split = A8
(signed off 2026-06-17, extended to oil + district heat in the research pass).

HDD BASE CONVENTION (important, 2026-06-17): we use an **18 C base** throughout,
consistent with the gold ``mv_kpi_daily.hdd_day`` and open-meteo. This is NOT the
German VDI 3807 Gradtagzahl (20/15 base, ~3500 Kd) -- mixing the two would bias
the heating estimate ~10-15%. HDD_REF is the German national normal at 18 C base.
Normals are screening-grade, seeded offline (DWD / open-meteo); for a bridged
building the engine uses the gold HDD instead of these.
"""
from typing import Optional

# A2 -- reference climate the archetype bands assume (DE national, 18 C base).
HDD_REF = 3200.0

_HDD: dict[str, dict[str, float]] = {
    "DE": {"default": 3200.0, "cold": 3800.0, "moderate": 3200.0, "mild": 2800.0},
    "AT": {"default": 3500.0, "cold": 4200.0, "moderate": 3500.0, "mild": 2900.0},
    "NL": {"default": 2900.0},
    "FR": {"default": 2400.0, "cold": 3200.0, "moderate": 2400.0, "mild": 1700.0},
    "PL": {"default": 3600.0},
    "TR": {"default": 1600.0, "cold": 2600.0, "moderate": 1600.0, "mild": 1000.0},
    "EU": {"default": 3000.0},
}
_HDD_FALLBACK = 3000.0

# A8 -- heating fuel: (ef_kg_kwh, {country: indicative price EUR/kWh}).
# Gas EF 0.201 confirmed (UBA Erdgas ~0.20-0.202, Hi basis). Oil/district-heat
# added in the research pass. Prices indicative 2026 (Heizspiegel/BDEW); editable.
GAS_EF_KG_KWH = 0.201
_FUEL: dict[str, tuple[float, dict]] = {
    "gas":           (0.201, {"DE": 0.11, "AT": 0.10, "NL": 0.10, "FR": 0.10, "TR": 0.035}),
    "oil":           (0.266, {"DE": 0.10, "AT": 0.10, "FR": 0.10}),
    "district_heat": (0.200, {"DE": 0.12, "AT": 0.11, "NL": 0.10}),
}
_FUEL_PRICE_FALLBACK = {"gas": 0.09, "oil": 0.10, "district_heat": 0.11}


def hdd_normal(country_code: Optional[str], climate_zone: Optional[str] = None) -> float:
    code = (country_code or "").strip().upper()
    table = _HDD.get(code)
    if not table:
        return _HDD_FALLBACK
    if climate_zone:
        z = climate_zone.strip().lower()
        if z in table:
            return table[z]
    return table.get("default", _HDD_FALLBACK)


def gas_price(country_code: Optional[str]) -> float:
    code = (country_code or "").strip().upper()
    return _FUEL["gas"][1].get(code, _FUEL_PRICE_FALLBACK["gas"])


def heating_fuel(country_code: Optional[str], heating_system: Optional[str],
                 has_gas: bool) -> Optional[tuple]:
    """Resolve the heating fuel -> (kind, price_eur_kwh, ef_kg_kwh), or ``None``
    for electric / heat-pump / unknown (caller falls back to electricity)."""
    hs = (heating_system or "").lower()
    code = (country_code or "").strip().upper()
    kind = None
    if has_gas or "gas" in hs:
        kind = "gas"
    elif "oil" in hs or "oel" in hs or "öl" in hs or "heizöl" in hs:
        kind = "oil"
    elif "district" in hs or "fern" in hs:
        kind = "district_heat"
    if kind is None:
        return None
    ef, prices = _FUEL[kind]
    return kind, prices.get(code, _FUEL_PRICE_FALLBACK[kind]), ef
