"""Abatement service — builds the portfolio Marginal Abatement Cost Curve (MACC).

Reads Fabric `gold_recommendations` (same catalog as /actions), computes a
marginal abatement cost per measure, sorts cheapest-first, and returns the curve
+ portfolio totals. Visibility mirrors /actions and /portfolio: the user sees
measures for buildings in their orgs plus any sample/demo org.

Marginal abatement cost (STATED ASSUMPTION — energy reviewer: Mert):
    MAC (€/tCO2) = (net_capex / lifetime − annual_saving_eur) / annual_tCO2

  * Undiscounted, simplified annualisation (no WACC / CRF) — indicative, not
    audited finance. A negative MAC means the measure pays for itself.
  * `lifetime` is taken from MEASURE_LIFETIME_YEARS by action_type keyword,
    defaulting to DEFAULT_LIFETIME. These are typical engineering service lives,
    not guarantees — surfaced to the UI so the footnote is honest.
  * Measures with no / non-positive annual CO2 are excluded (can't sit on the
    CO2 axis). Missing CapEx is treated as 0 (e.g. operational/behavioural).
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.integrations import fabric_sql
from app.repositories import building as building_repo
from app.schemas.abatement import MaccMeasure, MaccResponse, MaccTotals

# Typical measure service lives (years). Stated assumption — see module docstring.
MEASURE_LIFETIME_YEARS: dict[str, int] = {
    "envelope": 30, "insulation": 30, "fabric": 30, "window": 30, "glazing": 30,
    "roof": 30, "facade": 30, "wall": 30,
    "solar": 25, "pv": 25, "photovoltaic": 25,
    "heat_pump": 18, "heatpump": 18, "hvac": 18, "boiler": 18, "chiller": 18,
    "heating": 18, "cooling": 18, "ventilation": 15,
    "battery": 12, "storage": 12, "lighting": 12, "led": 12,
    "control": 10, "bms": 10, "ems": 10, "automation": 10, "schedul": 10,
    "setpoint": 10, "thermostat": 10,
    "behav": 5, "operational": 5, "maintenance": 5, "commission": 5, "tuning": 5,
}
DEFAULT_LIFETIME = 15


def _safe_float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _lifetime_for(action_type: str | None, title: str | None) -> int:
    """Pick a measure lifetime by matching keywords in action_type then title."""
    hay = f"{action_type or ''} {title or ''}".lower()
    for keyword, years in MEASURE_LIFETIME_YEARS.items():
        if keyword in hay:
            return years
    return DEFAULT_LIFETIME


def get_macc_for_user(
    db: Session,
    *,
    user_id: UUID,
    building_id: str | None = None,
    limit: int = 500,
) -> MaccResponse:
    """Compute the portfolio MACC for everything the user can see."""
    note = (
        "Indicative marginal abatement cost: (net CapEx ÷ measure lifetime − annual "
        "saving) ÷ annual tCO₂, undiscounted. Negative = the measure pays for itself. "
        "Decision-support, not audited finance."
    )
    empty = MaccResponse(
        measures=[], totals=MaccTotals(),
        lifetime_assumptions=MEASURE_LIFETIME_YEARS, note=note,
    )

    visible = building_repo.list_buildings_for_user(db, user_id=user_id)
    fabric_ids = [b.fabric_building_id for b in visible if b.fabric_building_id]
    name_by_fid = {
        b.fabric_building_id: b.name for b in visible if b.fabric_building_id
    }
    if not fabric_ids:
        return empty

    if building_id is not None:
        if building_id not in fabric_ids:
            return empty
        fabric_ids = [building_id]

    ph, params = fabric_sql.format_in_clause(fabric_ids)
    sql = f"""
    SELECT TOP (?)
        building_id, rank, action_type, title_en, compliance_driver,
        annual_saving_eur, co2_saving_kg, capex_eur, net_capex_eur
    FROM [dbo].[gold_recommendations]
    WHERE building_id IN ({ph})
    """
    rows = fabric_sql.execute_query(sql, (limit, *params))

    measures: list[MaccMeasure] = []
    for r in rows:
        co2_kg = _safe_float(r.get("co2_saving_kg"))
        co2_t = co2_kg / 1000.0
        if co2_t <= 0:
            continue  # can't place a non-abating measure on the CO2 axis

        bid = r["building_id"]
        rank = r.get("rank")
        action_type = r.get("action_type")
        title = r.get("title_en")
        annual_saving = _safe_float(r.get("annual_saving_eur"))
        # Prefer net CapEx (after grant); fall back to gross, then 0.
        net_capex = _safe_float(
            r.get("net_capex_eur") if r.get("net_capex_eur") is not None
            else r.get("capex_eur")
        )
        lifetime = _lifetime_for(action_type, title)
        annualised_capex = net_capex / lifetime if lifetime > 0 else net_capex
        mac = (annualised_capex - annual_saving) / co2_t

        measures.append(
            MaccMeasure(
                action_id=f"{bid}|{int(rank) if rank is not None else 0}",
                fabric_building_id=bid,
                building_name=name_by_fid.get(bid, bid),
                title=title,
                action_type=action_type,
                compliance_driver=r.get("compliance_driver"),
                annual_co2_t=round(co2_t, 3),
                annual_saving_eur=round(annual_saving, 2),
                net_capex_eur=round(net_capex, 2),
                assumed_lifetime_years=lifetime,
                mac_eur_per_t=round(mac, 2),
                is_profitable=mac < 0,
                cumulative_co2_t=0.0,  # filled after sort
            )
        )

    # Cheapest-first ordering defines the curve; then accumulate CO2 on the x-axis.
    measures.sort(key=lambda m: m.mac_eur_per_t)
    running = 0.0
    for m in measures:
        running += m.annual_co2_t
        m.cumulative_co2_t = round(running, 3)

    total_co2 = sum(m.annual_co2_t for m in measures)
    profitable = [m for m in measures if m.is_profitable]
    weighted = (
        round(sum(m.mac_eur_per_t * m.annual_co2_t for m in measures) / total_co2, 2)
        if total_co2 > 0 else None
    )
    totals = MaccTotals(
        measure_count=len(measures),
        total_annual_co2_t=round(total_co2, 3),
        profitable_annual_co2_t=round(sum(m.annual_co2_t for m in profitable), 3),
        total_net_capex_eur=round(sum(m.net_capex_eur for m in measures), 2),
        profitable_net_capex_eur=round(sum(m.net_capex_eur for m in profitable), 2),
        weighted_avg_mac_eur_per_t=weighted,
    )
    return MaccResponse(
        measures=measures, totals=totals,
        lifetime_assumptions=MEASURE_LIFETIME_YEARS, note=note,
    )
