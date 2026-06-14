"""
Portfolio metrics service.

Reads Fabric Lakehouse tables (silver_building_master, gold_kpi_daily,
gold_anomaly_log, gold_recommendations, gold_iot_daily_summary) and shapes
the data into the Pydantic response models used by /portfolio endpoints.

Solar (Solar initiative A): gold_kpi_daily already carries solar_generated_kwh,
solar_self_consumed_kwh, solar_exported_kwh, co2_savings_from_solar_kg. We
surface them as an optional SolarKPIs block, null when the portfolio has no PV.
"""

from datetime import date, timedelta
from typing import Any

from app.integrations import fabric_sql
from app.schemas.portfolio import (
    KPITile,
    PortfolioBuildingRow,
    PortfolioBuildingsResponse,
    PortfolioKPIs,
    PortfolioPeriod,
    SolarKPIs,
)

# Annualization factor for daily -> yearly EUI conversion.
ANNUALIZE_FACTOR = 365.25 / 30


def _get_anchor_date(building_ids: list[str]) -> date | None:
    """Latest date with KPI data for any visible building (anchors the window)."""
    if not building_ids:
        return None
    ph, params = fabric_sql.format_in_clause(building_ids)
    sql = (
        f"SELECT MAX([date]) AS max_date "
        f"FROM [dbo].[gold_kpi_daily] "
        f"WHERE building_id IN ({ph})"
    )
    return fabric_sql.execute_scalar(sql, params)


def _delta_pct(current: float, prior: float) -> float | None:
    """Percent change vs prior period. Returns None when prior is zero."""
    if prior == 0:
        return None
    return ((current - prior) / prior) * 100


def _direction(delta: float | None) -> str:
    """Sign of the delta (physical hint), not a value judgement."""
    if delta is None:
        return "neutral"
    if delta > 0.5:
        return "up"
    if delta < -0.5:
        return "down"
    return "neutral"


def _safe_float(v: Any) -> float:
    """Treat None / NULL as 0.0 in numeric aggregations."""
    return float(v) if v is not None else 0.0


