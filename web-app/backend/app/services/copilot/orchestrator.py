"""Copilot orchestrator — drives the tool-use loop and yields SSE events.

The LLMProvider abstraction streams a SINGLE turn. The orchestrator runs the
multi-turn loop:

    1. Build the Anthropic-format message list from DB history.
    2. Stream the model's response — yield text deltas as SSE events.
    3. On message_complete:
         * stop_reason == "tool_use"  →  dispatch each tool, build a
                                          tool_result user message, loop.
         * otherwise (end_turn etc.)  →  emit `complete` SSE event, return.
    4. Hard cap at MAX_ITERATIONS to prevent runaway tool calls.

Persistence:
    Each message (user, assistant, tool) is written to Postgres in real time
    so the conversation state is durable even if the SSE stream breaks. The
    same DB rows feed the GET /conversations/{id} history endpoint.

Authorization:
    visible_building_ids is resolved once at stream start from the same
    repository the /buildings and /portfolio endpoints use — single source
    of truth for "what can this user see".
"""
from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, timezone
from typing import Any, AsyncIterator
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.building import Building
from app.db.models.copilot import CopilotMessage
from app.repositories import building as building_repo
from app.repositories import copilot as copilot_repo
from app.services.copilot.dispatcher import ToolContext, dispatch_tool
from app.services.copilot.tools import TOOL_DEFINITIONS
from app.services.llm import get_llm_provider

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5
TOOL_RESULT_PREVIEW_CHARS = 400


# ----- SSE helpers -----------------------------------------------------


def sse_event(event_name: str, data: dict[str, Any]) -> str:
    """Format one Server-Sent Event chunk.

    Spec: https://html.spec.whatwg.org/multipage/server-sent-events.html
    """
    payload = json.dumps(data, default=_json_default)
    return f"event: {event_name}\ndata: {payload}\n\n"


def _json_default(o: Any) -> Any:
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, UUID):
        return str(o)
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def _preview(result_data: dict[str, Any]) -> str:
    """Compact JSON preview of a tool_result for the SSE 'tool_result' event."""
    try:
        s = json.dumps(result_data, default=_json_default)
    except Exception:  # noqa: BLE001
        return "<unserializable>"
    if len(s) <= TOOL_RESULT_PREVIEW_CHARS:
        return s
    return s[:TOOL_RESULT_PREVIEW_CHARS] + "…"


# ----- DB ↔ Anthropic message conversion -------------------------------


def _db_to_anthropic(messages: list[CopilotMessage]) -> list[dict[str, Any]]:
    """Convert a flat list of CopilotMessage rows into Anthropic-format messages.

    Rules:
      * Consecutive 'tool' role messages collapse into ONE user message
        whose content is a list of tool_result blocks (Anthropic requires
        all tool_results for one assistant turn to be in one user message).
      * 'assistant' rows with tool_calls become content blocks
        (text + tool_use), otherwise plain string content.
      * 'user' rows become plain string content.
    """
    out: list[dict[str, Any]] = []
    pending_tool_results: list[dict[str, Any]] = []

    def flush_pending():
        nonlocal pending_tool_results
        if pending_tool_results:
            out.append({"role": "user", "content": pending_tool_results})
            pending_tool_results = []

    for m in messages:
        if m.role == "tool":
            pending_tool_results.append({
                "type": "tool_result",
                "tool_use_id": m.tool_call_id or "",
                "content": m.content or "",
            })
            continue

        # Non-tool row → flush any pending tool_results first
        flush_pending()

        if m.role == "user":
            out.append({"role": "user", "content": m.content or ""})
        elif m.role == "assistant":
            tool_calls = m.tool_calls or []
            # tool_calls can be a list or a dict (single call) — normalize.
            if isinstance(tool_calls, dict):
                tool_calls = [tool_calls]

            if not tool_calls:
                out.append({"role": "assistant", "content": m.content or ""})
            else:
                blocks: list[dict[str, Any]] = []
                if m.content:
                    blocks.append({"type": "text", "text": m.content})
                for tc in tool_calls:
                    blocks.append({
                        "type": "tool_use",
                        "id": tc.get("id"),
                        "name": tc.get("name"),
                        "input": tc.get("input") or {},
                    })
                out.append({"role": "assistant", "content": blocks})

    flush_pending()
    return out


