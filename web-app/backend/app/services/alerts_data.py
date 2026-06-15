"""Alerts service -- portfolio-wide READ over Fabric gold_anomaly_log, collapsed
into ongoing *issues*, plus the Day 31 Postgres acknowledge overlay (alert_status).

Why grouping (2026-06-14 review)
--------------------------------
gold_anomaly_log keys every anomaly by (building_id, anomaly_type, DATE). A
chronic fault therefore emits a brand-new row every single day, so a handful of
real problems inflate into thousands of "alerts" (one demo building showed 508).
A facility manager can't act on 508 rows. This service now folds those daily
occurrences into one issue per (building_id, anomaly_type):

  * representative  = the worst-severity, then most-recent occurrence (its id,
    reading, description and recommended action are what the row shows);
  * occurrence_count = how many days the issue spans (the "how chronic" signal);
  * first/last_detected_at = active-since and latest.

All the counts (chips, summary cards, nav badge) are likewise issue-level, so the
numbers a user sees match the rows. The raw-event explosion is fixed at source in
the Fabric notebook (anomaly_detection.py episode model); this layer makes even
the current per-day data legible.

Two independent state dimensions survive grouping:
  * Fabric is_resolved  -> analytical (did the data return to normal). An issue
    is "open" when ANY occurrence is still unresolved.
  * Postgres ack_status -> operational (has a human acknowledged / dismissed the
    issue). Keyed by the open representative's anomaly_id.

"Unhandled" = open AND its representative not acknowledged/dismissed = the active
triage queue + the nav badge source.

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
from app.integrations import gold_read
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

VALID_RESOLUTIONS: frozenset[str] = frozenset({"unresolved", "resolved", "all"})

# Severity ordering (lower rank = worse). Drives "worst occurrence" selection and
# the table sort.
_SEVERITY_RANK: dict[str, int] = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
_RANK_TO_SEVERITY: dict[int, str] = {0: "CRITICAL", 1: "HIGH", 2: "MEDIUM", 3: "LOW"}

# Defensive cap on the raw-occurrence scan we group in Python. Realistic portfolios
# (post episode-model) sit in the low thousands; 50k keeps a pathological feed from
# blowing memory while never biting normal data. Ordered newest-first so a cap hit
# drops the oldest occurrences, not the active head of an issue.
_RAW_SCAN_CAP = 50000


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


def _rank(severity: Any) -> int:
    return _SEVERITY_RANK.get((severity or "").upper(), 4)


def _sort_key(detected_at: Any) -> Any:
    """A comparable key for 'most recent' that tolerates datetime or ISO string."""
    if detected_at is None:
        return ""
    if isinstance(detected_at, datetime):
        # Drop tz so naive/aware don't collide during max().
        return detected_at.replace(tzinfo=None)
    return str(detected_at)


class _NegStr:
    """Wraps a value so that ordering is reversed (descending)."""

    __slots__ = ("v",)

    def __init__(self, v: str) -> None:
        self.v = v

    def __lt__(self, other: "_NegStr") -> bool:
        return self.v > other.v

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _NegStr) and self.v == other.v


def _neg(ts: Any) -> _NegStr:
    """Invert a timestamp sort key so 'larger ts' compares as 'smaller'."""
    return _NegStr(str(ts))


class _Issue:
    """Accumulator for one (building_id, anomaly_type) group."""

    __slots__ = (
        "building_id", "anomaly_type", "occ_total", "occ_open",
        "first_at", "last_at", "worst_rank", "worst_open_rank",
        "rep", "rep_key", "open_rep", "open_rep_key",
    )

    def __init__(self, building_id: str, anomaly_type: Any) -> None:
        self.building_id = building_id
        self.anomaly_type = anomaly_type
        self.occ_total = 0
        self.occ_open = 0
        self.first_at: Any = None
        self.last_at: Any = None
        self.worst_rank = 99
        self.worst_open_rank = 99
        self.rep: dict[str, Any] | None = None        # worst-then-latest overall
        self.rep_key: tuple = (99, _NegStr(""))
        self.open_rep: dict[str, Any] | None = None    # worst-then-latest among open
        self.open_rep_key: tuple = (99, _NegStr(""))

    def add(self, r: dict[str, Any]) -> None:
        rank = _rank(r.get("severity"))
        ts = _sort_key(r.get("detected_at"))
        resolved = bool(r.get("is_resolved"))

        self.occ_total += 1
        if self.first_at is None or ts < self.first_at:
            self.first_at = ts
        if self.last_at is None or ts > self.last_at:
            self.last_at = ts
        if rank < self.worst_rank:
            self.worst_rank = rank

        # Representative = worst severity, then most recent. Lower key wins:
        # smaller rank first, then larger ts (via the descending _NegStr wrapper).
        cand_key = (rank, _neg(ts))
        if self.rep is None or cand_key < self.rep_key:
            self.rep, self.rep_key = r, cand_key

        if not resolved:
            self.occ_open += 1
            if rank < self.worst_open_rank:
                self.worst_open_rank = rank
            if self.open_rep is None or cand_key < self.open_rep_key:
                self.open_rep, self.open_rep_key = r, cand_key

    @property
    def has_open(self) -> bool:
        return self.occ_open > 0


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
    """Portfolio-wide issue view (Fabric, grouped) merged with the ack overlay."""
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

    res_norm = (resolution or "").lower() or None
    if res_norm not in VALID_RESOLUTIONS:
        res_norm = "unresolved" if unresolved_only else "all"

    # ---- One scan of the raw occurrences; group + count in Python -------------
    # We fetch the full visible scope once (no severity/resolution WHERE) so the
    # issue-level counts can see every occurrence, then derive the table from the
    # same rows. Realistic volumes are small; _RAW_SCAN_CAP guards the pathological.
    scan_sql = f"""
    SELECT TOP ({_RAW_SCAN_CAP})
        anomaly_id, building_id, anomaly_type, severity, detected_at,
        is_resolved, metric_value, threshold_value,
        description_en, recommended_action_en
    FROM [dbo].[gold_anomaly_log]
    WHERE building_id IN ({ph})
    ORDER BY detected_at DESC
    """
    all_rows = gold_read.query(scan_sql, ids_params)

    # Group every occurrence into issues (all resolutions, all severities).
    issues: dict[tuple, _Issue] = {}
    for r in all_rows:
        key = (r.get("building_id"), r.get("anomaly_type"))
        g = issues.get(key)
        if g is None:
            g = _Issue(r.get("building_id"), r.get("anomaly_type"))
            issues[key] = g
        g.add(r)

    # ---- Acknowledge overlay (Postgres), keyed by representative anomaly_id ----
    overlay: dict[str, AlertStatus] = {}
    if org_ids:
        stmt = select(AlertStatus).where(AlertStatus.organization_id.in_(org_ids))
        for a in db.scalars(stmt).all():
            overlay[a.fabric_anomaly_id] = a

    # ---- Build the table (issues matching the severity + resolution scope) -----
    items = _build_issue_items(
        issues, res_norm, sev_norm, overlay, name_by_fid, can_manage_by_fid
    )
    items = items[: max(limit, 0)]

    # ---- Issue-level counts (independent of the row cap) -----------------------
    counts = _issue_counts(issues, overlay)

    return AlertsResponse(alerts=items, severity_counts=counts)


def _build_issue_items(
    issues: dict[tuple, _Issue],
    res_norm: str | None,
    sev_norm: str | None,
    overlay: dict[str, AlertStatus],
    name_by_fid: dict[str, str],
    can_manage_by_fid: dict[str, bool],
) -> list[AlertItem]:
    """One AlertItem per in-scope issue, sorted worst-severity then most-recent."""
    rows: list[tuple[int, Any, AlertItem]] = []
    for issue in issues.values():
        # Resolution scope.
        if res_norm == "unresolved" and not issue.has_open:
            continue
        if res_norm == "resolved" and issue.has_open:
            # An issue with any open occurrence belongs to the open queue, not the
            # resolved view -- keeps "Show resolved" to genuinely closed issues.
            continue

        if res_norm == "unresolved":
            rep = issue.open_rep
            rep_rank = issue.worst_open_rank
            occ = issue.occ_open
        else:
            rep = issue.rep
            rep_rank = issue.worst_rank
            occ = issue.occ_total
        if rep is None:
            continue

        # Severity filter applies to the issue's (scoped) worst severity.
        if sev_norm in VALID_SEVERITIES and _RANK_TO_SEVERITY.get(rep_rank) != sev_norm:
            continue

        bid = issue.building_id
        aid = str(rep["anomaly_id"]) if rep.get("anomaly_id") is not None else None
        ov = overlay.get(aid) if aid is not None else None
        worst_sev = _RANK_TO_SEVERITY.get(rep_rank, (rep.get("severity") or None))

        rows.append((
            rep_rank,
            _neg(_sort_key(issue.last_at)),
            AlertItem(
                anomaly_id=aid,
                fabric_building_id=bid,
                building_name=name_by_fid.get(bid, bid),
                anomaly_type=rep.get("anomaly_type"),
                severity=worst_sev,
                detected_at=rep.get("detected_at"),
                is_resolved=bool(rep.get("is_resolved")),
                metric_value=_safe_float(rep.get("metric_value")),
                threshold_value=_safe_float(rep.get("threshold_value")),
                deviation_pct=_deviation_pct(
                    rep.get("metric_value"), rep.get("threshold_value")
                ),
                description=rep.get("description_en"),
                recommended_action=rep.get("recommended_action_en"),
                occurrence_count=int(occ),
                first_detected_at=_as_dt(issue.first_at),
                last_detected_at=_as_dt(issue.last_at),
                ack_status=(ov.ack_status if ov else "new"),  # type: ignore[arg-type]
                acknowledged_at=(ov.acknowledged_at if ov else None),
                ack_notes=(ov.notes if ov else None),
                can_manage=can_manage_by_fid.get(bid, False),
            ),
        ))

    rows.sort(key=lambda t: (t[0], t[1]))
    return [it for _, _, it in rows]


def _issue_counts(
    issues: dict[tuple, _Issue], overlay: dict[str, AlertStatus]
) -> AlertSeverityCounts:
    """Fold issues into issue-level severity counts (chips, cards, nav badge)."""
    counts = AlertSeverityCounts()
    acked = {fid for fid, a in overlay.items() if a.ack_status in _HANDLED}

    for issue in issues.values():
        counts.total += 1
        _bump_total(counts, issue.worst_rank)

        if issue.has_open:
            counts.unresolved_total += 1
            _bump_unresolved(counts, issue.worst_open_rank)

            # Unhandled = open issue whose open representative isn't acked/dismissed.
            rep = issue.open_rep or {}
            aid = str(rep["anomaly_id"]) if rep.get("anomaly_id") is not None else None
            if aid is None or aid not in acked:
                counts.unhandled_total += 1
                if issue.worst_open_rank == 0:
                    counts.unhandled_critical += 1
                elif issue.worst_open_rank == 1:
                    counts.unhandled_high += 1

    # Operational overlay tallies -- count issues whose representative is handled.
    for a in overlay.values():
        if a.ack_status == "acknowledged":
            counts.acknowledged += 1
        elif a.ack_status == "dismissed":
            counts.dismissed += 1

    return counts


def _bump_total(counts: AlertSeverityCounts, rank: int) -> None:
    if rank == 0:
        counts.critical += 1
    elif rank == 1:
        counts.high += 1
    elif rank == 2:
        counts.medium += 1
    elif rank == 3:
        counts.low += 1


def _bump_unresolved(counts: AlertSeverityCounts, rank: int) -> None:
    if rank == 0:
        counts.unresolved_critical += 1
    elif rank == 1:
        counts.unresolved_high += 1
    elif rank == 2:
        counts.unresolved_medium += 1
    elif rank == 3:
        counts.unresolved_low += 1


def _as_dt(ts: Any) -> datetime | None:
    """Coerce the grouping sort-key back to a datetime for the schema, if possible."""
    if ts is None or ts == "":
        return None
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromisoformat(str(ts))
    except (ValueError, TypeError):
        return None


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
