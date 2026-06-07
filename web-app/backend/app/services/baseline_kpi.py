"""Baseline KPI engine — turns uploaded monthly consumption into real KPIs.

Pure functions over Postgres rows (no Fabric, no Spark, no network). This is the
Tier-1 "see value today" path: a building that has only uploaded a consumption
CSV / bills still gets EUI, annual energy, carbon and cost — so the dashboard
tiles and the AI advisor light up before any live Fabric data is connected. Once
the building is bridged to Fabric, the canonical gold KPIs take over and this
becomes the pre-bridge stand-in (same formulas → comparable numbers).

Energy logic (product-owner approved 2026-06-05; CLAUDE.md guardrails):
  * Window: >=12 months -> trailing 12 (a real annual run-rate). <12 months ->
    annualize (monthly average x 12) and FLAG it (``is_annualized``); new
    buildings light up early without faking precision.
  * EUI = annual kWh / floor area (m2). NOT weather-corrected (stated as such).
  * CO2 = annual kWh x grid factor(country, year) — location-based, year-indexed
    (reference_factors mirror of the Fabric ref layer). Provenance carried.
  * Cost = actual uploaded cost when every window month has it; otherwise an
    estimate = annual kWh x avg tariff(country, year), flagged ``estimated``.
  * 30-day tile figures = annual / (365.25/30) — a steady representative month,
    matching the 30-day semantics the Fabric portfolio path uses.

All outputs are indicative and carry assumptions; the engine never invents a
field it doesn't have (e.g. EUI is None without a floor area).

The ORM types are imported only for type-checking (TYPE_CHECKING) so this module
has zero runtime DB dependency: it consumes any objects exposing ``.period``,
``.energy_kwh``, ``.cost_eur`` (rows) and ``.floor_area_m2``, ``.country_code``
(building). That keeps the energy math trivially unit-testable.
"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.services import reference_factors

if TYPE_CHECKING:
    from app.db.models.building import Building, BuildingConsumption

# 30-day representative window as a fraction of an average year (365.25 days).
_DAYS_30_OF_YEAR = 30.0 / 365.25
_TRAILING_WINDOW = 12


def _f(value: Decimal | float | None) -> float | None:
    return float(value) if value is not None else None


def _empty(area: float | None) -> dict:
    """Shape returned when a building has no uploaded consumption yet."""
    return {
        "source": "uploaded_baseline",
        "has_data": False,
        "months_available": 0,
        "window_months": 0,
        "period_start": None,
        "period_end": None,
        "window": "none",
        "is_annualized": False,
        "annual_energy_kwh": None,
        "eui_kwh_m2_yr": None,
        "annual_co2_kg": None,
        "annual_cost_eur": None,
        "kwh_30d": None,
        "co2_30d_kg": None,
        "cost_30d_eur": None,
        "cost_basis": "unknown",
        "cost_rate_eur_kwh": None,
        "co2_factor_kg_kwh": None,
        "co2_factor_year": None,
        "co2_factor_confidence": None,
        "co2_factor_source": None,
        "floor_area_m2": area,
    }


def compute_baseline_kpis(
    rows: list[BuildingConsumption], building: Building
) -> dict:
    """Compute baseline KPIs for a building from its uploaded monthly rows.

    ``rows`` may be unsorted and any length; ``building`` supplies floor area
    (for EUI) and country (for the grid factor + tariff). Returns a flat dict
    matching ``schemas.consumption.BaselineKPIs``.
    """
    area = _f(building.floor_area_m2)
    if area is not None and area <= 0:
        area = None  # zero/negative area can't yield a meaningful EUI

    if not rows:
        return _empty(area)

    ordered = sorted(rows, key=lambda r: r.period)
    n = len(ordered)

    # --- Window selection: trailing-12 vs annualize-from-N ----------------
    if n >= _TRAILING_WINDOW:
        window = ordered[-_TRAILING_WINDOW:]
        window_months = _TRAILING_WINDOW
        is_annualized = False
        annual_kwh = float(sum((r.energy_kwh for r in window), Decimal(0)))
        window_label = "trailing_12"
    else:
        window = ordered
        window_months = n
        is_annualized = True
        total_kwh = float(sum((r.energy_kwh for r in window), Decimal(0)))
        annual_kwh = (total_kwh / n) * 12.0
        window_label = f"annualized_from_{n}"

    period_start = window[0].period
    period_end = window[-1].period
    year = int(period_end[:4])  # year-index the factor to the latest period

    # --- EUI --------------------------------------------------------------
    eui = (annual_kwh / area) if area else None

    # --- CO2 (location-based, year-indexed) -------------------------------
    gf = reference_factors.grid_emission_factor(building.country_code, year)
    annual_co2 = annual_kwh * gf.emission_factor_kg_kwh

    # --- Cost (actual when every window month has it; else estimate) ------
    has_full_cost = all(r.cost_eur is not None for r in window)
    if has_full_cost:
        cost_total = float(sum((r.cost_eur for r in window), Decimal(0)))
        annual_cost = (cost_total / n) * 12.0 if is_annualized else cost_total
        cost_basis = "actual"
        cost_rate = None
    else:
        tariff = reference_factors.electricity_tariff_avg(building.country_code, year)
        annual_cost = annual_kwh * tariff.avg_eur_kwh
        cost_basis = "estimated"
        cost_rate = tariff.avg_eur_kwh

    return {
        "source": "uploaded_baseline",
        "has_data": True,
        "months_available": n,
        "window_months": window_months,
        "period_start": period_start,
        "period_end": period_end,
        "window": window_label,
        "is_annualized": is_annualized,
        "annual_energy_kwh": round(annual_kwh, 0),
        "eui_kwh_m2_yr": round(eui, 1) if eui is not None else None,
        "annual_co2_kg": round(annual_co2, 0),
        "annual_cost_eur": round(annual_cost, 0),
        "kwh_30d": round(annual_kwh * _DAYS_30_OF_YEAR, 0),
        "co2_30d_kg": round(annual_co2 * _DAYS_30_OF_YEAR, 0),
        "cost_30d_eur": round(annual_cost * _DAYS_30_OF_YEAR, 0),
        "cost_basis": cost_basis,
        "cost_rate_eur_kwh": round(cost_rate, 3) if cost_rate is not None else None,
        "co2_factor_kg_kwh": gf.emission_factor_kg_kwh,
        "co2_factor_year": gf.year,
        "co2_factor_confidence": gf.confidence,
        "co2_factor_source": gf.source,
        "floor_area_m2": area,
    }
