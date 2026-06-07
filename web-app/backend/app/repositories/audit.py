"""DB operations for AuditLog -- the compliance/security event log.

record_event() is called INSIDE a mutation's transaction (db.add + flush); the
caller's db.commit() then persists the domain change and its audit row
atomically. list_recent() powers the /admin Activity view.
"""
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import AuditLog


def record_event(
    db: Session,
    *,
    user_id: UUID | None,
    organization_id: UUID | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: Any | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Insert an audit row. Caller commits (usually with the mutation)."""
    event = AuditLog(
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    db.flush()
    return event


def list_recent(
    db: Session,
    *,
    limit: int = 50,
    action_prefix: str | None = None,
) -> list[AuditLog]:
    """Most-recent audit events, newest first, with the actor eager-loaded.

    action_prefix filters to a family (e.g. 'admin.') when set.
    """
    stmt = select(AuditLog).options(joinedload(AuditLog.user))
    if action_prefix:
        stmt = stmt.where(AuditLog.action.like(f"{action_prefix}%"))
    stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit)
    return list(db.scalars(stmt).unique().all())


def list_for_org(
    db: Session,
    organization_id: UUID,
    *,
    limit: int = 50,
) -> list[AuditLog]:
    """Most-recent events for ONE organization, newest first, actor eager-loaded.

    Powers the /settings Activity view (org-scoped, all action families).
    """
    stmt = (
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .options(joinedload(AuditLog.user))
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )
    return list(db.scalars(stmt).unique().all())
