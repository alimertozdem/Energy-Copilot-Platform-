"""Actions service — Fabric gold_recommendations + Postgres recommendation_status join.

The Fabric catalog has no status column; the Postgres overlay holds the
lifecycle. This service joins the two and returns shaped DTOs for the
/actions endpoints.

Visibility (mirrors /portfolio): user sees recommendations for buildings in
their orgs plus buildings in any sample/demo org. Enforced via
building_repo.list_buildings_for_user.

Synthetic action_id format: "{fabric_building_id}|{rank}".  Day 16 finding —
gold_recommendations has no surrogate id, so rank within building is the
stable key.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Building, OrgMember
from app.db.models.recommendation import RecommendationStatus
from app.integrations import fabric_sql
from app.repositories import building as building_repo
from app.services import access
from app.schemas.actions import (
    ActionItem,
    ActionsResponse,
    ActionStatus,
    ActionStatusCounts,
    ActionStatusUpdateResponse,
)


# Allowed values mirror schemas.actions.ActionStatus -- enforced at the API
# boundary in the router but also defensively here.
VALID_STATUSES: frozenset[str] = frozenset(
    {"open", "in_progress", "completed", "dismissed", "not_applicable"}
)


def _safe_float(v: Any) -> float | None:
    if v is None:
        return None
    return float(v)


def _synth_id(building_id: str, rank: Any) -> str:
    """Stable synthetic identifier for a (building, rank) recommendation."""
    return f"{building_id}|{int(rank) if rank is not None else 0}"


def _parse_action_id(action_id: str) -> tuple[str, int] | None:
    """Parse 'B001|3' into ('B001', 3). Returns None for malformed input."""
    if "|" not in action_id:
        return None
    bid, _, rank_s = action_id.partition("|")
    try:
        return bid, int(rank_s)
    except ValueError:
        return None


# =====================================================================
# GET /actions
# =====================================================================

def get_actions_for_user(
    db: Session,
    *,
    user_id: UUID,
    status_filter: str | None = None,
    building_id: str | None = None,
    category: str | None = None,
    limit: int = 500,
) -> ActionsResponse:
    """Build the joined Fabric + Postgres view for the actions table.

    Filters are applied AFTER the join so status counts reflect the
    unfiltered view (frontend filter chips can show accurate totals while
    the visible rows are filtered).
    """
    visible_buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    fabric_ids = [b.fabric_building_id for b in visible_buildings if b.fabric_building_id]
    name_by_fid = {
        b.fabric_building_id: b.name
        for b in visible_buildings
        if b.fabric_building_id
    }
    pg_building_id_by_fid = {
        b.fabric_building_id: b.id for b in visible_buildings if b.fabric_building_id
    }
    org_ids = {b.organization_id for b in visible_buildings}
    # Write-gate per building (deduped by org): can the caller change status?
    _manage_by_org: dict = {}
    for _b in visible_buildings:
        if _b.organization_id not in _manage_by_org:
            _manage_by_org[_b.organization_id] = access.can_manage_building(
                db, user_id=user_id, building=_b
            )
    can_manage_by_fid = {
        b.fabric_building_id: _manage_by_org.get(b.organization_id, False)
        for b in visible_buildings
        if b.fabric_building_id
    }

    if not fabric_ids:
        return ActionsResponse(actions=[], status_counts=ActionStatusCounts())

    # Optional building scope -- ensure requested building is visible.
    if building_id is not None:
        if building_id not in fabric_ids:
            return ActionsResponse(actions=[], status_counts=ActionStatusCounts())
        fabric_ids = [building_id]

    ph, params = fabric_sql.format_in_clause(fabric_ids)

    cat_clause = ""
    cat_params: tuple = ()
    if category:
        cat_clause = " AND action_type = ?"
        cat_params = (category,)

    sql = f"""
    SELECT TOP (?)
        building_id,
        rank,
        action_type,
        title_en,
        description_en,
        priority_label,
        priority_score,
        compliance_driver,
        annual_saving_eur,
        co2_saving_kg,
        capex_eur,
        net_capex_eur,
        grant_eur,
        payback_years,
        npv_eur
    FROM [dbo].[gold_recommendations]
    WHERE building_id IN ({ph}){cat_clause}
    ORDER BY building_id ASC,
             priority_sort_order ASC,
             ISNULL(priority_score, 0) DESC
    """
    rows = fabric_sql.execute_query(sql, (limit, *params, *cat_params))

    # Postgres overlay — fetch every recommendation_status row for the user's
    # orgs in one query, then build a dict keyed by fabric_recommendation_id.
    overlay: dict[str, RecommendationStatus] = {}
    if org_ids:
        stmt = select(RecommendationStatus).where(
            RecommendationStatus.organization_id.in_(org_ids)
        )
        for s in db.scalars(stmt).all():
            overlay[s.fabric_recommendation_id] = s

    # Aggregate counts -- across the unfiltered status overlay so chips show
    # the org-wide totals, not just the filtered subset.
    counts = ActionStatusCounts()
    for s in overlay.values():
        if s.status == "open":
            counts.open += 1
        elif s.status == "in_progress":
            counts.in_progress += 1
        elif s.status == "completed":
            counts.completed += 1
        elif s.status == "dismissed":
            counts.dismissed += 1
        elif s.status == "not_applicable":
            counts.not_applicable += 1

    actions: list[ActionItem] = []
    for r in rows:
        bid = r["building_id"]
        rank = r.get("rank")
        action_id = _synth_id(bid, rank)
        overlay_row = overlay.get(action_id)
        status: ActionStatus = (
            overlay_row.status if overlay_row else "open"  # type: ignore[assignment]
        )

        # Frontend filter happens AFTER count aggregation.
        if status_filter and status_filter != "all" and status != status_filter:
            continue

        actions.append(
            ActionItem(
                action_id=action_id,
                fabric_building_id=bid,
                building_name=name_by_fid.get(bid, bid),
                rank=int(rank) if rank is not None else None,
                action_type=r.get("action_type"),
                title=r.get("title_en"),
                description=r.get("description_en"),
                priority_label=r.get("priority_label"),
                priority_score=_safe_float(r.get("priority_score")),
                compliance_driver=r.get("compliance_driver"),
                annual_saving_eur=_safe_float(r.get("annual_saving_eur")),
                co2_saving_kg=_safe_float(r.get("co2_saving_kg")),
                capex_eur=_safe_float(r.get("capex_eur")),
                net_capex_eur=_safe_float(r.get("net_capex_eur")),
                grant_eur=_safe_float(r.get("grant_eur")),
                payback_years=_safe_float(r.get("payback_years")),
                npv_eur=_safe_float(r.get("npv_eur")),
                status=status,
                status_updated_at=overlay_row.updated_at if overlay_row else None,
                completed_at=overlay_row.completed_at if overlay_row else None,
                notes=overlay_row.notes if overlay_row else None,
                can_manage=can_manage_by_fid.get(bid, False),
            )
        )

    # Total = catalog rows visible AFTER filtering -- this is what the user
    # sees in the table, distinct from per-status overlay counts.
    counts.total = len(actions)

    # Track how many catalog rows lack any overlay = implicit 'open' count
    # contribution. We adjust open up to reflect that a catalog row with no
    # Postgres row is considered open by default.
    implicit_open = sum(
        1
        for r in rows
        if _synth_id(r["building_id"], r.get("rank")) not in overlay
    )
    counts.open += implicit_open

    return ActionsResponse(actions=actions, status_counts=counts)


# =====================================================================
# PATCH /actions/{action_id}
# =====================================================================

def update_action_status_for_user(
    db: Session,
    *,
    user_id: UUID,
    action_id: str,
    new_status: ActionStatus,
    notes: str | None = None,
) -> ActionStatusUpdateResponse | None:
    """Upsert a recommendation_status row tied to the user's org.

    Returns None when:
      * action_id is malformed
      * the building referenced isn't visible to the user
      * the user has no org_member row (shouldn't happen via API but
        defensive)

    Authorization model:
      * Building must be visible to the user (mirrors GET /actions).
      * The recommendation_status row is written under the building's
        organization_id (not the user's "personal" org) so multi-member
        orgs share state.
    """
    if new_status not in VALID_STATUSES:
        return None

    parsed = _parse_action_id(action_id)
    if parsed is None:
        return None
    fabric_building_id, _rank = parsed

    # Look up the building (also enforces visibility via the repo).
    bldg = building_repo.get_building_for_user(
        db, fabric_building_id=fabric_building_id, user_id=user_id
    )
    if bldg is None:
        return None

    org_id = bldg.organization_id

    existing = db.scalar(
        select(RecommendationStatus).where(
            RecommendationStatus.organization_id == org_id,
            RecommendationStatus.fabric_recommendation_id == action_id,
        )
    )

    now = datetime.now(timezone.utc)

    if existing is None:
        row = RecommendationStatus(
            id=uuid4(),
            organization_id=org_id,
            building_id=bldg.id,
            fabric_recommendation_id=action_id,
            status=new_status,
            notes=notes,
        )
        if new_status == "completed":
            row.completed_by_user_id = user_id
            row.completed_at = now
        db.add(row)
        db.commit()
        db.refresh(row)
        return ActionStatusUpdateResponse(
            action_id=action_id,
            status=new_status,
            status_updated_at=row.updated_at or now,
            completed_at=row.completed_at,
        )

    existing.status = new_status
    if notes is not None:
        existing.notes = notes
    if new_status == "completed" and existing.completed_at is None:
        existing.completed_by_user_id = user_id
        existing.completed_at = now
    elif new_status != "completed":
        # Going back from completed → open / in_progress / dismissed clears
        # the completion timestamp so the user can reset state cleanly.
        existing.completed_at = None
        existing.completed_by_user_id = None
    db.commit()
    db.refresh(existing)
    return ActionStatusUpdateResponse(
        action_id=action_id,
        status=new_status,
        status_updated_at=existing.updated_at or now,
        completed_at=existing.completed_at,
    )
