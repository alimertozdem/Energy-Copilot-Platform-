"""Pydantic schemas for the /copilot router.

Wire format only — these are request/response DTOs, not DB models. The
SQLAlchemy CopilotConversation/CopilotMessage models live in
app/db/models/copilot.py.
"""
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ----- Requests --------------------------------------------------------


class ConversationCreateRequest(BaseModel):
    """Body for POST /copilot/conversations.

    All fields optional — caller can create an empty thread and post the
    first message separately, or open with a building context.
    """

    title: str | None = Field(
        default=None,
        max_length=255,
        description="Display title. Auto-generated from first user message when omitted.",
    )
    fabric_building_id: str | None = Field(
        default=None,
        max_length=100,
        description=(
            "Optional building context. When set, the copilot defaults to "
            "discussing this building. NULL = portfolio-level chat."
        ),
    )


class MessageCreateRequest(BaseModel):
    """Body for POST /copilot/conversations/{id}/messages."""

    content: str = Field(min_length=1, max_length=10_000)


# ----- Responses -------------------------------------------------------


class MessageItem(BaseModel):
    """One message in a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: Literal["user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[dict[str, Any]] | dict[str, Any] | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    latency_ms: int | None = None
    created_at: datetime


class ConversationItem(BaseModel):
    """One row in the conversation list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    provider: str
    model: str | None = None
    fabric_building_id: str | None = Field(
        default=None,
        description="Joined from buildings table for convenience. NULL = portfolio-level.",
    )
    is_archived: bool
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    conversations: list[ConversationItem]


class ConversationDetail(ConversationItem):
    """Conversation header + ordered message list (GET /conversations/{id})."""

    messages: list[MessageItem]


class ConversationCreatedResponse(BaseModel):
    """Returned from POST /conversations."""

    id: UUID
    title: str
