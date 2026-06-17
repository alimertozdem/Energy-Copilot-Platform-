"""Estimation Engine (Tier A) orchestrator -- the evidence-stacking pipeline.

L0 archetype -> L1 vintage -> L2 HDD -> (L3 area) -> L5 EPC -> L4 partial-bill,
emitting every value as {low, point, high} + confidence + method + editable.
Pure functions over an assembled ``EngineInput``; no DB / Fabric / network.

Design + signed-off assumptions: docs/architecture/estimation-engine-logic.md.
2026-06-17 research pass: L5 EPC now anchors on the real German GEG Energieausweis
final-energy class bands (kWh/m2/yr), and cost/CO2 fuel-split covers gas, oil and
district heat (electricity proxy only when the heating fuel is unknown).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.services import reference_factors
from app.services.estimation import archetypes, vintage, factors


@dataclass
class EngineInput:
    building_type: Optional[str] = None
    floor_area_m2: Optional[float] = None
    conditioned_area_m2: Optional[float] = None      # gold mv_building_master
    construction_year: Optional[int] = None
    country_code: Optional[str] = None
    climate_zone: Optional[str] = None
    hdd_annual: Optional[float] = None               # gold mv_kpi_daily Σ (18 C base); else None -> normal
    epc_class: Optional[str] = None
    bills: list = field(default_factory=list)        # list[(period 'YYYY-MM', energy_kwh, cost_eur|None)]
    footprint_m2: Optional[float] = None
    floors_above_ground: Optional[int] = None
    building_height_m: Optional[float] = None
    has_gas_heating: Optional[bool] = None
    heating_system: Optional[str] = None
    year: int = 2025                                 # reporting year for factor lookups


@dataclass
class EngineResult:
    available: bool
    reason: Optional[str] = None
    basis: str = "estimated"                          # estimated | actual
    confidence: str = "low"                           # high | medium | low | very_low
    method: str = ""
    building_type: Optional[str] = None
    area_m2: Optional[float] = None
    area_basis: Optional[str] = None                  # user | gold | footprint | none
    eui_low: Optional[float] = None
    eui_point: Optional[float] = None
    eui_high: Optional[float] = None
    annual_kwh_low: Optional[float] = None
    annual_kwh_point: Optional[float] = None
    annual_kwh_high: Optional[float] = None
    annual_cost_eur_low: Optional[float] = None
    annual_cost_eur_point: Optional[float] = None
    annual_cost_eur_high: Optional[float] = None
    annual_co2_kg_low: Optional[float] = None
    annual_co2_kg_point: Optional[float] = None
    annual_co2_kg_high: Optional[float] = None
    cost_basis: str = "fuel_split"                    # fuel_split_<fuel> | electricity_proxy
    editable_fields: list = field(default_factory=list)


# A6 -- German GEG Energieausweis final-energy efficiency classes (kWh/m2/yr).
# Source: GEG Anlage 10 (A+ <30 ... H >250). These are residential (Wohngebaeude),
# final energy per m2 Gebaeudenutzflaeche (AN ~1.2x Wohnflaeche) -- so a screening
# anchor with a wide sigma; non-residential letter scales differ.
_EPC_GEG: dict[str, tuple[float, float]] = {
    "A+": (0.0, 30.0), "A": (30.0, 50.0), "B": (50.0, 75.0), "C": (75.0, 100.0),
    "D": (100.0, 130.0), "E": (130.0, 160.0), "F": (160.0, 200.0),
    "G": (200.0, 250.0), "H": (250.0, 350.0),
}


def _blend(v1: float, w1: float, v2: float, w2: float) -> tuple[float, float]:
    """Inverse-variance blend of two relative-uncertainty estimates (A5)."""
    s1 = max(w1 * v1, 1e-6) ** 2
    s2 = max(w2 * v2, 1e-6) ** 2
    var = 1.0 / (1.0 / s1 + 1.0 / s2)
    v = (v1 / s1 + v2 / s2) * var
    w = (var ** 0.5) / v if v else 0.0
    return v, w


def _resolve_area(inp: EngineInput) -> tuple[Optional[float], Optional[float], str]:
    if inp.floor_area_m2 and inp.floor_area_m2 > 0:
        return float(inp.floor_area_m2), 0.0, "user"
    if inp.conditioned_area_m2 and inp.conditioned_area_m2 > 0:
        return float(inp.conditioned_area_m2), 0.05, "gold"
    if inp.footprint_m2 and inp.footprint_m2 > 0:                       # A7 gap-fill only
        storeys = inp.floors_above_ground
        if not storeys and inp.building_height_m:
            storeys = max(1, round(inp.building_height_m / 3.2))
        if storeys:
            return float(inp.footprint_m2) * storeys * 0.8, 0.35, "footprint"
    return None, None, "none"


def _annualize_fraction(months: list, heat_frac: float) -> float:
    """Fraction of annual energy the observed calendar months represent (A4)."""
    shape = archetypes.HEATING_MONTHLY_SHAPE
    ssum = sum(shape) or 1.0
    frac = 0.0
    for m in months:
        if 1 <= m <= 12:
            heat = shape[m - 1] / ssum
            frac += heat_frac * heat + (1.0 - heat_frac) * (1.0 / 12.0)
    return frac


def _epc_eui(epc_class: Optional[str]) -> Optional[tuple]:
    """A6 -- map a German Energieausweis class to a final-energy EUI anchor
    (class-band midpoint) + a wide relative sigma (asset rating, AN area basis)."""
    c = (epc_class or "").strip().upper().replace(" ", "")
    key = "A+" if c.startswith("A+") else c[:1]
    band = _EPC_GEG.get(key)
    if not band:
        return None
    return (band[0] + band[1]) / 2.0, 0.22


def _confidence(basis: str, n_bills_used: int, area_basis: str, method: list) -> str:
    if basis == "actual":
        return "high"
    if n_bills_used >= 1:
        return "medium"
    if area_basis == "footprint":
        return "very_low"
    if ("vintage" in method and "hdd" in method) or "epc" in method:
        return "medium"
    return "low"


def estimate(inp: EngineInput) -> EngineResult:
    arche = archetypes.get(inp.building_type)
    if arche is None:
        return EngineResult(available=False, reason="building_type_not_modeled",
                            building_type=inp.building_type)

    method: list = ["archetype"]
    eui = (arche.eui_lo + arche.eui_hi) / 2.0
    w = (arche.eui_hi - arche.eui_lo) / (arche.eui_lo + arche.eui_hi)

    # L1 vintage -- reposition within the band
    p = vintage.band_position(inp.construction_year)
    if p is not None:
        eui = arche.eui_lo + p * (arche.eui_hi - arche.eui_lo)
        w *= 0.8
        method.append("vintage")

    # L2 climate -- scale the heating fraction only
    hdd = inp.hdd_annual or factors.hdd_normal(inp.country_code, inp.climate_zone)
    if hdd:
        m_clim = hdd / factors.HDD_REF
        eui = eui * ((1.0 - arche.heat_frac) + arche.heat_frac * m_clim)
        w *= 0.95
        method.append("hdd")

    # L5 EPC anchor -- inverse-variance blend (below a bill, above bare prior)
    if inp.epc_class:
        epc = _epc_eui(inp.epc_class)
        if epc:
            eui, w = _blend(eui, w, epc[0], epc[1])
            method.append("epc")

    # area
    area, w_area, area_basis = _resolve_area(inp)

    # L4 partial-bill anchor (strongest)
    basis = "estimated"
    bills = [b for b in (inp.bills or []) if b and b[1] is not None and float(b[1]) > 0]
    bills.sort(key=lambda b: b[0])
    n = len(bills)
    n_used = 0
    if area and n >= 12:
        annual = sum(float(b[1]) for b in bills[-12:])
        eui = annual / area
        w = 0.05
        basis = "actual"
        method = ["actual_bill_12m"]
        n_used = n
    elif area and 1 <= n < 12:
        months = [int(b[0][5:7]) for b in bills if len(b[0]) >= 7]
        frac = _annualize_fraction(months, arche.heat_frac)
        if frac > 0:
            annual_bill = sum(float(b[1]) for b in bills) / frac
            eui_bill = annual_bill / area
            w_bill = 0.08 if n >= 6 else 0.15
            eui, w = _blend(eui, w, eui_bill, w_bill)
            method.append(f"bill_{n}m")
            n_used = n

    # derive E (combine EUI + area uncertainty in quadrature)
    if area:
        w_e = (w ** 2 + (w_area or 0.0) ** 2) ** 0.5
        kwh = eui * area
    else:
        w_e = w
        kwh = None

    res = EngineResult(
        available=True, basis=basis, building_type=arche.building_type,
        area_m2=round(area, 0) if area else None, area_basis=area_basis,
        method=" · ".join(method),
        eui_low=round(eui * (1 - w), 1), eui_point=round(eui, 1), eui_high=round(eui * (1 + w), 1),
        confidence=_confidence(basis, n_used, area_basis, method),
        editable_fields=["building_type", "floor_area_m2", "construction_year",
                         "country_code", "epc_class", "heating_system"],
    )

    if kwh is not None:
        res.annual_kwh_low = round(kwh * (1 - w_e), 0)
        res.annual_kwh_point = round(kwh, 0)
        res.annual_kwh_high = round(kwh * (1 + w_e), 0)
        _derive_cost_co2(res, kwh, w_e, inp, arche.heat_frac)

    return res


def _derive_cost_co2(res: EngineResult, kwh: float, w_e: float,
                     inp: EngineInput, heat_frac: float) -> None:
    tariff = reference_factors.electricity_tariff_avg(inp.country_code, inp.year).avg_eur_kwh
    grid = reference_factors.grid_emission_factor(inp.country_code, inp.year).emission_factor_kg_kwh
    fuel = factors.heating_fuel(inp.country_code, inp.heating_system, bool(inp.has_gas_heating))
    if fuel:                                                           # A8 fuel-split
        kind, fprice, fef = fuel
        cost = heat_frac * kwh * fprice + (1 - heat_frac) * kwh * tariff
        co2 = heat_frac * kwh * fef + (1 - heat_frac) * kwh * grid
        res.cost_basis = f"fuel_split_{kind}"
    else:                                                             # electric / heat-pump / unknown
        cost = kwh * tariff
        co2 = kwh * grid
        res.cost_basis = "electricity_proxy"
    res.annual_cost_eur_low = round(cost * (1 - w_e), 0)
    res.annual_cost_eur_point = round(cost, 0)
    res.annual_cost_eur_high = round(cost * (1 + w_e), 0)
    res.annual_co2_kg_low = round(co2 * (1 - w_e), 0)
    res.annual_co2_kg_point = round(co2, 0)
    res.annual_co2_kg_high = round(co2 * (1 + w_e), 0)
