"""Copilot router — 4 endpoints driving /copilot in the frontend.

  GET    /copilot/conversations              -- list (recent first)
  POST   /copilot/conversations              -- create empty thread
  GET    /copilot/conversations/{id}         -- header + full message history
  POST   /copilot/conversations/{id}/messages -- send user msg, SSE stream

Authentication: same JWT bearer as /buildings and /portfolio.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import copilot as copilot_repo
from app.schemas.copilot import (
    ConversationCreatedResponse,
    ConversationCreateRequest,
    ConversationDetail,
    ConversationItem,
    ConversationListResponse,
    MessageCreateRequest,
    MessageItem,
)
from app.services.copilot.orchestrator import sse_event, stream_assistant_response
from app.utils.jwt import (
    bearer_scheme,
    decode_access_token,
    get_current_user_id,
)

router = APIRouter(prefix="/copilot", tags=["copilot"])


def _get_user_and_org(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> tuple[UUID, UUID]:
    """Pull user_id + organization_id out of the JWT.

    The JWT issued by /auth/login already carries org_id (the user's personal
    workspace at signup). We trust it rather than re-querying Postgres on
    every request — same pattern as get_current_user_id.
    """
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing Authorization header")
    claims = decode_access_token(credentials.credentials)
    try:
        org_id = UUID(claims["org_id"])
    except (KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing valid 'org_id' claim")
    return user_id, org_id


# ----- GET /conversations ----------------------------------------------


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    user_and_org: Annotated[tuple[UUID, UUID], Depends(_get_user_and_org)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
    include_archived: bool = False,
) -> ConversationListResponse:
    user_id, _ = user_and_org
    rows = copilot_repo.list_conversations_for_user(
        db,
        user_id=user_id,
        limit=limit,
        include_archived=include_archived,
    )
    return ConversationListResponse(
        conversations=[ConversationItem(**r) for r in rows]
    )


# ----- POST /conversations ---------------------------------------------


@router.post(
    "/conversations",
    response_model=ConversationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    body: ConversationCreateRequest,
    user_and_org: Annotated[tuple[UUID, UUID], Depends(_get_user_and_org)],
    db: Annotated[Session, Depends(get_db)],
) -> ConversationCreatedResponse:
    user_id, org_id = user_and_org

    # Title: caller-provided OR a placeholder. Auto-titling from the first
    # user message is a V1.5 polish (extra Claude call after first turn).
    title = (body.title or "New Chat").strip()[:255]

    conv = copilot_repo.create_conversation(
        db,
        user_id=user_id,
        organization_id=org_id,
        title=title,
        fabric_building_id=body.fabric_building_id,
    )
    return ConversationCreatedResponse(id=conv.id, title=conv.title)


# ----- GET /conversations/{id} -----------------------------------------


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: UUID,
    user_and_org: Annotated[tuple[UUID, UUID], Depends(_get_user_and_org)],
    db: Annotated[Session, Depends(get_db)],
) -> ConversationDetail:
    user_id, _ = user_and_org
    looked_up = copilot_repo.get_conversation_with_building(
        db, conversation_id=conversation_id, user_id=user_id,
    )
    if looked_up is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found.")
    conv, fab_id = looked_up
    messages = copilot_repo.list_messages(db, conversation_id=conversation_id)
    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        provider=conv.provider,
        model=conv.model,
        fabric_building_id=fab_id,
        is_archived=conv.is_archived,
        last_message_at=conv.last_message_at,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageItem.model_validate(m) for m in messages],
    )


# ----- POST /conversations/{id}/messages  (SSE) ------------------------


@router.post("/conversations/{conversation_id}/messages")
async def post_message(
    conversation_id: UUID,
    body: MessageCreateRequest,
    user_and_org: Annotated[tuple[UUID, UUID], Depends(_get_user_and_org)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Send a user message and stream the assistant's response via SSE.

    Response content-type: text/event-stream. Events:

      event: user_message_persisted    -- {"id": "<uuid>"}
      event: text                      -- {"text": "<chunk>"}
      event: tool_call_start           -- {"tool_use_id", "name"}
      event: tool_call                 -- {"tool", "tool_use_id", "input"}
      event: tool_result               -- {"tool", "tool_use_id", "result_preview", "is_error"}
      event: complete                  -- {"message_id", "stop_reason", "tokens_input", "tokens_output"}
      event: error                     -- {"message"}
    """
    user_id, org_id = user_and_org

    # Verify access before opening the stream — return a clean 404 instead
    # of starting the SSE and emitting an error event (less surprising).
    looked_up = copilot_repo.get_conversation_with_building(
        db, conversation_id=conversation_id, user_id=user_id,
    )
    if looked_up is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found.")

    async def event_stream():
        try:
            async for chunk in stream_assistant_response(
                db,
                conversation_id=conversation_id,
                user_id=user_id,
                organization_id=org_id,
                user_message=body.content,
            ):
                yield chunk
        except Exception as exc:  # noqa: BLE001 — last-resort safety
            yield sse_event("error", {
                "message": f"Stream aborted: {type(exc).__name__}: {exc}",
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # disable nginx/proxy buffering
            "Connection": "keep-alive",
        },
    )
