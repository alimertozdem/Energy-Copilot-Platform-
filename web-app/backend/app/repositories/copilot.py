"""DB operations for CopilotConversation + CopilotMessage.

Thin repository: each function wraps one SQLAlchemy query or persist.
Authorization (user_id ownership) is enforced inside every read/write
so callers can't accidentally leak another user's conversation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.building import Building
from app.db.models.copilot import CopilotConversation, CopilotMessage


def create_conversation(
    db: Session,
    *,
    user_id: UUID,
    organization_id: UUID,
    title: str,
    fabric_building_id: str | None = None,
    provider: str = "claude",
    model: str | None = None,
) -> CopilotConversation:
    """Create + persist a new conversation row.

    When `fabric_building_id` is given, we look up the matching Building
    UUID in Postgres so the FK is populated. If the building isn't
    registered (sample data or pending onboarding), building_id stays NULL.
    """
    building_uuid: UUID | None = None
    if fabric_building_id:
        bldg = db.scalar(
            select(Building).where(Building.fabric_building_id == fabric_building_id)
        )
        if bldg is not None:
            building_uuid = bldg.id

    conv = CopilotConversation(
        id=uuid4(),
        user_id=user_id,
        organization_id=organization_id,
        building_id=building_uuid,
        title=title,
        provider=provider,
        model=model,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def list_conversations_for_user(
    db: Session,
    *,
    user_id: UUID,
    limit: int = 50,
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    """Return the user's recent conversations as plain dicts.

    Output shape includes the joined fabric_building_id so the response
    DTO can be filled in one DB round-trip instead of two.
    """
    stmt = (
        select(CopilotConversation, Building.fabric_building_id)
        .outerjoin(Building, CopilotConversation.building_id == Building.id)
        .where(CopilotConversation.user_id == user_id)
    )
    if not include_archived:
        stmt = stmt.where(CopilotConversation.is_archived.is_(False))
    stmt = stmt.order_by(
        desc(CopilotConversation.last_message_at.is_(None)),
        desc(CopilotConversation.last_message_at),
        desc(CopilotConversation.created_at),
    ).limit(limit)

    rows = db.execute(stmt).all()
    return [
        {
            "id": conv.id,
            "title": conv.title,
            "provider": conv.provider,
            "model": conv.model,
            "fabric_building_id": fab_id,
            "is_archived": conv.is_archived,
            "last_message_at": conv.last_message_at,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
        }
        for conv, fab_id in rows
    ]


def get_conversation_for_user(
    db: Session,
    *,
    conversation_id: UUID,
    user_id: UUID,
) -> CopilotConversation | None:
    """Return a conversation iff it belongs to this user. None on missing/forbidden.

    Conflates 404 + 403 to prevent enumeration leaks (same pattern as buildings).
    """
    stmt = (
        select(CopilotConversation)
        .where(CopilotConversation.id == conversation_id)
        .where(CopilotConversation.user_id == user_id)
        .options(selectinload(CopilotConversation.messages))
    )
    return db.scalar(stmt)


def get_conversation_with_building(
    db: Session,
    *,
    conversation_id: UUID,
    user_id: UUID,
) -> tuple[CopilotConversation, str | None] | None:
    """Same as get_conversation_for_user but also returns fabric_building_id."""
    stmt = (
        select(CopilotConversation, Building.fabric_building_id)
        .outerjoin(Building, CopilotConversation.building_id == Building.id)
        .where(CopilotConversation.id == conversation_id)
        .where(CopilotConversation.user_id == user_id)
    )
    row = db.execute(stmt).first()
    if row is None:
        return None
    return row[0], row[1]


def list_messages(
    db: Session,
    *,
    conversation_id: UUID,
) -> list[CopilotMessage]:
    """Return all messages in a conversation, ordered by created_at ASC."""
    stmt = (
        select(CopilotMessage)
        .where(CopilotMessage.conversation_id == conversation_id)
        .order_by(CopilotMessage.created_at)
    )
    return list(db.scalars(stmt).all())


def append_message(
    db: Session,
    *,
    conversation_id: UUID,
    role: str,
    content: str | None = None,
    tool_calls: list[dict[str, Any]] | dict[str, Any] | None = None,
    tool_call_id: str | None = None,
    tool_name: str | None = None,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
    latency_ms: int | None = None,
) -> CopilotMessage:
    """Insert one message and bump the conversation's last_message_at."""
    msg = CopilotMessage(
        id=uuid4(),
        conversation_id=conversation_id,
        role=role,
        content=content,
        tool_calls=tool_calls,
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        latency_ms=latency_ms,
    )
    db.add(msg)
    # Bump conversation activity timestamp.
    conv = db.get(CopilotConversation, conversation_id)
    if conv is not None:
        conv.last_message_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(msg)
    return msg


def append_messages_bulk(
    db: Session,
    *,
    conversation_id: UUID,
    messages: Iterable[dict[str, Any]],
) -> list[CopilotMessage]:
    """Insert multiple messages atomically (single commit).

    Used by the orchestrator after a tool-use turn — the assistant message
    plus N tool_result messages are persisted together.
    """
    rows: list[CopilotMessage] = []
    for m in messages:
        rows.append(
            CopilotMessage(
                id=uuid4(),
                conversation_id=conversation_id,
                role=m["role"],
                content=m.get("content"),
                tool_calls=m.get("tool_calls"),
                tool_call_id=m.get("tool_call_id"),
                tool_name=m.get("tool_name"),
                tokens_input=m.get("tokens_input"),
                tokens_output=m.get("tokens_output"),
                latency_ms=m.get("latency_ms"),
            )
        )
    db.add_all(rows)
    conv = db.get(CopilotConversation, conversation_id)
    if conv is not None:
        conv.last_message_at = datetime.now(timezone.utc)
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows
