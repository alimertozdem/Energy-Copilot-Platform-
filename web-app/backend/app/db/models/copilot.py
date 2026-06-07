"""CopilotConversation and CopilotMessage models -- AI chat history.

Pattern:
    Standard chat-thread (ChatGPT/Claude style):
        Conversation = thread with metadata (user, org, building context)
        Message      = one entry in the thread (user / assistant / tool roles)

Tool use:
    Tool invocations are structured. 'assistant' messages may include
    tool_calls (JSONB), and matching 'tool' messages reference them via
    tool_call_id. Mirrors the Anthropic / OpenAI tool-use schemas.

Token tracking:
    tokens_input + tokens_output let us roll up monthly LLM cost per user,
    enforce per-tier limits (e.g. free=10k/month), and detect abuse.

System prompts:
    NOT stored in DB -- 'system' role is template-driven at the backend
    layer (LLMProvider class). Only user/assistant/tool persisted.
"""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class CopilotConversation(Base, TimestampMixin):
    """A user's chat thread with the EnergyLens AI copilot."""

    __tablename__ = "copilot_conversations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Optional building context ("analyze B001"). NULL = portfolio-level chat.
    building_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Auto-generated from first message via LLM (Day 14+ implementation).
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # 'claude' | 'azure_openai'
    provider: Mapped[str] = mapped_column(
        String(20),
        default="claude",
        nullable=False,
    )
    # e.g. "claude-sonnet-4-6"
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship()  # noqa: F821
    organization: Mapped["Organization"] = relationship()  # noqa: F821
    building: Mapped["Building | None"] = relationship()  # noqa: F821
    messages: Mapped[list["CopilotMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="CopilotMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<CopilotConversation {self.id} '{self.title}'>"


class CopilotMessage(Base, TimestampMixin):
    """A single message in a copilot conversation.

    Roles:
      - 'user'      --> what the human typed
      - 'assistant' --> LLM response (may include tool_calls JSONB)
      - 'tool'      --> output of a tool execution (references tool_call_id)
    """

    __tablename__ = "copilot_messages"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("copilot_conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # 'user' | 'assistant' | 'tool'
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Structured tool invocations (assistant messages may have these).
    tool_calls: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    # For role='tool': which assistant tool_call this message answers.
    tool_call_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # LLM cost & performance tracking.
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    conversation: Mapped["CopilotConversation"] = relationship(
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<CopilotMessage {self.role} in {self.conversation_id}>"
