"""Solar detail service (Solar initiative C) -- daily series + summary for /solar.

Reads gold_kpi_daily solar columns (already produced by 03_gold_kpi_engine):
solar_generated_kwh, solar_self_consumed_kwh, solar_exported_kwh,
solar_performance_ratio. Portfolio-summed per day over a rolling window.
"""
from datetime import date, timedelta
from typing import Any

from app.integrations import fabric_sql
from app.integrations import gold_read
from app.schemas.solar import SolarDetailResponse, SolarSeriesPoint, SolarSummary

WINDOW_DAYS = 90


def _f(v: Any) -> float:
    return float(v) if v is not None else 0.0


def get_solar_detail(building_ids: list[str]) -> SolarDetailResponse:
    """Daily portfolio solar series + summary over the last WINDOW_DAYS."""
    empty = SolarDetailResponse(has_data=False, series=[], summary=None)
    if not building_ids:
        return empty

    ph, params = fabric_sql.format_in_clause(building_ids)

    anchor = gold_read.scalar(
        f"SELECT MAX([date]) FROM [dbo].[gold_kpi_daily] WHERE building_id IN ({ph})",
        params,
    )
    if anchor is None:
        return empty

    start = anchor - timedelta(days=WINDOW_DAYS - 1)
    series_sql = f"""
    SELECT [date] AS d,
        SUM(solar_generated_kwh)     AS gen,
        SUM(solar_self_consumed_kwh) AS self_c,
        SUM(solar_exported_kwh)      AS exp_c,
        AVG(solar_performance_ratio) AS pr
    FROM [dbo].[gold_kpi_daily]
    WHERE building_id IN ({ph}) AND [date] BETWEEN ? AND ?
    GROUP BY [date]
    ORDER BY [date]
    """
    rows = gold_read.query(series_sql, (*params, start, anchor))

    series = [
        SolarSeriesPoint(
            date=r["d"],
            generated_kwh=_f(r.get("gen")),
            self_consumed_kwh=_f(r.get("self_c")),
            exported_kwh=_f(r.get("exp_c")),
            performance_ratio=(
                float(r["pr"]) if r.get("pr") is not None else None
            ),
        )
        for r in rows
    ]

    total_gen = sum(p.generated_kwh for p in series)
    if total_gen <= 0:
        return empty

    total_self = sum(p.self_consumed_kwh for p in series)
    total_exp = sum(p.exported_kwh for p in series)
    prs = [p.performance_ratio for p in series if p.performance_ratio is not None]
    avg_pr = (sum(prs) / len(prs)) if prs else None
    days = len(series) or 1

    cap = _f(
        gold_read.scalar(
            f"SELECT SUM(pv_capacity_kwp) FROM [dbo].[silver_building_master] "
            f"WHERE building_id IN ({ph}) AND has_pv = 1",
            params,
        )
    )
    # Annualized specific yield = (generated / installed kWp) scaled to a year.
    specific_yield = (
        (total_gen / cap) * (365.25 / days) if cap > 0 else None
    )

    summary = SolarSummary(
        total_generated_kwh=total_gen,
        total_self_consumed_kwh=total_self,
        total_exported_kwh=total_exp,
        avg_performance_ratio=avg_pr,
        self_consumption_rate=(total_self / total_gen * 100) if total_gen > 0 else 0.0,
        specific_yield_kwh_kwp=specific_yield,
        pv_capacity_kwp=cap,
        days=days,
    )
    return SolarDetailResponse(has_data=True, series=series, summary=summary)
