"""Copilot tool definitions + handlers.

Six tools the LLM can invoke to answer user questions about their
portfolio. Each tool has:
    1. An Anthropic-compatible ToolDefinition (name + description +
       input_schema in JSON Schema form).
    2. A handler function that runs the actual work and returns a JSON-
       serializable dict for the tool_result block.

Authorization:
    Every handler that accepts a building_id MUST check it against
    ctx.visible_building_ids first. Otherwise the LLM could hallucinate
    "B999" and the SQL would happily query it (and reveal "no data" —
    which is itself an enumeration leak).

Schema notes:
    Fabric tables live in [dbo] schema. UPPERCASE severity values in
    gold_anomaly_log (Day 15 finding). gold_recommendations has no
    status column — V1 treats every row as "open"; status overlay lives
    in Postgres recommendation_status (see update_action_status below).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select

from app.db.models.recommendation import RecommendationStatus
from app.db.models.building import Building
from app.integrations import fabric_sql
from app.services.llm import ToolDefinition

# =====================================================================
# Shared helpers
# =====================================================================

ANNUALIZE_FACTOR = 365.25 / 30


def _safe_float(v: Any) -> float:
    """Treat None / NULL as 0.0 in numeric aggregations."""
    return float(v) if v is not None else 0.0


def _delta_pct(current: float, prior: float) -> float | None:
    """Percent change vs prior period. None when prior is zero."""
    if prior == 0:
        return None
    return ((current - prior) / prior) * 100


def _json_safe(value: Any) -> Any:
    """Coerce SQL types (Decimal, date, datetime, UUID) to JSON-safe values.

    The tool_result content sent to Anthropic must be JSON-serializable.
    pyodbc / SQLAlchemy hand us Decimal and date objects that json.dumps
    chokes on, so we walk the dict tree once before returning.
    """
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def _check_building_access(
    building_id: str,
    visible_building_ids: list[str],
) -> dict[str, Any] | None:
    """Return an {"error": ...} dict if the building is not visible.

    Returns None (success — falsy) when the building is accessible.
    Pattern used at the top of every per-building handler.
    """
    if building_id not in visible_building_ids:
        return {
            "error": (
                f"Building '{building_id}' is not in the accessible portfolio. "
                f"Accessible buildings: {visible_building_ids[:10]}"
                f"{'...' if len(visible_building_ids) > 10 else ''}"
            )
        }
    return None


# =====================================================================
# Tool 1 — query_kpi
# =====================================================================

QUERY_KPI_TOOL = ToolDefinition(
    name="query_kpi",
    description=(
        "Get a single energy KPI value for one building over a recent window, "
        "with delta vs the prior equal-length window. Use this when the user "
        "asks 'what is X for building Y' — e.g. consumption, cost, CO2, EUI."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "building_id": {
                "type": "string",
                "description": (
                    "The fabric_building_id of the building, e.g. 'B001'. "
                    "Must be a building visible to the user."
                ),
            },
            "metric": {
                "type": "string",
                "enum": ["energy", "cost", "co2", "eui"],
                "description": (
                    "'energy' = total kWh, 'cost' = EUR, 'co2' = kg CO2e, "
                    "'eui' = kWh/m²/year (annualized)."
                ),
            },
            "days": {
                "type": "integer",
                "minimum": 1,
                "maximum": 365,
                "default": 30,
                "description": "Window length in days. Defaults to 30.",
            },
        },
        "required": ["building_id", "metric"],
    },
)


def query_kpi(
    *,
    ctx,  # ToolContext — typed loosely to avoid circular import at module load
    building_id: str,
    metric: str,
    days: int = 30,
    **_extra,
) -> dict[str, Any]:
    err = _check_building_access(building_id, ctx.visible_building_ids)
    if err:
        return err

    valid_metrics = {"energy", "cost", "co2", "eui"}
    if metric not in valid_metrics:
        return {"error": f"Invalid metric '{metric}'. Must be one of {sorted(valid_metrics)}."}

    # Anchor to MAX(date) for this building — see portfolio_metrics.py rationale.
    anchor_sql = "SELECT MAX([date]) FROM [dbo].[gold_kpi_daily] WHERE building_id = ?"
    anchor = fabric_sql.execute_scalar(anchor_sql, (building_id,))
    if anchor is None:
        return {
            "error": f"No KPI data found for building '{building_id}'.",
        }

    cur_start = anchor - timedelta(days=days - 1)
    cur_end = anchor
    prev_start = anchor - timedelta(days=days * 2 - 1)
    prev_end = anchor - timedelta(days=days)

    # area JOIN only needed for EUI
    sql = """
    WITH cur AS (
        SELECT
            SUM(total_consumption_kwh) AS kwh,
            SUM(estimated_cost_eur)    AS cost,
            SUM(co2_emissions_kg)      AS co2
        FROM [dbo].[gold_kpi_daily]
        WHERE building_id = ? AND [date] BETWEEN ? AND ?
    ),
    prev AS (
        SELECT
            SUM(total_consumption_kwh) AS kwh,
            SUM(estimated_cost_eur)    AS cost,
            SUM(co2_emissions_kg)      AS co2
        FROM [dbo].[gold_kpi_daily]
        WHERE building_id = ? AND [date] BETWEEN ? AND ?
    ),
    area AS (
        SELECT gross_floor_area_m2, building_name
        FROM [dbo].[silver_building_master]
        WHERE building_id = ?
    )
    SELECT
        cur.kwh AS cur_kwh, cur.cost AS cur_cost, cur.co2 AS cur_co2,
        prev.kwh AS prev_kwh, prev.cost AS prev_cost, prev.co2 AS prev_co2,
        area.gross_floor_area_m2 AS area_m2,
        area.building_name AS name
    FROM cur CROSS JOIN prev CROSS JOIN area
    """
    rows = fabric_sql.execute_query(
        sql,
        (
            building_id, cur_start, cur_end,
            building_id, prev_start, prev_end,
            building_id,
        ),
    )
    if not rows:
        return {"error": f"No data for building '{building_id}' in the last {days} days."}

    r = rows[0]
    days_factor = 365.25 / days

    if metric == "energy":
        cur_val = _safe_float(r["cur_kwh"])
        prev_val = _safe_float(r["prev_kwh"])
        unit = "kWh"
    elif metric == "cost":
        cur_val = _safe_float(r["cur_cost"])
        prev_val = _safe_float(r["prev_cost"])
        unit = "EUR"
    elif metric == "co2":
        cur_val = _safe_float(r["cur_co2"])
        prev_val = _safe_float(r["prev_co2"])
        unit = "kg CO2e"
    else:  # eui
        area = _safe_float(r["area_m2"])
        if area <= 0:
            return {"error": "Building floor area is not recorded; EUI cannot be computed."}
        cur_val = (_safe_float(r["cur_kwh"]) * days_factor) / area
        prev_val = (_safe_float(r["prev_kwh"]) * days_factor) / area
        unit = "kWh/m²/year"

    return _json_safe({
        "building_id": building_id,
        "building_name": r["name"],
        "metric": metric,
        "unit": unit,
        "current_value": round(cur_val, 2),
        "prior_value": round(prev_val, 2),
        "delta_pct": round(_delta_pct(cur_val, prev_val), 2) if _delta_pct(cur_val, prev_val) is not None else None,
        "period_days": days,
        "current_period": {"start": cur_start, "end": cur_end},
        "prior_period": {"start": prev_start, "end": prev_end},
    })


# =====================================================================
# Tool 2 — compare_buildings
# =====================================================================

COMPARE_BUILDINGS_TOOL = ToolDefinition(
    name="compare_buildings",
    description=(
        "Rank multiple buildings by a single metric over a recent window. "
        "Use when the user asks 'which of my buildings is worst/best at X' "
        "or 'compare X across these buildings'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "building_ids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 20,
                "description": "List of fabric_building_ids to compare.",
            },
            "metric": {
                "type": "string",
                "enum": ["energy", "cost", "co2", "eui"],
                "description": "Which metric to rank by.",
            },
            "days": {
                "type": "integer",
                "minimum": 1,
                "maximum": 365,
                "default": 30,
            },
            "order": {
                "type": "string",
                "enum": ["highest_first", "lowest_first"],
                "default": "highest_first",
                "description": (
                    "'highest_first' = worst at top for 'lower-is-better' "
                    "metrics like energy/cost/co2/eui."
                ),
            },
        },
        "required": ["building_ids", "metric"],
    },
)


def compare_buildings(
    *,
    ctx,
    building_ids: list[str],
    metric: str,
    days: int = 30,
    order: str = "highest_first",
    **_extra,
) -> dict[str, Any]:
    # Filter to only visible buildings — silently drop any forbidden IDs to
    # avoid enumeration leak. LLM sees only what's allowed in the result.
    allowed = [bid for bid in building_ids if bid in ctx.visible_building_ids]
    rejected = [bid for bid in building_ids if bid not in ctx.visible_building_ids]
    if not allowed:
        return {"error": "None of the requested buildings are accessible."}

    valid_metrics = {"energy", "cost", "co2", "eui"}
    if metric not in valid_metrics:
        return {"error": f"Invalid metric '{metric}'. Must be one of {sorted(valid_metrics)}."}

    # Anchor to MAX(date) across the visible buildings.
    ph, params = fabric_sql.format_in_clause(allowed)
    anchor_sql = (
        f"SELECT MAX([date]) FROM [dbo].[gold_kpi_daily] "
        f"WHERE building_id IN ({ph})"
    )
    anchor = fabric_sql.execute_scalar(anchor_sql, params)
    if anchor is None:
        return {"error": "No KPI data for the requested buildings."}

    cur_start = anchor - timedelta(days=days - 1)
    days_factor = 365.25 / days

    sql = f"""
    SELECT
        b.building_id,
        b.building_name,
        b.city,
        b.gross_floor_area_m2 AS area_m2,
        ISNULL(SUM(k.total_consumption_kwh), 0) AS kwh,
        ISNULL(SUM(k.estimated_cost_eur), 0)    AS cost,
        ISNULL(SUM(k.co2_emissions_kg), 0)      AS co2
    FROM [dbo].[silver_building_master] b
    LEFT JOIN [dbo].[gold_kpi_daily] k
        ON k.building_id = b.building_id
       AND k.[date] BETWEEN ? AND ?
    WHERE b.building_id IN ({ph})
    GROUP BY b.building_id, b.building_name, b.city, b.gross_floor_area_m2
    """
    rows = fabric_sql.execute_query(sql, (cur_start, anchor, *params))

    items: list[dict[str, Any]] = []
    for r in rows:
        kwh = _safe_float(r["kwh"])
        cost = _safe_float(r["cost"])
        co2 = _safe_float(r["co2"])
        area = _safe_float(r["area_m2"])

        if metric == "energy":
            value, unit = kwh, "kWh"
        elif metric == "cost":
            value, unit = cost, "EUR"
        elif metric == "co2":
            value, unit = co2, "kg CO2e"
        else:  # eui
            value = (kwh * days_factor) / area if area > 0 else 0.0
            unit = "kWh/m²/year"

        items.append({
            "building_id": r["building_id"],
            "building_name": r["building_name"],
            "city": r["city"],
            "value": round(value, 2),
        })

    items.sort(key=lambda x: x["value"], reverse=(order == "highest_first"))
    for i, item in enumerate(items, start=1):
        item["rank"] = i

    return _json_safe({
        "metric": metric,
        "unit": unit,
        "period_days": days,
        "period": {"start": cur_start, "end": anchor},
        "ranking_order": order,
        "ranked": items,
        "rejected_building_ids": rejected,  # so the LLM can mention if some were dropped
    })


# =====================================================================
# Tool 3 — list_recommendations
# =====================================================================

LIST_RECOMMENDATIONS_TOOL = ToolDefinition(
    name="list_recommendations",
    description=(
        "List energy-saving recommendations for a building, sorted by "
        "estimated savings. Use when the user asks 'what can I do to "
        "improve X' or 'what should I fix first'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "building_id": {
                "type": "string",
                "description": "fabric_building_id of the target building.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 10,
            },
            "category": {
                "type": "string",
                "description": (
                    "Optional category filter, e.g. 'HVAC', 'Lighting', "
                    "'Envelope', 'Controls'. Omit to include all categories."
                ),
            },
        },
        "required": ["building_id"],
    },
)


def list_recommendations(
    *,
    ctx,
    building_id: str,
    limit: int = 10,
    category: str | None = None,
    **_extra,
) -> dict[str, Any]:
    err = _check_building_access(building_id, ctx.visible_building_ids)
    if err:
        return err

    # Schema (verified 2026-05-28):
    #   - No surrogate `recommendation_id` column. We synthesize one from
    #     `building_id|rank` so update_action_status has a stable identifier
    #     to write to Postgres recommendation_status.
    #   - Category filter maps to `action_type` (e.g. "HVAC", "Envelope").
    #   - Titles + descriptions are multilingual (title_en/de/tr); English by default.
    #   - Cost split into capex_eur + grant_eur + net_capex_eur. We surface
    #     capex_eur as "implementation_cost_eur" alias for stable response API.
    #   - Recommendations rank within a building via priority_sort_order ASC
    #     (lower = higher priority) then priority_score DESC.
    params: list[Any] = [building_id]
    where_extra = ""
    if category:
        where_extra = " AND action_type = ?"
        params.append(category)

    sql = f"""
    SELECT TOP (?)
        building_id,
        rank,
        action_type,
        priority_label,
        priority_score,
        compliance_driver,
        annual_saving_eur,
        co2_saving_kg,
        capex_eur,
        net_capex_eur,
        grant_eur,
        payback_years,
        npv_eur,
        title_en,
        description_en
    FROM [dbo].[gold_recommendations]
    WHERE building_id = ?{where_extra}
    ORDER BY priority_sort_order ASC, ISNULL(priority_score, 0) DESC
    """
    rows = fabric_sql.execute_query(sql, (limit, *params))

    def _synth_id(building: str, rank: Any) -> str:
        """Synthetic recommendation identifier — unique within (org, building)."""
        return f"{building}|{int(rank) if rank is not None else 0}"

    # Overlay Postgres recommendation_status for matching synthetic IDs.
    rec_ids = [_synth_id(building_id, r.get("rank")) for r in rows]
    statuses: dict[str, str] = {}
    if rec_ids:
        stmt = (
            select(
                RecommendationStatus.fabric_recommendation_id,
                RecommendationStatus.status,
            )
            .where(RecommendationStatus.organization_id == ctx.organization_id)
            .where(RecommendationStatus.fabric_recommendation_id.in_(rec_ids))
        )
        for fid, st in ctx.db.execute(stmt).all():
            statuses[fid] = st

    def _payback_months(years: Any) -> float | None:
        if years is None:
            return None
        return _safe_float(years) * 12

    recs = [
        {
            # Synthetic ID — pass this back to update_action_status.
            "recommendation_id": _synth_id(building_id, r.get("rank")),
            "rank": int(r["rank"]) if r.get("rank") is not None else None,
            "category": r.get("action_type"),
            "title": r.get("title_en"),
            "description": r.get("description_en"),
            "priority": r.get("priority_label"),
            "priority_score": _safe_float(r.get("priority_score")) if r.get("priority_score") is not None else None,
            "compliance_driver": r.get("compliance_driver"),
            "estimated_savings_eur": _safe_float(r.get("annual_saving_eur")),
            "co2_saving_kg": _safe_float(r.get("co2_saving_kg")),
            "payback_months": _payback_months(r.get("payback_years")),
            "payback_years": _safe_float(r.get("payback_years")) if r.get("payback_years") is not None else None,
            "implementation_cost_eur": _safe_float(r.get("capex_eur")) if r.get("capex_eur") is not None else None,
            "net_capex_eur": _safe_float(r.get("net_capex_eur")) if r.get("net_capex_eur") is not None else None,
            "grant_eur": _safe_float(r.get("grant_eur")) if r.get("grant_eur") is not None else None,
            "npv_eur": _safe_float(r.get("npv_eur")) if r.get("npv_eur") is not None else None,
            "status": statuses.get(_synth_id(building_id, r.get("rank")), "open"),
        }
        for r in rows
    ]

    return _json_safe({
        "building_id": building_id,
        "category_filter": category,
        "count": len(recs),
        "recommendations": recs,
    })


# =====================================================================
# Tool 4 — get_anomalies
# =====================================================================

GET_ANOMALIES_TOOL = ToolDefinition(
    name="get_anomalies",
    description=(
        "Get anomaly events for a building over a recent window. Anomalies "
        "are unusual consumption spikes / drops detected by the platform."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "building_id": {"type": "string"},
            "severity": {
                "type": "string",
                "enum": ["HIGH", "CRITICAL", "all"],
                "default": "all",
                "description": (
                    "Filter by severity. UPPERCASE values matter (Day 15 finding). "
                    "'all' includes MEDIUM/LOW as well."
                ),
            },
            "days": {
                "type": "integer",
                "minimum": 1,
                "maximum": 365,
                "default": 30,
            },
            "include_resolved": {
                "type": "boolean",
                "default": False,
                "description": "If false, only unresolved anomalies are returned.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 25,
            },
        },
        "required": ["building_id"],
    },
)


def get_anomalies(
    *,
    ctx,
    building_id: str,
    severity: str = "all",
    days: int = 30,
    include_resolved: bool = False,
    limit: int = 25,
    **_extra,
) -> dict[str, Any]:
    err = _check_building_access(building_id, ctx.visible_building_ids)
    if err:
        return err

    if severity not in {"HIGH", "CRITICAL", "all"}:
        return {"error": f"Invalid severity '{severity}'. Use 'HIGH', 'CRITICAL', or 'all'."}

    # Window anchor — anomaly log may not match KPI anchor exactly. Anchor to
    # MAX(detected_at) so a fresh-data window works even when sample data lags
    # real "today".
    anchor_sql = (
        "SELECT MAX(detected_at) FROM [dbo].[gold_anomaly_log] "
        "WHERE building_id = ?"
    )
    anchor = fabric_sql.execute_scalar(anchor_sql, (building_id,))
    if anchor is None:
        return {
            "building_id": building_id,
            "count": 0,
            "anomalies": [],
            "by_severity": {},
            "note": "No anomaly events recorded for this building.",
        }

    window_start = anchor - timedelta(days=days - 1) if isinstance(anchor, datetime) else anchor

    sev_clause = ""
    params: list[Any] = [limit, building_id, window_start]
    if severity in {"HIGH", "CRITICAL"}:
        sev_clause = " AND severity = ?"
        params.append(severity)

    resolved_clause = "" if include_resolved else " AND is_resolved = 0"

    # Schema (verified 2026-05-28): metric_value + threshold_value carry the
    # actual values; description is available in 3 languages (en/de/tr) —
    # we pick English by default. deviation_pct is computed here, not stored.
    sql = f"""
    SELECT TOP (?)
        anomaly_id,
        building_id,
        anomaly_type,
        severity,
        detected_at,
        is_resolved,
        metric_value,
        threshold_value,
        description_en,
        recommended_action_en
    FROM [dbo].[gold_anomaly_log]
    WHERE building_id = ?
      AND detected_at >= ?
      {resolved_clause}
      {sev_clause}
    ORDER BY detected_at DESC
    """
    rows = fabric_sql.execute_query(sql, tuple(params))

    # Severity distribution (across full window, not just TOP N)
    dist_sql = f"""
    SELECT severity, COUNT(*) AS n
    FROM [dbo].[gold_anomaly_log]
    WHERE building_id = ?
      AND detected_at >= ?
      {resolved_clause}
    GROUP BY severity
    """
    dist_rows = fabric_sql.execute_query(dist_sql, (building_id, window_start))
    by_sev = {r["severity"]: int(r["n"]) for r in dist_rows}

    def _deviation_pct(metric: Any, threshold: Any) -> float | None:
        """(metric - threshold) / threshold * 100, None when threshold is 0/null."""
        m = _safe_float(metric)
        t = _safe_float(threshold)
        if t == 0:
            return None
        return (m - t) / t * 100

    anomalies = [
        {
            "anomaly_id": str(r.get("anomaly_id")) if r.get("anomaly_id") is not None else None,
            "anomaly_type": r.get("anomaly_type"),
            "severity": r.get("severity"),
            "detected_at": r.get("detected_at"),
            "is_resolved": bool(r.get("is_resolved")),
            # Stable response API — aliased from DB columns to keep summarizers
            # (mock provider) and frontend types schema-agnostic.
            "consumption_kwh": _safe_float(r.get("metric_value")),
            "baseline_kwh": _safe_float(r.get("threshold_value")),
            "deviation_pct": _deviation_pct(r.get("metric_value"), r.get("threshold_value")),
            "description": r.get("description_en"),
            "recommended_action": r.get("recommended_action_en"),
        }
        for r in rows
    ]

    return _json_safe({
        "building_id": building_id,
        "window_days": days,
        "severity_filter": severity,
        "include_resolved": include_resolved,
        "count": len(anomalies),
        "by_severity": by_sev,
        "anomalies": anomalies,
    })


# =====================================================================
# Tool 5 — simulate_battery_scenario
# =====================================================================

SIMULATE_BATTERY_SCENARIO_TOOL = ToolDefinition(
    name="simulate_battery_scenario",
    description=(
        "Return ROI metrics for a battery storage deployment scenario at a "
        "building. Use when the user asks about battery payback, ROI, "
        "savings, or wants to compare chemistries / dispatch strategies. "
        "Data is precomputed in gold_battery_simulation (multiple scenarios "
        "per building covering chemistries × dispatch strategies)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "building_id": {"type": "string"},
            "chemistry": {
                "type": "string",
                "description": (
                    "Battery chemistry / technology: LFP, NMC, NCA, "
                    "Solid-State, etc. Maps to battery_tech in the data. "
                    "Omit to get the best scenario across all chemistries."
                ),
            },
            "strategy": {
                "type": "string",
                "description": (
                    "Dispatch strategy: 'peak_shaving', 'arbitrage', "
                    "'self_consumption', 'tou', 'pv_smoothing', etc. "
                    "Omit to get the best scenario across all strategies."
                ),
            },
        },
        "required": ["building_id"],
    },
)


def simulate_battery_scenario(
    *,
    ctx,
    building_id: str,
    chemistry: str | None = None,
    strategy: str | None = None,
    **_extra,
) -> dict[str, Any]:
    err = _check_building_access(building_id, ctx.visible_building_ids)
    if err:
        return err

    # Schema (verified 2026-05-28):
    #   - "chemistry" parameter maps to DB column `battery_tech`.
    #   - NPV column is `npv_10yr_eur` (10-year horizon, not generic).
    #   - ROI is expressed as `irr_percent` (internal rate of return).
    #   - CO₂ avoided is `annual_co2_avoided_kg`.
    #   - is_active_strategy filters to scenarios marked as the active config.
    # Response shape stays the same (chemistry / npv_eur / roi_pct aliases)
    # so the mock summarizer and frontend types don't need to change.
    where_clauses = ["building_id = ?"]
    params: list[Any] = [building_id]
    if chemistry:
        where_clauses.append("battery_tech = ?")
        params.append(chemistry)
    if strategy:
        where_clauses.append("strategy = ?")
        params.append(strategy)

    where_sql = " AND ".join(where_clauses)
    sql = f"""
    SELECT TOP 5
        scenario_id,
        building_id,
        building_name,
        country,
        battery_tech,
        battery_type,
        eu_compliant,
        battery_capacity_kwh,
        battery_power_kw,
        pv_capacity_kwp,
        total_capex_eur,
        strategy,
        strategy_label,
        is_active_strategy,
        annual_savings_eur,
        annual_co2_avoided_kg,
        payback_years,
        npv_10yr_eur,
        irr_percent
    FROM [dbo].[gold_battery_simulation]
    WHERE {where_sql}
    ORDER BY ISNULL(npv_10yr_eur, 0) DESC
    """
    try:
        rows = fabric_sql.execute_query(sql, tuple(params))
    except Exception as exc:
        # Defensive: schema could still drift over time. Surface to the LLM
        # so it can apologize instead of crashing the stream.
        return {
            "error": (
                "Could not query gold_battery_simulation. "
                f"Details: {type(exc).__name__}: {exc}"
            )
        }

    if not rows:
        filters_used = []
        if chemistry:
            filters_used.append(f"chemistry={chemistry}")
        if strategy:
            filters_used.append(f"strategy={strategy}")
        return {
            "building_id": building_id,
            "scenarios": [],
            "note": (
                f"No battery simulation scenarios found"
                + (f" with filters {filters_used}" if filters_used else "")
                + ". The building may not have battery analysis available yet."
            ),
        }

    scenarios = [
        {
            "scenario_id": r.get("scenario_id"),
            "building_name": r.get("building_name"),
            "country": r.get("country"),
            # Aliased to match the response API used by the mock summarizer
            # and the frontend — internal DB column is `battery_tech`.
            "chemistry": r.get("battery_tech"),
            "battery_type": r.get("battery_type"),
            "strategy": r.get("strategy"),
            "strategy_label": r.get("strategy_label"),
            "is_active_strategy": bool(r.get("is_active_strategy")) if r.get("is_active_strategy") is not None else None,
            "battery_capacity_kwh": _safe_float(r.get("battery_capacity_kwh")),
            "battery_power_kw": _safe_float(r.get("battery_power_kw")) if r.get("battery_power_kw") is not None else None,
            "pv_capacity_kwp": _safe_float(r.get("pv_capacity_kwp")) if r.get("pv_capacity_kwp") is not None else None,
            "total_capex_eur": _safe_float(r.get("total_capex_eur")) if r.get("total_capex_eur") is not None else None,
            "annual_savings_eur": _safe_float(r.get("annual_savings_eur")),
            "payback_years": _safe_float(r.get("payback_years")) if r.get("payback_years") is not None else None,
            # Aliased — DB stores 10-year NPV under a more specific name.
            "npv_eur": _safe_float(r.get("npv_10yr_eur")),
            "roi_pct": _safe_float(r.get("irr_percent")) if r.get("irr_percent") is not None else None,
            "co2_reduction_kg_year": _safe_float(r.get("annual_co2_avoided_kg")),
            "eu_compliant": bool(r.get("eu_compliant")) if r.get("eu_compliant") is not None else None,
        }
        for r in rows
    ]

    return _json_safe({
        "building_id": building_id,
        "filter": {"chemistry": chemistry, "strategy": strategy},
        "count": len(scenarios),
        "scenarios": scenarios,
        "best_scenario": scenarios[0] if scenarios else None,
    })


# =====================================================================
# Tool 6 — update_action_status (Postgres write)
# =====================================================================

UPDATE_ACTION_STATUS_TOOL = ToolDefinition(
    name="update_action_status",
    description=(
        "Update the status of a recommendation/action for tracking purposes. "
        "Used to mark a recommendation as in-progress, completed, or "
        "dismissed. Writes to the Postgres recommendation_status table "
        "(not Fabric). Available statuses: open, in_progress, completed, "
        "dismissed."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "fabric_recommendation_id": {
                "type": "string",
                "description": "The recommendation_id from gold_recommendations.",
            },
            "building_id": {
                "type": "string",
                "description": (
                    "fabric_building_id the recommendation belongs to. "
                    "Required for authorization."
                ),
            },
            "status": {
                "type": "string",
                "enum": ["open", "in_progress", "completed", "dismissed"],
            },
            "notes": {
                "type": "string",
                "description": "Optional free-text notes about the status change.",
            },
        },
        "required": ["fabric_recommendation_id", "building_id", "status"],
    },
)


def update_action_status(
    *,
    ctx,
    fabric_recommendation_id: str,
    building_id: str,
    status: str,
    notes: str | None = None,
    **_extra,
) -> dict[str, Any]:
    err = _check_building_access(building_id, ctx.visible_building_ids)
    if err:
        return err

    valid_statuses = {"open", "in_progress", "completed", "dismissed"}
    if status not in valid_statuses:
        return {"error": f"Invalid status '{status}'. Must be one of {sorted(valid_statuses)}."}

    # Look up the Postgres building row to get the UUID FK for recommendation_status.
    bldg = ctx.db.scalar(
        select(Building).where(Building.fabric_building_id == building_id)
    )
    if bldg is None:
        return {"error": f"Building '{building_id}' not registered in app database."}

    # Upsert: find existing row or insert new.
    existing = ctx.db.scalar(
        select(RecommendationStatus).where(
            RecommendationStatus.organization_id == ctx.organization_id,
            RecommendationStatus.fabric_recommendation_id == fabric_recommendation_id,
        )
    )

    if existing is None:
        new_row = RecommendationStatus(
            id=uuid4(),
            organization_id=ctx.organization_id,
            building_id=bldg.id,
            fabric_recommendation_id=fabric_recommendation_id,
            status=status,
            notes=notes,
        )
        if status == "completed":
            new_row.completed_by_user_id = ctx.user_id
            new_row.completed_at = datetime.now(timezone.utc)
        ctx.db.add(new_row)
        ctx.db.commit()
        return _json_safe({
            "success": True,
            "action": "created",
            "fabric_recommendation_id": fabric_recommendation_id,
            "new_status": status,
        })
    else:
        existing.status = status
        if notes is not None:
            existing.notes = notes
        if status == "completed" and existing.completed_at is None:
            existing.completed_by_user_id = ctx.user_id
            existing.completed_at = datetime.now(timezone.utc)
        ctx.db.commit()
        return _json_safe({
            "success": True,
            "action": "updated",
            "fabric_recommendation_id": fabric_recommendation_id,
            "new_status": status,
        })


# =====================================================================
# Registry — exported to dispatcher + LLMProvider
# =====================================================================

TOOL_DEFINITIONS: list[ToolDefinition] = [
    QUERY_KPI_TOOL,
    COMPARE_BUILDINGS_TOOL,
    LIST_RECOMMENDATIONS_TOOL,
    GET_ANOMALIES_TOOL,
    SIMULATE_BATTERY_SCENARIO_TOOL,
    UPDATE_ACTION_STATUS_TOOL,
]

TOOL_HANDLERS = {
    "query_kpi": query_kpi,
    "compare_buildings": compare_buildings,
    "list_recommendations": list_recommendations,
    "get_anomalies": get_anomalies,
    "simulate_battery_scenario": simulate_battery_scenario,
    "update_action_status": update_action_status,
}
