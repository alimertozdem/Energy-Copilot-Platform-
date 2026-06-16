"""Solar detail service (Solar initiative C) -- daily series + summary for /solar.

REAL-first, SAMPLE-fallback (per building):
  * gold_solar_daily  = REAL telemetry-derived KPIs (Phase A loader, Postgres-only).
  * gold_kpi_daily/mv_kpi_daily = SYNTHETIC sample KPIs (the seed portfolio).
A building that has any telemetry in the window is served from gold_solar_daily
(only its telemetry days); every other building falls back to the synthetic mv_.
The response carries data_basis + real_building_count so the UI can label it
honestly.

Energy-logic notes:
  * Performance ratio is GENERATION-WEIGHTED across buildings (sum(pr*gen)/sum(gen)).
    Sample PR excludes PR>PR_SANE_MAX building-days (low-sun artifact); real PR is
    already clamped at source (PR_MAX_PLAUSIBLE in the loader / gold engine).
  * self_consumed / exported come ONLY from buildings that report them (sample, or
    real buildings with a load meter). Inverter-only telemetry cannot split
    generation into on-site use vs export, so the self-consumption rate is computed
    over the METERED generation and self_consumption_coverage_pct says how much of
    total generation that covers. Never estimated.
  * Specific yield is annualized ONLY over a ~full-year window; shorter windows are
    reported as-is (annualizing a season misrepresents the year).
"""
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.integrations import fabric_sql
from app.integrations import gold_read
from app.schemas.solar import SolarDetailResponse, SolarSeriesPoint, SolarSummary

WINDOW_DAYS = 90
ANNUALIZE_MIN_DAYS = 350
PR_SANE_MAX = 1.1


def _f(v: Any) -> float:
    return float(v) if v is not None else 0.0


def _real_anchor(db: Session, building_ids: list[str]):
    """Latest telemetry date (gold_solar_daily). None if table absent / no rows."""
    try:
        from app.db.models.gold_solar_daily import GoldSolarDaily as G

        return db.execute(
            select(func.max(G.date)).where(G.building_id.in_(building_ids))
        ).scalar()
    except Exception:
        db.rollback()
        return None


def _query_real(db: Session, building_ids: list[str], start, anchor) -> list[dict]:
    """Telemetry rows in the window. [] if the table doesn't exist yet (pre-migration)."""
    try:
        from app.db.models.gold_solar_daily import GoldSolarDaily as G

        rows = db.execute(
            select(G.building_id, G.date, G.solar_generated_kwh, G.avg_solar_pr,
                   G.solar_self_consumed_kwh, G.solar_exported_kwh, G.data_source)
            .where(G.building_id.in_(building_ids))
            .where(G.date >= start)
            .where(G.date <= anchor)
        ).all()
        return [
            {"building_id": r[0], "date": r[1], "gen": _f(r[2]), "pr": r[3],
             "self": r[4], "exp": r[5], "ds": r[6]}
            for r in rows
        ]
    except Exception:
        db.rollback()
        return []


def get_solar_detail(building_ids: list[str], db: Session) -> SolarDetailResponse:
    """Daily portfolio solar series + summary over the last WINDOW_DAYS, real-first."""
    empty = SolarDetailResponse(has_data=False, series=[], summary=None)
    if not building_ids:
        return empty

    ph, params = fabric_sql.format_in_clause(building_ids)

    sample_anchor = gold_read.scalar(
        f"SELECT MAX([date]) FROM [dbo].[gold_kpi_daily] WHERE building_id IN ({ph})",
        params,
    )
    real_anchor = _real_anchor(db, building_ids)
    candidates = [d for d in (sample_anchor, real_anchor) if d is not None]
    if not candidates:
        return empty
    anchor = max(candidates)
    start = anchor - timedelta(days=WINDOW_DAYS - 1)

    real_rows = _query_real(db, building_ids, start, anchor)
    real_bids = {r["building_id"] for r in real_rows if r["gen"] > 0}
    sample_bids = [b for b in building_ids if b not in real_bids]

    # date -> accumulators
    acc: dict[Any, dict] = {}

    def slot(d):
        return acc.setdefault(
            d, {"gen": 0.0, "self": 0.0, "exp": 0.0, "pr_num": 0.0, "pr_den": 0.0,
                "gen_self": 0.0}
        )

    # provenance per building: 'telemetry' (live device) vs 'simulated' (demo feed)
    ds_by_bid = {r["building_id"]: (r.get("ds") or "telemetry") for r in real_rows}
    live_gen_total = 0.0
    sim_gen_total = 0.0
    for r in real_rows:
        if r["building_id"] not in real_bids:
            continue
        g = r["gen"]
        s = slot(r["date"])
        s["gen"] += g
        if ds_by_bid.get(r["building_id"]) == "simulated":
            sim_gen_total += g
        else:
            live_gen_total += g
        if r["pr"] is not None and g > 0:
            s["pr_num"] += float(r["pr"]) * g
            s["pr_den"] += g
        # self/exp only when a load meter produced them (else stays unmetered)
        if r.get("self") is not None:
            s["self"] += _f(r["self"])
            s["exp"] += _f(r["exp"])
            s["gen_self"] += g
    live_bids = {b for b in real_bids if ds_by_bid.get(b) != "simulated"}
    sim_bids = {b for b in real_bids if ds_by_bid.get(b) == "simulated"}

    sample_gen_total = 0.0
    if sample_bids:
        sph, sparams = fabric_sql.format_in_clause(sample_bids)
        series_sql = f"""
        SELECT [date] AS d,
            SUM(solar_generated_kwh)     AS gen,
            SUM(solar_self_consumed_kwh) AS self_c,
            SUM(solar_exported_kwh)      AS exp_c,
            SUM(CASE WHEN avg_solar_pr <= {PR_SANE_MAX} THEN avg_solar_pr * solar_generated_kwh ELSE 0 END) AS pr_num,
            SUM(CASE WHEN avg_solar_pr <= {PR_SANE_MAX} THEN solar_generated_kwh ELSE 0 END)                AS pr_den
        FROM [dbo].[gold_kpi_daily]
        WHERE building_id IN ({sph}) AND [date] BETWEEN ? AND ?
        GROUP BY [date]
        ORDER BY [date]
        """
        for row in gold_read.query(series_sql, (*sparams, start, anchor)):
            g = _f(row.get("gen"))
            s = slot(row["d"])
            s["gen"] += g
            s["self"] += _f(row.get("self_c"))
            s["exp"] += _f(row.get("exp_c"))
            s["pr_num"] += _f(row.get("pr_num"))
            s["pr_den"] += _f(row.get("pr_den"))
            s["gen_self"] += g  # sample buildings report self/exp
            sample_gen_total += g

    if not acc:
        return empty

    series = [
        SolarSeriesPoint(
            date=d,
            generated_kwh=acc[d]["gen"],
            self_consumed_kwh=acc[d]["self"],
            exported_kwh=acc[d]["exp"],
            performance_ratio=(
                acc[d]["pr_num"] / acc[d]["pr_den"] if acc[d]["pr_den"] > 0 else None
            ),
        )
        for d in sorted(acc)
    ]

    total_gen = sum(s["gen"] for s in acc.values())
    if total_gen <= 0:
        return empty
    total_self = sum(s["self"] for s in acc.values())
    total_exp = sum(s["exp"] for s in acc.values())
    gen_with_self = sum(s["gen_self"] for s in acc.values())
    pr_num = sum(s["pr_num"] for s in acc.values())
    pr_den = sum(s["pr_den"] for s in acc.values())
    days = len(acc) or 1
    avg_pr = (pr_num / pr_den) if pr_den > 0 else None

    cap = _f(
        gold_read.scalar(
            f"SELECT SUM(pv_capacity_kwp) FROM [dbo].[silver_building_master] "
            f"WHERE building_id IN ({ph}) AND has_pv = 1",
            params,
        )
    )
    annualized = days >= ANNUALIZE_MIN_DAYS
    if cap > 0:
        specific_yield = (total_gen / cap) * (365.25 / days) if annualized else (total_gen / cap)
    else:
        specific_yield = None

    self_available = gen_with_self > 0
    _present = [name for name, on in (("telemetry", live_gen_total > 0),
                                      ("simulated", sim_gen_total > 0),
                                      ("sample", sample_gen_total > 0)) if on]
    data_basis = "mixed" if len(_present) > 1 else (_present[0] if _present else "sample")

    summary = SolarSummary(
        total_generated_kwh=total_gen,
        total_self_consumed_kwh=total_self,
        total_exported_kwh=total_exp,
        avg_performance_ratio=avg_pr,
        self_consumption_rate=(total_self / gen_with_self * 100) if self_available else 0.0,
        self_consumption_available=self_available,
        self_consumption_coverage_pct=(gen_with_self / total_gen * 100) if total_gen > 0 else None,
        specific_yield_kwh_kwp=specific_yield,
        specific_yield_annualized=(specific_yield is not None and annualized),
        pv_capacity_kwp=cap,
        days=days,
        data_basis=data_basis,
        real_building_count=len(live_bids),
        simulated_building_count=len(sim_bids),
    )
    return SolarDetailResponse(has_data=True, series=series, summary=summary)