def get_portfolio_kpis(building_ids: list[str]) -> PortfolioKPIs:
    """4 headline KPI tiles (+ optional solar block) + delta vs prior 30 days."""
    anchor = _get_anchor_date(building_ids)
    if anchor is None:
        today = date.today()
        return PortfolioKPIs(
            period=PortfolioPeriod(
                start_date=today - timedelta(days=29), end_date=today, days=30
            ),
            total_energy=KPITile(value=0.0, unit="kWh", delta_pct=None, direction="neutral"),
            avg_eui=KPITile(value=0.0, unit="kWh/m2/yr", delta_pct=None, direction="neutral"),
            total_cost=KPITile(value=0.0, unit="EUR", delta_pct=None, direction="neutral"),
            total_co2=KPITile(value=0.0, unit="kg CO2e", delta_pct=None, direction="neutral"),
            solar=None,
        )

    cur_start = anchor - timedelta(days=29)
    cur_end = anchor
    prev_start = anchor - timedelta(days=59)
    prev_end = anchor - timedelta(days=30)

    ph, ids_params = fabric_sql.format_in_clause(building_ids)
    sql = f"""
    WITH cur AS (
        SELECT
            SUM(total_consumption_kwh)     AS kwh,
            SUM(estimated_cost_eur)        AS cost,
            SUM(co2_emissions_kg)          AS co2,
            SUM(solar_generated_kwh)       AS solar_gen,
            SUM(solar_self_consumed_kwh)   AS solar_self,
            SUM(solar_exported_kwh)        AS solar_exp,
            SUM(co2_savings_from_solar_kg) AS solar_co2
        FROM [dbo].[gold_kpi_daily]
        WHERE building_id IN ({ph}) AND [date] BETWEEN ? AND ?
    ),
    prev AS (
        SELECT
            SUM(total_consumption_kwh)     AS kwh,
            SUM(estimated_cost_eur)        AS cost,
            SUM(co2_emissions_kg)          AS co2,
            SUM(solar_generated_kwh)       AS solar_gen,
            SUM(solar_self_consumed_kwh)   AS solar_self,
            SUM(solar_exported_kwh)        AS solar_exp,
            SUM(co2_savings_from_solar_kg) AS solar_co2
        FROM [dbo].[gold_kpi_daily]
        WHERE building_id IN ({ph}) AND [date] BETWEEN ? AND ?
    ),
    area AS (
        SELECT SUM(gross_floor_area_m2) AS total_area
        FROM [dbo].[silver_building_master]
        WHERE building_id IN ({ph})
    )
    SELECT
        cur.kwh  AS cur_kwh,  cur.cost  AS cur_cost,  cur.co2  AS cur_co2,
        cur.solar_gen  AS cur_solar_gen,  cur.solar_self AS cur_solar_self,
        cur.solar_exp  AS cur_solar_exp,  cur.solar_co2  AS cur_solar_co2,
        prev.kwh AS prev_kwh, prev.cost AS prev_cost, prev.co2 AS prev_co2,
        prev.solar_gen AS prev_solar_gen, prev.solar_self AS prev_solar_self,
        prev.solar_exp AS prev_solar_exp, prev.solar_co2 AS prev_solar_co2,
        area.total_area AS total_area
    FROM cur CROSS JOIN prev CROSS JOIN area
    """
    params = (
        *ids_params, cur_start, cur_end,
        *ids_params, prev_start, prev_end,
        *ids_params,
    )
    rows = fabric_sql.execute_query(sql, params)
    row = rows[0] if rows else {}

    cur_kwh = _safe_float(row.get("cur_kwh"))
    cur_cost = _safe_float(row.get("cur_cost"))
    cur_co2 = _safe_float(row.get("cur_co2"))
    prev_kwh = _safe_float(row.get("prev_kwh"))
    prev_cost = _safe_float(row.get("prev_cost"))
    prev_co2 = _safe_float(row.get("prev_co2"))
    total_area = _safe_float(row.get("total_area"))

    cur_solar_gen = _safe_float(row.get("cur_solar_gen"))
    cur_solar_self = _safe_float(row.get("cur_solar_self"))
    cur_solar_exp = _safe_float(row.get("cur_solar_exp"))
    cur_solar_co2 = _safe_float(row.get("cur_solar_co2"))
    prev_solar_gen = _safe_float(row.get("prev_solar_gen"))
    prev_solar_self = _safe_float(row.get("prev_solar_self"))
    prev_solar_exp = _safe_float(row.get("prev_solar_exp"))
    prev_solar_co2 = _safe_float(row.get("prev_solar_co2"))

    if total_area > 0:
        cur_eui = (cur_kwh * ANNUALIZE_FACTOR) / total_area
        prev_eui = (prev_kwh * ANNUALIZE_FACTOR) / total_area
    else:
        cur_eui = 0.0
        prev_eui = 0.0

    kwh_delta = _delta_pct(cur_kwh, prev_kwh)
    eui_delta = _delta_pct(cur_eui, prev_eui)
    cost_delta = _delta_pct(cur_cost, prev_cost)
    co2_delta = _delta_pct(cur_co2, prev_co2)

    solar = None
    if cur_solar_gen > 0 or prev_solar_gen > 0:
        cur_renew = (cur_solar_self / cur_kwh * 100) if cur_kwh > 0 else 0.0
        prev_renew = (prev_solar_self / prev_kwh * 100) if prev_kwh > 0 else 0.0
        gen_delta = _delta_pct(cur_solar_gen, prev_solar_gen)
        renew_delta = _delta_pct(cur_renew, prev_renew)
        exp_delta = _delta_pct(cur_solar_exp, prev_solar_exp)
        sco2_delta = _delta_pct(cur_solar_co2, prev_solar_co2)
        solar = SolarKPIs(
            generated=KPITile(value=cur_solar_gen, unit="kWh", delta_pct=gen_delta, direction=_direction(gen_delta)),
            renewable_rate=KPITile(value=cur_renew, unit="%", delta_pct=renew_delta, direction=_direction(renew_delta)),
            exported=KPITile(value=cur_solar_exp, unit="kWh", delta_pct=exp_delta, direction=_direction(exp_delta)),
            co2_avoided=KPITile(value=cur_solar_co2, unit="kg CO2e", delta_pct=sco2_delta, direction=_direction(sco2_delta)),
        )

    return PortfolioKPIs(
        period=PortfolioPeriod(start_date=cur_start, end_date=cur_end, days=30),
        total_energy=KPITile(value=cur_kwh, unit="kWh", delta_pct=kwh_delta, direction=_direction(kwh_delta)),
        avg_eui=KPITile(value=cur_eui, unit="kWh/m2/yr", delta_pct=eui_delta, direction=_direction(eui_delta)),
        total_cost=KPITile(value=cur_cost, unit="EUR", delta_pct=cost_delta, direction=_direction(cost_delta)),
        total_co2=KPITile(value=cur_co2, unit="kg CO2e", delta_pct=co2_delta, direction=_direction(co2_delta)),
        solar=solar,
    )


