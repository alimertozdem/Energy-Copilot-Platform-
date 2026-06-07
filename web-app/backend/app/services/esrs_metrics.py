"""ESRS-E1-aligned compliance metrics service.

Reads GHG from gold_ghg_scope (tCO2e, monthly per building per scope) and energy
from gold_kpi_daily, scoped to the user's visible buildings, and shapes them into
the EsrsReport model.

ESRS-E1-aligned SUPPORT — indicative, not an audited disclosure. Scope 3 is an
estimate; Scope 2 is reported both location- and market-based (ESRS E1-6).
Reporting period = the latest reporting_year present in gold_ghg_scope (annual).
"""
from typing import Any

from app.integrations import fabric_sql
from app.schemas.esrs import (
    EsrsBuildingRow,
    EsrsDataQuality,
    EsrsReport,
    EsrsScopeBreakdown,
)

KWH_TO_MWH = 1 / 1000


def _safe_float(v: Any) -> float:
    return float(v) if v is not None else 0.0


def _zero_scopes() -> EsrsScopeBreakdown:
    return EsrsScopeBreakdown(
        scope1_tco2e=0.0,
        scope2_location_tco2e=0.0,
        scope2_market_tco2e=0.0,
        scope3_tco2e=0.0,
        total_location_tco2e=0.0,
        total_market_tco2e=0.0,
    )


def _empty_report(buildings_total: int) -> EsrsReport:
    return EsrsReport(
        reporting_year=None,
        has_data=False,
        buildings_total=buildings_total,
        buildings_reported=0,
        floor_area_m2=0.0,
        energy_total_mwh=0.0,
        energy_renewable_pct=None,
        ghg=_zero_scopes(),
        ghg_intensity_tco2e_m2=None,
        data_quality=EsrsDataQuality(),
        rows=[],
    )


def get_esrs_report(building_ids: list[str]) -> EsrsReport:
    """Energy + Scope 1/2/3 GHG summary for the visible portfolio's latest year."""
    if not building_ids:
        return _empty_report(0)

    ph, ids_params = fabric_sql.format_in_clause(building_ids)

    # Reporting period = latest year present for any visible building.
    year_val = fabric_sql.execute_scalar(
        f"SELECT MAX(reporting_year) FROM [dbo].[gold_ghg_scope] "
        f"WHERE building_id IN ({ph})",
        ids_params,
    )
    if year_val is None:
        return _empty_report(len(building_ids))
    year = int(year_val)

    # Per-building GHG totals for that year (worst monthly data-quality flag wins).
    rows_sql = f"""
    SELECT
        b.building_id,
        b.building_name,
        b.building_type,
        b.gross_floor_area_m2,
        g.scope1_tco2,
        g.scope2_location_tco2,
        g.scope2_market_tco2,
        g.scope3_tco2,
        g.total_location_tco2,
        g.total_market_tco2,
        g.dq_flag
    FROM [dbo].[silver_building_master] b
    INNER JOIN (
        SELECT
            building_id,
            SUM(scope1_total_tco2)       AS scope1_tco2,
            SUM(scope2_location_tco2)    AS scope2_location_tco2,
            SUM(scope2_market_tco2)      AS scope2_market_tco2,
            SUM(scope3_estimated_tco2)   AS scope3_tco2,
            SUM(total_ghg_location_tco2) AS total_location_tco2,
            SUM(total_ghg_market_tco2)   AS total_market_tco2,
            MAX(data_quality_flag)       AS dq_flag
        FROM [dbo].[gold_ghg_scope]
        WHERE building_id IN ({ph}) AND reporting_year = ?
        GROUP BY building_id
    ) g ON g.building_id = b.building_id
    WHERE b.building_id IN ({ph})
    ORDER BY g.total_location_tco2 DESC
    """
    rows_params = (*ids_params, year, *ids_params)
    rows = fabric_sql.execute_query(rows_sql, rows_params)

    # Portfolio energy for the same calendar year.
    energy_rows = fabric_sql.execute_query(
        f"""
        SELECT
            SUM(total_consumption_kwh)   AS kwh,
            SUM(solar_self_consumed_kwh) AS solar_self
        FROM [dbo].[gold_kpi_daily]
        WHERE building_id IN ({ph}) AND YEAR([date]) = ?
        """,
        (*ids_params, year),
    )
    e = energy_rows[0] if energy_rows else {}
    total_kwh = _safe_float(e.get("kwh"))
    solar_self = _safe_float(e.get("solar_self"))
    energy_mwh = total_kwh * KWH_TO_MWH
    renewable_pct = (solar_self / total_kwh * 100) if total_kwh > 0 else None

    # Per-building rows + portfolio roll-up + data-quality counts.
    out_rows: list[EsrsBuildingRow] = []
    s1 = s2l = s2m = s3 = tl = tm = 0.0
    area_reported = 0.0
    dq = {"complete": 0, "estimated": 0, "missing_gas": 0, "other": 0}

    for r in rows:
        area = _safe_float(r.get("gross_floor_area_m2"))
        rs1 = _safe_float(r.get("scope1_tco2"))
        rs2l = _safe_float(r.get("scope2_location_tco2"))
        rs2m = _safe_float(r.get("scope2_market_tco2"))
        rs3 = _safe_float(r.get("scope3_tco2"))
        rtl = _safe_float(r.get("total_location_tco2"))
        rtm = _safe_float(r.get("total_market_tco2"))
        flag = r.get("dq_flag")

        s1 += rs1
        s2l += rs2l
        s2m += rs2m
        s3 += rs3
        tl += rtl
        tm += rtm
        area_reported += area
        if flag in dq:
            dq[flag] += 1
        else:
            dq["other"] += 1

        out_rows.append(
            EsrsBuildingRow(
                fabric_building_id=r["building_id"],
                name=r.get("building_name") or "",
                building_type=r.get("building_type") or "",
                floor_area_m2=area,
                scope1_tco2e=rs1,
                scope2_location_tco2e=rs2l,
                scope2_market_tco2e=rs2m,
                scope3_tco2e=rs3,
                total_location_tco2e=rtl,
                ghg_intensity_tco2e_m2=(rtl / area) if area > 0 else None,
                data_quality_flag=flag,
            )
        )

    intensity = (tl / area_reported) if area_reported > 0 else None

    return EsrsReport(
        reporting_year=year,
        has_data=len(out_rows) > 0,
        buildings_total=len(building_ids),
        buildings_reported=len(out_rows),
        floor_area_m2=area_reported,
        energy_total_mwh=energy_mwh,
        energy_renewable_pct=renewable_pct,
        ghg=EsrsScopeBreakdown(
            scope1_tco2e=s1,
            scope2_location_tco2e=s2l,
            scope2_market_tco2e=s2m,
            scope3_tco2e=s3,
            total_location_tco2e=tl,
            total_market_tco2e=tm,
        ),
        ghg_intensity_tco2e_m2=intensity,
        data_quality=EsrsDataQuality(**dq),
        rows=out_rows,
    )
