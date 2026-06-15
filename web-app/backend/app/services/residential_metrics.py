"""Residential resident-view metrics service.

Reads the residential Gold tables and shapes them into the /residence response.
Mirrors ``portfolio_metrics``: parameterized reads against the Fabric SQL Analytics
Endpoint (``app/integrations/fabric_sql.py``), ``[dbo]`` schema, ``IN (...)`` filter.

Privacy by construction: every query filters ``WHERE unit_id IN (the resident's own
units)``. The anonymized building benchmark is already pre-aggregated INTO each
unit's own Gold row (``building_avg_*`` + ``vs_building_pct``), so the resident view
never reads another named unit -- no cross-unit join, no leakage.

Source tables (created by ``notebooks/gold/30_residential_gold.py``):
  * gold_residential_unit_kpi      -- per-unit EUI, EPC band, building benchmark
  * gold_residential_common_split  -- HKVO 70/30 common-area allocation
  * gold_residential_uvi_monthly   -- monthly heating/DHW kWh+cost (UVI feed)
"""
from datetime import date
from typing import Any

from app.integrations import fabric_sql
from app.integrations import gold_read
from app.schemas.residence import (
    ResidenceCommonArea,
    ResidenceKpi,
    ResidenceMonthlyPoint,
    ResidenceSummary,
    ResidenceUnit,
)


def _f(v: Any) -> float | None:
    """Pass numeric values through; keep NULL as None (don't fabricate zeros)."""
    return float(v) if v is not None else None


def _i(v: Any) -> int | None:
    return int(v) if v is not None else None


def _read_unit_kpi(unit_ids: list[str]) -> dict[str, dict]:
    ph, params = fabric_sql.format_in_clause(unit_ids)
    sql = f"""
    SELECT unit_id, building_id, is_heated, area_m2,
           coverage_start, coverage_end, cov_days,
           heating_dhw_kwh_annual, eui_kwh_m2_yr,
           climate_adjustment_factor, eui_climate_adjusted_kwh_m2_yr,
           epc_band, building_avg_eui_kwh_m2_yr, vs_building_pct
    FROM [dbo].[gold_residential_unit_kpi]
    WHERE unit_id IN ({ph})
    """
    return {r["unit_id"]: r for r in gold_read.query(sql, params)}


def _read_common_split(unit_ids: list[str]) -> dict[str, dict]:
    ph, params = fabric_sql.format_in_clause(unit_ids)
    sql = f"""
    SELECT unit_id, building_id, coverage_start, coverage_end,
           unit_metered_kwh, area_m2, cons_weight, area_weight,
           cons_share, area_share, allocation_share,
           building_total_kwh, unit_allocated_kwh
    FROM [dbo].[gold_residential_common_split]
    WHERE unit_id IN ({ph})
    """
    return {r["unit_id"]: r for r in gold_read.query(sql, params)}


def _read_uvi_monthly(unit_ids: list[str]) -> dict[str, list[dict]]:
    ph, params = fabric_sql.format_in_clause(unit_ids)
    sql = f"""
    SELECT unit_id, [year], [month], energy_type,
           kwh, cost_eur, building_avg_kwh, vs_building_pct
    FROM [dbo].[gold_residential_uvi_monthly]
    WHERE unit_id IN ({ph})
    ORDER BY unit_id, [year], [month], energy_type
    """
    grouped: dict[str, list[dict]] = {}
    for r in gold_read.query(sql, params):
        grouped.setdefault(r["unit_id"], []).append(r)
    return grouped


def _to_kpi(r: dict) -> ResidenceKpi:
    return ResidenceKpi(
        eui_kwh_m2_yr=_f(r.get("eui_kwh_m2_yr")),
        eui_climate_adjusted_kwh_m2_yr=_f(r.get("eui_climate_adjusted_kwh_m2_yr")),
        climate_adjustment_factor=_f(r.get("climate_adjustment_factor")),
        epc_band=r.get("epc_band"),
        heating_dhw_kwh_annual=_f(r.get("heating_dhw_kwh_annual")),
        building_avg_eui_kwh_m2_yr=_f(r.get("building_avg_eui_kwh_m2_yr")),
        vs_building_pct=_f(r.get("vs_building_pct")),
        coverage_start=r.get("coverage_start"),
        coverage_end=r.get("coverage_end"),
        cov_days=_i(r.get("cov_days")),
    )


def _to_common(r: dict) -> ResidenceCommonArea:
    return ResidenceCommonArea(
        unit_metered_kwh=_f(r.get("unit_metered_kwh")),
        unit_allocated_kwh=_f(r.get("unit_allocated_kwh")),
        allocation_share=_f(r.get("allocation_share")),
        cons_weight=_f(r.get("cons_weight")),
        area_weight=_f(r.get("area_weight")),
        cons_share=_f(r.get("cons_share")),
        area_share=_f(r.get("area_share")),
        building_total_kwh=_f(r.get("building_total_kwh")),
        coverage_start=r.get("coverage_start"),
        coverage_end=r.get("coverage_end"),
    )


def _to_monthly(r: dict) -> ResidenceMonthlyPoint:
    return ResidenceMonthlyPoint(
        year=int(r["year"]),
        month=int(r["month"]),
        energy_type=r.get("energy_type") or "",
        kwh=_f(r.get("kwh")),
        cost_eur=_f(r.get("cost_eur")),
        building_avg_kwh=_f(r.get("building_avg_kwh")),
        vs_building_pct=_f(r.get("vs_building_pct")),
    )


def get_residence_summary(unit_ids: list[str], as_of: date) -> ResidenceSummary:
    """Build the resident summary for the unit set ``resolve_resident_scope`` returned.

    ``unit_ids`` is the authoritative, tenancy-window-filtered set. A unit with no
    Gold rows yet still appears, with null metrics (honest "no data" rather than a
    fabricated zero).
    """
    if not unit_ids:
        return ResidenceSummary(as_of=as_of, units=[])

    kpi_rows = _read_unit_kpi(unit_ids)
    common_rows = _read_common_split(unit_ids)
    monthly_rows = _read_uvi_monthly(unit_ids)

    units: list[ResidenceUnit] = []
    for uid in unit_ids:
        k = kpi_rows.get(uid)
        c = common_rows.get(uid)
        ms = monthly_rows.get(uid, [])

        # Unit attributes live on the Gold rows; prefer the KPI row, fall back to split.
        attr_src = k or c or {}
        is_heated_raw = (k or {}).get("is_heated")
        units.append(
            ResidenceUnit(
                unit_id=uid,
                area_m2=_f(attr_src.get("area_m2")),
                is_heated=bool(is_heated_raw) if is_heated_raw is not None else None,
                kpi=_to_kpi(k) if k else None,
                common_area=_to_common(c) if c else None,
                monthly=[_to_monthly(m) for m in ms],
            )
        )
    return ResidenceSummary(as_of=as_of, units=units)
