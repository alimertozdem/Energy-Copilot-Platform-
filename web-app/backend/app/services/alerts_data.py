"""Alerts service -- portfolio-wide READ over Fabric gold_anomaly_log, plus the
Day 31 Postgres acknowledge overlay (alert_status).

Two independent state dimensions:
  * Fabric is_resolved  -> analytical (did the data return to normal).
  * Postgres ack_status -> operational (has a human acknowledged / dismissed it).

"Unhandled" = unresolved AND not acknowledged/dismissed = the active triage
queue + the nav badge source. Computing it correctly means intersecting the
currently-unresolved anomaly ids (Fabric) with the org's acked/dismissed ids
(Postgres): an acked alert may have since auto-resolved, so we only subtract
acks that are STILL unresolved. The subtraction happens in Python to avoid an
anomaly_id IN-clause whose Fabric SQL type we don't want to assume.

Schema (verified via copilot get_anomalies, 2026-05-28):
    gold_anomaly_log(anomaly_id, building_id, anomaly_type, severity,
        detected_at, is_resolved, metric_value, threshold_value,
        description_en, recommended_action_en)
    severity UPPERCASE (CRITICAL / HIGH / MEDIUM / LOW).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.alert_status import AlertStatus
from app.integrations import fabric_sql
from app.repositories import building as building_repo
from app.services import access
from app.schemas.alerts import (
    AlertAckUpdateResponse,
    AlertItem,
    AlertSeverityCounts,
    AlertsResponse,
)

VALID_SEVERITIES: frozenset[str] = frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW"})
VALID_ACK_STATUSES: frozenset[str] = frozenset({"new", "acknowledged", "dismissed"})
_HANDLED: frozenset[str] = frozenset({"acknowledged", "dismissed"})

# Defensive cap on the unresolved-id scan used for the unhandled counts.
_UNRESOLVED_SCAN_CAP = 5000

VALID_RESOLUTIONS: frozenset[str] = frozenset({"unresolved", "resolved", "all"})

# Severity priority for ORDER BY (CRITICAL first). Shared across the row queries.
_SEVERITY_RANK_SQL = (
    "CASE severity "
    "WHEN 'CRITICAL' THEN 0 "
    "WHEN 'HIGH' THEN 1 "
    "WHEN 'MEDIUM' THEN 2 "
    "WHEN 'LOW' THEN 3 "
    "ELSE 4 END"
)


def _safe_float(v: Any) -> float | None:
    if v is None:
        return None
    return float(v)


def _deviation_pct(metric: Any, threshold: Any) -> float | None:
    """(metric - threshold) / threshold * 100. None when threshold is 0/null."""
    if metric is None or threshold is None:
        return None
    m = float(metric)
    t = float(threshold)
    if t == 0:
        return None
    return (m - t) / t * 100


def get_alerts_for_user(
    db: Session,
    *,
    user_id: UUID,
    severity: str | None = None,
    building_id: str | None = None,
    unresolved_only: bool = False,
    resolution: str | None = None,
    limit: int = 500,
) -> AlertsResponse:
    """Portfolio-wide anomaly view (Fabric) merged with the ack overlay (Postgres)."""
    visible_buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    fabric_ids = [b.fabric_building_id for b in visible_buildings if b.fabric_building_id]
    name_by_fid = {
        b.fabric_building_id: b.name
        for b in visible_buildings
        if b.fabric_building_id
    }
    org_ids = {b.organization_id for b in visible_buildings}
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
        return AlertsResponse(alerts=[], severity_counts=AlertSeverityCounts())

    if building_id is not None:
        if building_id not in fabric_ids:
            return AlertsResponse(alerts=[], severity_counts=AlertSeverityCounts())
        fabric_ids = [building_id]

    ph, ids_params = fabric_sql.format_in_clause(fabric_ids)

    sev_norm = severity.upper() if severity else None
    if sev_norm == "ALL":
        sev_norm = None

    sev_clause = ""
    sev_params: tuple = ()
    if sev_norm in VALID_SEVERITIES:
        sev_clause = " AND severity = ?"
        sev_params = (sev_norm,)

    # ---- Resolution filter (tri-state) -----------------------------------------
    # `resolution` (unresolved | resolved | all) is the modern param; the legacy
    # `unresolved_only` bool is kept for the nav badge poll. `resolution` wins
    # when both are supplied. Ordering is tuned per mode so the row cap never
    # starves the set the caller asked for:
    #   * unresolved -> active triage: most-severe, then newest.
    #   * resolved   -> recently-resolved first, so "Show resolved" is never
    #                   empty under the cap (the Day 33 bug).
    #   * all        -> unresolved first, then severity, then newest (legacy).
    res_norm = (resolution or "").lower() or None
    if res_norm not in VALID_RESOLUTIONS:
        res_norm = "unresolved" if unresolved_only else "all"

    if res_norm == "unresolved":
        resolved_clause = " AND is_resolved = 0"
        order_clause = f"ORDER BY {_SEVERITY_RANK_SQL} ASC, detected_at DESC"
    elif res_norm == "resolved":
        resolved_clause = " AND is_resolved = 1"
        order_clause = "ORDER BY detected_at DESC"
    else:  # all
        resolved_clause = ""
        order_clause = (
            f"ORDER BY is_resolved ASC, {_SEVERITY_RANK_SQL} ASC, detected_at DESC"
        )

    # ---- Row query (capped) ----------------------------------------------------
    row_sql = f"""
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
    WHERE building_id IN ({ph}){resolved_clause}{sev_clause}
    {order_clause}
    """
    rows = fabric_sql.execute_query(row_sql, (limit, *ids_params, *sev_params))

    # ---- Acknowledge overlay (Postgres), keyed by fabric_anomaly_id ----
    overlay: dict[str, AlertStatus] = {}
    if org_ids:
        stmt = select(AlertStatus).where(AlertStatus.organization_id.in_(org_ids))
        for a in db.scalars(stmt).all():
            overlay[a.fabric_anomaly_id] = a

    alerts: list[AlertItem] = []
    for r in rows:
        bid = r["building_id"]
        aid = str(r["anomaly_id"]) if r.get("anomaly_id") is not None else None
        ov = overlay.get(aid) if aid is not None else None
        alerts.append(
            AlertItem(
                anomaly_id=aid,
                fabric_building_id=bid,
                building_name=name_by_fid.get(bid, bid),
                anomaly_type=r.get("anomaly_type"),
                severity=(r.get("severity") or None),
                detected_at=r.get("detected_at"),
                is_resolved=bool(r.get("is_resolved")),
                metric_value=_safe_float(r.get("metric_value")),
                threshold_value=_safe_float(r.get("threshold_value")),
                deviation_pct=_deviation_pct(r.get("metric_value"), r.get("threshold_value")),
                description=r.get("description_en"),
                recommended_action=r.get("recommended_action_en"),
                ack_status=(ov.ack_status if ov else "new"),  # type: ignore[arg-type]
                acknowledged_at=(ov.acknowledged_at if ov else None),
                ack_notes=(ov.notes if ov else None),
                can_manage=can_manage_by_fid.get(bid, False),
            )
        )

    # ---- Counts (accurate regardless of the row cap) ----
    dist_sql = f"""
    SELECT severity, is_resolved, COUNT(*) AS n
    FROM [dbo].[gold_anomaly_log]
    WHERE building_id IN ({ph})
    GROUP BY severity, is_resolved
    """
    dist_rows = fabric_sql.execute_query(dist_sql, ids_params)
    counts = _aggregate_counts(dist_rows)

    # Overlay tallies (operational).
    for a in overlay.values():
        if a.ack_status == "acknowledged":
            counts.acknowledged += 1
        elif a.ack_status == "dismissed":
            counts.dismissed += 1

    # Unhandled = unresolved minus (acked/dismissed AND still unresolved).
    _fill_unhandled_counts(counts, ph, ids_params, overlay)

    return AlertsResponse(alerts=alerts, severity_counts=counts)


def _aggregate_counts(dist_rows: list[dict[str, Any]]) -> AlertSeverityCounts:
    """Fold a `severity x is_resolved` GROUP BY result into base counts."""
    counts = AlertSeverityCounts()
    for r in dist_rows:
        sev = (r.get("severity") or "").upper()
        n = int(r.get("n") or 0)
        resolved = bool(r.get("is_resolved"))

        counts.total += n
        if sev == "CRITICAL":
            counts.critical += n
        elif sev == "HIGH":
            counts.high += n
        elif sev == "MEDIUM":
            counts.medium += n
        elif sev == "LOW":
            counts.low += n

        if not resolved:
            counts.unresolved_total += n
            if sev == "CRITICAL":
                counts.unresolved_critical += n
            elif sev == "HIGH":
                counts.unresolved_high += n
            elif sev == "MEDIUM":
                counts.unresolved_medium += n
            elif sev == "LOW":
                counts.unresolved_low += n

    return counts


def _fill_unhandled_counts(
    counts: AlertSeverityCounts,
    ph: str,
    ids_params: tuple,
    overlay: dict[str, AlertStatus],
) -> None:
    """Set unhandled_* by scanning currently-unresolved ids and subtracting acks.

    Only acks whose anomaly is STILL unresolved are subtracted, so an acked alert
    that later auto-resolved doesn't double-count.
    """
    acked = {fid for fid, a in overlay.items() if a.ack_status in _HANDLED}
    sql = f"""
    SELECT TOP ({_UNRESOLVED_SCAN_CAP}) anomaly_id, severity
    FROM [dbo].[gold_anomaly_log]
    WHERE building_id IN ({ph}) AND is_resolved = 0
    """
    rows = fabric_sql.execute_query(sql, ids_params)
    for r in rows:
        aid = str(r["anomaly_id"]) if r.get("anomaly_id") is not None else None
        if aid is not None and aid in acked:
            continue
        sev = (r.get("severity") or "").upper()
        counts.unhandled_total += 1
        if sev == "CRITICAL":
            counts.unhandled_critical += 1
        elif sev == "HIGH":
            counts.unhandled_high += 1


def update_alert_ack_for_user(
    db: Session,
    *,
    user_id: UUID,
    anomaly_id: str,
    building_id: str,
    ack_status: str,
    notes: str | None = None,
) -> AlertAckUpdateResponse | None:
    """Upsert an alert_status row tied to the building's org.

    Returns None when:
      * ack_status is invalid
      * the building isn't visible to the user (mirrors GET visibility)

    The alert_status row is written under the building's organization_id so
    multi-member orgs share triage state (mirrors recommendation_status).
    """
    if ack_status not in VALID_ACK_STATUSES:
        return None

    bldg = building_repo.get_building_for_user(
        db, fabric_building_id=building_id, user_id=user_id
    )
    if bldg is None:
        return None

    org_id = bldg.organization_id
    now = datetime.now(timezone.utc)
    handled = ack_status in _HANDLED

    existing = db.scalar(
        select(AlertStatus).where(
            AlertStatus.organization_id == org_id,
            AlertStatus.fabric_anomaly_id == anomaly_id,
        )
    )

    if existing is None:
        row = AlertStatus(
            id=uuid4(),
            organization_id=org_id,
            building_id=bldg.id,
            fabric_anomaly_id=anomaly_id,
            ack_status=ack_status,
            notes=notes,
        )
        if handled:
            row.acknowledged_by_user_id = user_id
            row.acknowledged_at = now
        db.add(row)
        db.commit()
        db.refresh(row)
        return AlertAckUpdateResponse(
            anomaly_id=anomaly_id,
            ack_status=ack_status,  # type: ignore[arg-type]
            acknowledged_at=row.acknowledged_at,
        )

    existing.ack_status = ack_status
    if notes is not None:
        existing.notes = notes
    if handled:
        if existing.acknowledged_at is None:
            existing.acknowledged_at = now
        existing.acknowledged_by_user_id = user_id
    else:
        # Reset to 'new' clears the handled metadata.
        existing.acknowledged_at = None
        existing.acknowledged_by_user_id = None
    db.commit()
    db.refresh(existing)
    return AlertAckUpdateResponse(
        anomaly_id=anomaly_id,
        ack_status=ack_status,  # type: ignore[arg-type]
        acknowledged_at=existing.acknowledged_at,
    )