# ----- System prompt ---------------------------------------------------


def _build_system_prompt(
    visible_buildings: list[Building],
    focus_building_id: str | None,
) -> str:
    """Construct the system message handed to the model on every turn.

    Includes:
      * Mission framing — energy management assistant
      * Tool-use directive — never invent numbers
      * The user's accessible portfolio (up to 30 buildings inline)
      * Today's ISO date (so the model can resolve relative dates)
      * Optional focus building when the chat is per-building scoped
    """
    today_iso = datetime.now(timezone.utc).date().isoformat()

    # Compact portfolio summary — fabric_id + name + city + type
    rows = []
    for b in visible_buildings[:30]:
        bits = [b.fabric_building_id or "?", b.name or "(unnamed)"]
        if b.city:
            bits.append(b.city)
        if b.building_type:
            bits.append(b.building_type)
        rows.append(" — ".join(bits))
    portfolio_block = "\n".join(f"  • {r}" for r in rows) if rows else "  (no buildings visible)"
    if len(visible_buildings) > 30:
        portfolio_block += f"\n  • …and {len(visible_buildings) - 30} more"

    focus_block = ""
    if focus_building_id:
        focus_block = (
            f"\nThis conversation is focused on building {focus_building_id}. "
            "Unless the user names another building, assume questions are about it.\n"
        )

    return f"""You are EnergyLens Copilot, an AI assistant for commercial building \
energy management. You help facility and energy managers understand \
consumption patterns, identify anomalies, prioritize improvement \
recommendations, and plan battery storage investments.

TOOL-USE DIRECTIVE
You have access to {len(TOOL_DEFINITIONS)} tools that query the user's \
portfolio data. When asked about specific buildings, metrics, anomalies, \
recommendations, or battery scenarios — USE THE TOOLS. Never invent \
numbers. After receiving tool results, cite the data naturally \
("Based on the last 30 days of consumption data...").

PORTFOLIO ACCESS
The user can see the following buildings:
{portfolio_block}
{focus_block}
RESPONSE STYLE
* Be concise. One short paragraph beats five long ones.
* Format numbers with units (kWh, EUR, kg CO₂e, kWh/m²/year).
* Show direction on deltas with arrows (↓22% lower, ↑5% higher).
* When data is unavailable, say so honestly — never fabricate values.
* Always reply in the language the user used.

CONTEXT
Today's date: {today_iso}
"""


# ----- Main entry point ------------------------------------------------


