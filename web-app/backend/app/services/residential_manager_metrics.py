"""Manager-facing residential metrics (building grain).

Reads the residential Gold tables for ALL units of one building — the manager's
per-unit view (legitimate under HKVO cost allocation; NOT anonymized — anonymization
is the resident view). Same Fabric SQL read path as ``portfolio_metrics`` ([dbo],
parameterized). Building-level visibility is enforced by the router before calling.
"""
from datetime import datetime, timezone
from typing import Any

from app.integrations import fabric_sql
from app.schemas.residential import (
    ResidentialBuildingResponse,
    ResidentialBuildingRollup,
    ResidentialUnitRow,
    UviComplianceResponse,
    UviComplianceRow,
    UviStatus,
)

# --- UVI / HKVO compliance assumptions (STATED — energy/legal reviewer: Mert) ---
# HKVO §6a: monthly UVI mandatory from 1 Jan 2027 (remote-readable meters Dec 2026).
HKVO_UVI_DEADLINE = "2027-01-01"
# HKVO §12: a resident may cut 3% of their consumption-based heating cost when the
# UVI duty is breached. Exposure = 3% × annual heating cost.
HKVO_PENALTY_RATE = 0.03
# Heat tariff to turn kWh into a billed-cost basis (district-heating ballpark, DE).
# Indicative only — refine per the portfolio's actual heat price.
HEAT_TARIFF_EUR_KWH = 0.12
# Readiness thresholds (assumptions): "ready" = broad coverage + recent month.
UVI_READY_COVERAGE = 0.9
UVI_READY_MAX_MONTHS = 2


def _f(v: Any) -> float | None:
    return float(v) if v is not None else None


def _i(v: Any) -> int | None:
    return int(v) if v is not None else None


def get_building_residential(fabric_building_id: str) -> ResidentialBuildingResponse:
    """Per-unit KPIs + a building rollup for one building."""
    kpi_rows = fabric_sql.execute_query(
        """
        SELECT unit_id, area_m2, is_heated, eui_kwh_m2_yr, epc_band,
               vs_building_pct, heating_dhw_kwh_annual, cov_days,
               building_avg_eui_kwh_m2_yr
        FROM [dbo].[gold_residential_unit_kpi]
        WHERE building_id = ?
        ORDER BY unit_id
        """,
        (fabric_building_id,),
    )
    common = {
        r["unit_id"]: r
        for r in fabric_sql.execute_query(
            "SELECT unit_id, unit_allocated_kwh, allocation_share "
            "FROM [dbo].[gold_residential_common_split] WHERE building_id = ?",
            (fabric_building_id,),
        )
    }
    uvi_rows = fabric_sql.execute_query(
        "SELECT [year] AS y, [month] AS m, COUNT(DISTINCT unit_id) AS units "
        "FROM [dbo].[gold_residential_uvi_monthly] WHERE building_id = ? "
        "GROUP BY [year], [month] ORDER BY [year] DESC, [month] DESC",
        (fabric_building_id,),
    )

    units: list[ResidentialUnitRow] = []
    epc_dist: dict[str, int] = {}
    building_avg: float | None = None
    for r in kpi_rows:
        band = r.get("epc_band")
        if band:
            epc_dist[band] = epc_dist.get(band, 0) + 1
        if building_avg is None:
            building_avg = _f(r.get("building_avg_eui_kwh_m2_yr"))
        c = common.get(r["unit_id"], {})
        is_heated_raw = r.get("is_heated")
        units.append(
            ResidentialUnitRow(
                unit_id=r["unit_id"],
                area_m2=_f(r.get("area_m2")),
                is_heated=bool(is_heated_raw) if is_heated_raw is not None else None,
                eui_kwh_m2_yr=_f(r.get("eui_kwh_m2_yr")),
                epc_band=band,
                vs_building_pct=_f(r.get("vs_building_pct")),
                heating_dhw_kwh_annual=_f(r.get("heating_dhw_kwh_annual")),
                common_allocated_kwh=_f(c.get("unit_allocated_kwh")),
                cov_days=_i(r.get("cov_days")),
            )
        )

    uvi = UviStatus()
    if uvi_rows:
        top = uvi_rows[0]
        uvi = UviStatus(
            latest_year=_i(top.get("y")),
            latest_month=_i(top.get("m")),
            units_covered=_i(top.get("units")) or 0,
        )

    rollup = ResidentialBuildingRollup(
        units_with_data=len(units),
        building_avg_eui_kwh_m2_yr=building_avg,
        epc_distribution=epc_dist,
        uvi=uvi,
    )
    return ResidentialBuildingResponse(
        fabric_building_id=fabric_building_id, rollup=rollup, units=units
    )



def get_portfolio_rollups(building_ids: list[str]) -> dict[str, ResidentialBuildingRollup]:
    """Per-building rollups for many buildings at once (portfolio overview)."""
    if not building_ids:
        return {}
    ph, params = fabric_sql.format_in_clause(building_ids)
    kpi = fabric_sql.execute_query(
        "SELECT building_id, epc_band, building_avg_eui_kwh_m2_yr "
        f"FROM [dbo].[gold_residential_unit_kpi] WHERE building_id IN ({ph})",
        params,
    )
    uvi = fabric_sql.execute_query(
        "SELECT building_id, [year] AS y, [month] AS m, COUNT(DISTINCT unit_id) AS units "
        f"FROM [dbo].[gold_residential_uvi_monthly] WHERE building_id IN ({ph}) "
        "GROUP BY building_id, [year], [month]",
        params,
    )
    agg: dict[str, dict] = {}
    for r in kpi:
        b = r["building_id"]
        a = agg.setdefault(b, {"count": 0, "epc": {}, "avg": None})
        a["count"] += 1
        band = r.get("epc_band")
        if band:
            a["epc"][band] = a["epc"].get(band, 0) + 1
        if a["avg"] is None:
            a["avg"] = _f(r.get("building_avg_eui_kwh_m2_yr"))
    latest: dict[str, dict] = {}
    for r in uvi:
        b = r["building_id"]
        y, m = _i(r.get("y")), _i(r.get("m"))
        if y is None or m is None:
            continue
        cur = latest.get(b)
        if cur is None or (y, m) > (cur["y"], cur["m"]):
            latest[b] = {"y": y, "m": m, "u": _i(r.get("units")) or 0}
    out: dict[str, ResidentialBuildingRollup] = {}
    for b in building_ids:
        a = agg.get(b)
        ul = latest.get(b)
        out[b] = ResidentialBuildingRollup(
            units_with_data=a["count"] if a else 0,
            building_avg_eui_kwh_m2_yr=a["avg"] if a else None,
            epc_distribution=a["epc"] if a else {},
            uvi=(
                UviStatus(latest_year=ul["y"], latest_month=ul["m"], units_covered=ul["u"])
                if ul
                else UviStatus()
            ),
        )
    return out


def get_uvi_compliance(
    building_ids: list[str], names: dict[str, str]
) -> UviComplianceResponse:
    """Per-building UVI/HKVO compliance readiness + portfolio penalty exposure.

    Reuses the residential Gold tables (unit_kpi for unit counts + annual heat
    kWh; uvi_monthly for latest-month coverage). Penalty exposure is an indicative
    HKVO §12 estimate (see module constants). `names` maps fabric_building_id ->
    display name (the manager's building names live in Postgres, not Fabric).
    """
    note = (
        "Indicative HKVO §12 exposure: 3% of consumption-based heating cost "
        f"(≈ €{HEAT_TARIFF_EUR_KWH:.2f}/kWh). Monthly UVI is mandatory from "
        "1 Jan 2027. Decision-support, not legal advice."
    )
    empty = UviComplianceResponse(
        deadline=HKVO_UVI_DEADLINE, heat_tariff_eur_kwh=HEAT_TARIFF_EUR_KWH, note=note
    )
    if not building_ids:
        return empty

    ph, params = fabric_sql.format_in_clause(building_ids)
    kpi = fabric_sql.execute_query(
        "SELECT building_id, COUNT(*) AS units, "
        "SUM(heating_dhw_kwh_annual) AS heat_kwh "
        f"FROM [dbo].[gold_residential_unit_kpi] WHERE building_id IN ({ph}) "
        "GROUP BY building_id",
        params,
    )
    uvi = fabric_sql.execute_query(
        "SELECT building_id, [year] AS y, [month] AS m, COUNT(DISTINCT unit_id) AS units "
        f"FROM [dbo].[gold_residential_uvi_monthly] WHERE building_id IN ({ph}) "
        "GROUP BY building_id, [year], [month]",
        params,
    )

    kpi_by_b = {r["building_id"]: r for r in kpi}
    latest: dict[str, dict] = {}
    for r in uvi:
        b = r["building_id"]
        y, m = _i(r.get("y")), _i(r.get("m"))
        if y is None or m is None:
            continue
        cur = latest.get(b)
        if cur is None or (y, m) > (cur["y"], cur["m"]):
            latest[b] = {"y": y, "m": m, "u": _i(r.get("units")) or 0}

    now = datetime.now(timezone.utc)
    rows: list[UviComplianceRow] = []
    ready = at_risk = 0
    total_exposure = 0.0

    for b in building_ids:
        k = kpi_by_b.get(b, {})
        total_units = _i(k.get("units")) or 0
        heat_kwh = _f(k.get("heat_kwh"))
        ul = latest.get(b)
        units_covered = ul["u"] if ul else 0
        coverage = (units_covered / total_units) if total_units else None
        months_since = (
            (now.year - ul["y"]) * 12 + (now.month - ul["m"]) if ul else None
        )
        exposure = (
            round(HKVO_PENALTY_RATE * heat_kwh * HEAT_TARIFF_EUR_KWH, 2)
            if heat_kwh is not None
            else None
        )

        if units_covered == 0 or months_since is None:
            status = "at_risk"
        elif (
            coverage is not None
            and coverage >= UVI_READY_COVERAGE
            and months_since <= UVI_READY_MAX_MONTHS
        ):
            status = "ready"
        else:
            status = "partial"

        if status == "ready":
            ready += 1
        elif status == "at_risk":
            at_risk += 1
        if exposure:
            total_exposure += exposure

        rows.append(
            UviComplianceRow(
                fabric_building_id=b,
                name=names.get(b, b),
                total_units=total_units,
                units_covered=units_covered,
                coverage_pct=round(coverage, 3) if coverage is not None else None,
                latest_year=ul["y"] if ul else None,
                latest_month=ul["m"] if ul else None,
                months_since_latest=months_since,
                annual_heat_kwh=round(heat_kwh, 1) if heat_kwh is not None else None,
                penalty_exposure_eur=exposure,
                status=status,
            )
        )

    # At-risk first (worst), then partial, then ready — the manager's work queue.
    order = {"at_risk": 0, "partial": 1, "ready": 2}
    rows.sort(key=lambda r: (order.get(r.status, 3), -(r.penalty_exposure_eur or 0)))

    return UviComplianceResponse(
        deadline=HKVO_UVI_DEADLINE,
        buildings_total=len(building_ids),
        buildings_ready=ready,
        buildings_at_risk=at_risk,
        total_penalty_exposure_eur=round(total_exposure, 2),
        heat_tariff_eur_kwh=HEAT_TARIFF_EUR_KWH,
        note=note,
        rows=rows,
    )