def get_portfolio_buildings(building_ids: list[str]) -> PortfolioBuildingsResponse:
    """One row per visible building with 30-day aggregates + module flags."""
    if not building_ids:
        return PortfolioBuildingsResponse(buildings=[])

    anchor = _get_anchor_date(building_ids)
    if anchor is None:
        return _buildings_without_kpi(building_ids)

    start_date = anchor - timedelta(days=29)
    end_date = anchor

    ph, ids_params = fabric_sql.format_in_clause(building_ids)

    sql = f"""
    SELECT
        b.building_id,
        b.building_name,
        b.city,
        b.country_code,
        b.building_type,
        b.gross_floor_area_m2,
        b.energy_certificate,
        b.has_pv,
        b.has_battery,
        b.subscription_tier,
        ISNULL(k.kwh_30d,  0) AS kwh_30d,
        ISNULL(k.cost_30d, 0) AS cost_30d,
        ISNULL(k.co2_30d,  0) AS co2_30d,
        ISNULL(a.open_anom, 0) AS open_anomalies,
        ISNULL(r.rec_count, 0) AS open_recommendations,
        CASE WHEN i.building_id IS NOT NULL THEN CAST(1 AS bit) ELSE CAST(0 AS bit) END AS has_iot
    FROM [dbo].[silver_building_master] b
    LEFT JOIN (
        SELECT
            building_id,
            SUM(total_consumption_kwh) AS kwh_30d,
            SUM(estimated_cost_eur)    AS cost_30d,
            SUM(co2_emissions_kg)      AS co2_30d
        FROM [dbo].[gold_kpi_daily]
        WHERE building_id IN ({ph}) AND [date] BETWEEN ? AND ?
        GROUP BY building_id
    ) k ON k.building_id = b.building_id
    LEFT JOIN (
        -- Distinct OPEN issue types, not raw daily events: gold_anomaly_log keys
        -- by (building, type, DATE), so a chronic fault would otherwise count as
        -- hundreds. COUNT(DISTINCT anomaly_type) gives the calm "N issues need
        -- attention" number that matches the grouped /alerts view.
        SELECT building_id, COUNT(DISTINCT anomaly_type) AS open_anom
        FROM [dbo].[gold_anomaly_log]
        WHERE building_id IN ({ph})
          AND is_resolved = 0
          AND severity IN ('HIGH', 'CRITICAL')
        GROUP BY building_id
    ) a ON a.building_id = b.building_id
    LEFT JOIN (
        SELECT building_id, COUNT(*) AS rec_count
        FROM [dbo].[gold_recommendations]
        WHERE building_id IN ({ph})
        GROUP BY building_id
    ) r ON r.building_id = b.building_id
    LEFT JOIN (
        SELECT DISTINCT building_id
        FROM [dbo].[gold_iot_daily_summary]
        WHERE building_id IN ({ph})
    ) i ON i.building_id = b.building_id
    WHERE b.building_id IN ({ph})
    ORDER BY ISNULL(k.kwh_30d, 0) DESC
    """

    params = (
        *ids_params, start_date, end_date,
        *ids_params,
        *ids_params,
        *ids_params,
        *ids_params,
    )

    rows = fabric_sql.execute_query(sql, params)
    return PortfolioBuildingsResponse(buildings=[_row_to_building(r) for r in rows])


def _row_to_building(r: dict) -> PortfolioBuildingRow:
    """Map a SQL row dict to the Pydantic response model."""
    area = _safe_float(r.get("gross_floor_area_m2"))
    kwh = _safe_float(r.get("kwh_30d"))
    eui = (kwh * ANNUALIZE_FACTOR) / area if area > 0 else None

    return PortfolioBuildingRow(
        fabric_building_id=r["building_id"],
        name=r["building_name"] or "",
        city=r["city"] or "",
        country=r["country_code"] or "",
        building_type=r["building_type"] or "",
        floor_area_m2=area,
        epc_class=r.get("energy_certificate"),
        kwh_30d=kwh,
        cost_30d_eur=_safe_float(r.get("cost_30d")),
        co2_30d_kg=_safe_float(r.get("co2_30d")),
        eui_kwh_m2_yr=eui,
        open_anomalies=int(r.get("open_anomalies") or 0),
        open_recommendations=int(r.get("open_recommendations") or 0),
        has_pv=bool(r.get("has_pv")),
        has_battery=bool(r.get("has_battery")),
        has_iot=bool(r.get("has_iot")),
        subscription_tier=r.get("subscription_tier") or "Monitor",
    )


def _buildings_without_kpi(building_ids: list[str]) -> PortfolioBuildingsResponse:
    """Fallback when buildings exist but gold_kpi_daily has no rows."""
    ph, ids_params = fabric_sql.format_in_clause(building_ids)
    sql = f"""
    SELECT
        b.building_id, b.building_name, b.city, b.country_code, b.building_type,
        b.gross_floor_area_m2, b.energy_certificate, b.has_pv, b.has_battery,
        b.subscription_tier
    FROM [dbo].[silver_building_master] b
    WHERE b.building_id IN ({ph})
    """
    rows = fabric_sql.execute_query(sql, ids_params)
    buildings = [
        PortfolioBuildingRow(
            fabric_building_id=r["building_id"],
            name=r["building_name"] or "",
            city=r["city"] or "",
            country=r["country_code"] or "",
            building_type=r["building_type"] or "",
            floor_area_m2=_safe_float(r.get("gross_floor_area_m2")),
            epc_class=r.get("energy_certificate"),
            kwh_30d=0.0,
            cost_30d_eur=0.0,
            co2_30d_kg=0.0,
            eui_kwh_m2_yr=None,
            open_anomalies=0,
            open_recommendations=0,
            has_pv=bool(r.get("has_pv")),
            has_battery=bool(r.get("has_battery")),
            has_iot=False,
            subscription_tier=r.get("subscription_tier") or "Monitor",
        )
        for r in rows
    ]
    return PortfolioBuildingsResponse(buildings=buildings)