async def stream_assistant_response(
    db: Session,
    *,
    conversation_id: UUID,
    user_id: UUID,
    organization_id: UUID,
    user_message: str,
) -> AsyncIterator[str]:
    """Run one user-turn through the tool-use loop, yielding SSE event chunks.

    Caller passes this directly into a FastAPI StreamingResponse. Each yielded
    string is already SSE-formatted (event: ... \\n data: ... \\n\\n).
    """
    # ---- 1. Auth + conversation load ----
    looked_up = copilot_repo.get_conversation_with_building(
        db, conversation_id=conversation_id, user_id=user_id,
    )
    if looked_up is None:
        yield sse_event("error", {"message": "Conversation not found or not accessible."})
        return
    conversation, focus_fab_id = looked_up

    # ---- 2. Resolve visible buildings (auth boundary) ----
    visible_buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    visible_fab_ids = [b.fabric_building_id for b in visible_buildings if b.fabric_building_id]

    ctx = ToolContext(
        user_id=user_id,
        organization_id=organization_id,
        visible_building_ids=visible_fab_ids,
        db=db,
    )

    # ---- 3. Persist the user message + load full history ----
    user_db_msg = copilot_repo.append_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=user_message,
    )
    yield sse_event("user_message_persisted", {"id": str(user_db_msg.id)})

    history = copilot_repo.list_messages(db, conversation_id=conversation_id)
    anthropic_messages = _db_to_anthropic(history)

    # ---- 4. Tool-use loop ----
    system = _build_system_prompt(visible_buildings, focus_fab_id)
    provider = get_llm_provider()

    for iteration in range(MAX_ITERATIONS):
        turn_started_at = time.monotonic()
        assistant_text = ""
        tool_uses: list[dict[str, Any]] = []
        final_meta: dict[str, Any] | None = None
        errored = False

        async for event in provider.chat_stream(
            system=system,
            messages=anthropic_messages,
            tools=TOOL_DEFINITIONS,
            model=conversation.model or provider.default_model,
        ):
            if event.type == "text_delta":
                assistant_text += event.data.get("text", "")
                yield sse_event("text", event.data)

            elif event.type == "tool_use_start":
                yield sse_event("tool_call_start", event.data)

            elif event.type == "tool_use_end":
                tu = {
                    "id": event.data["id"],
                    "name": event.data["name"],
                    "input": event.data.get("input", {}),
                }
                tool_uses.append(tu)
                yield sse_event("tool_call", {
                    "tool": tu["name"],
                    "tool_use_id": tu["id"],
                    "input": tu["input"],
                })

            elif event.type == "message_complete":
                final_meta = event.data

            elif event.type == "error":
                yield sse_event("error", event.data)
                errored = True
                break

        if errored:
            return

        if final_meta is None:
            yield sse_event("error", {"message": "Stream ended without message_complete event."})
            return

        latency_ms = int((time.monotonic() - turn_started_at) * 1000)
        stop_reason = final_meta.get("stop_reason", "end_turn")

        # ---- Persist assistant turn ----
        assistant_db = copilot_repo.append_message(
            db,
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_text or None,
            tool_calls=tool_uses if tool_uses else None,
            tokens_input=final_meta.get("tokens_input"),
            tokens_output=final_meta.get("tokens_output"),
            latency_ms=latency_ms,
        )

        # ---- Update conversation.model on first turn ----
        if conversation.model is None:
            conversation.model = provider.default_model
            db.commit()

        # ---- Decide: loop again or terminate? ----
        if stop_reason == "tool_use" and tool_uses:
            # Append assistant message (with tool_use blocks) to anthropic_messages
            assistant_blocks: list[dict[str, Any]] = []
            if assistant_text:
                assistant_blocks.append({"type": "text", "text": assistant_text})
            for tu in tool_uses:
                assistant_blocks.append({
                    "type": "tool_use",
                    "id": tu["id"],
                    "name": tu["name"],
                    "input": tu["input"],
                })
            anthropic_messages.append({"role": "assistant", "content": assistant_blocks})

            # Execute tools + persist tool_result messages + build next-turn user message
            tool_result_blocks: list[dict[str, Any]] = []
            for tu in tool_uses:
                result_data = dispatch_tool(tu["name"], tu["input"], ctx)
                result_json = json.dumps(result_data, default=_json_default)

                copilot_repo.append_message(
                    db,
                    conversation_id=conversation_id,
                    role="tool",
                    content=result_json,
                    tool_call_id=tu["id"],
                    tool_name=tu["name"],
                )

                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": result_json,
                })

                yield sse_event("tool_result", {
                    "tool": tu["name"],
                    "tool_use_id": tu["id"],
                    "result_preview": _preview(result_data),
                    "is_error": "error" in result_data,
                })

            anthropic_messages.append({"role": "user", "content": tool_result_blocks})
            # ↻ loop continues into next turn

        else:
            # Terminal — end_turn, max_tokens, or other non-tool-use stop
            yield sse_event("complete", {
                "message_id": str(assistant_db.id),
                "stop_reason": stop_reason,
                "tokens_input": final_meta.get("tokens_input"),
                "tokens_output": final_meta.get("tokens_output"),
                "latency_ms": latency_ms,
            })
            return

    # ---- Loop hit MAX_ITERATIONS ----
    logger.warning(
        "Copilot hit MAX_ITERATIONS (%d) for conversation %s",
        MAX_ITERATIONS, conversation_id,
    )
    yield sse_event("complete", {
        "message_id": None,
        "stop_reason": "max_iterations",
        "warning": f"Hit max tool-use iterations ({MAX_ITERATIONS}).",
    })
