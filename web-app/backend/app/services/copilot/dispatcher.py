"""Tool dispatcher — routes LLM tool_use calls to handler functions.

Design notes:
    * Each handler is a pure-ish function that takes a ToolContext (auth +
      DB handles) + the LLM-supplied tool input (already parsed from JSON).
    * Handlers return a JSON-serializable dict that becomes the body of the
      `tool_result` content block sent back to the LLM.
    * Authorization is enforced *inside* each handler using
      ToolContext.visible_building_ids. Handlers MUST check that any
      building_id argument is in that set before querying — otherwise the
      LLM could hallucinate "B999" and read data the user can't see.
    * Errors are NEVER raised back to the orchestrator (would terminate the
      stream). They're wrapped as {"error": "..."} so the LLM can recover
      ("Sorry, that building isn't in your portfolio — here are the ones
      I can see...").
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.copilot.tools import TOOL_HANDLERS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolContext:
    """Per-turn auth + DB context passed to every tool handler.

    Fields:
        user_id:                Postgres users.id (UUID) of the requester.
        organization_id:        Active org for write tools (update_action_status).
        visible_building_ids:   List of fabric_building_id strings the user
                                can read. Authorization is enforced by every
                                handler against this list.
        db:                     SQLAlchemy session (for Postgres reads/writes —
                                e.g. recommendation_status). Fabric reads go
                                through fabric_sql.execute_query() directly.
    """

    user_id: UUID
    organization_id: UUID
    visible_building_ids: list[str]
    db: Session


def dispatch_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    ctx: ToolContext,
) -> dict[str, Any]:
    """Route a tool_use call to the matching handler and return its result.

    Never raises. Unknown tools, handler exceptions, and authorization
    failures all return {"error": "<message>"} so the LLM can continue.
    """
    handler: Callable[..., dict[str, Any]] | None = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return {
            "error": f"Unknown tool '{tool_name}'. Available tools: "
                     f"{', '.join(sorted(TOOL_HANDLERS.keys()))}"
        }

    try:
        result = handler(ctx=ctx, **tool_input)
        # Soft contract: handler returns a dict. Be defensive in case one
        # ever returns something else (e.g. a dataclass) — coerce or wrap.
        if not isinstance(result, dict):
            return {"result": result}
        return result
    except TypeError as exc:
        # LLM emitted bogus args (extra/missing keyword). Hand the message
        # back so it can retry with the correct schema.
        logger.warning(
            "Tool '%s' arg mismatch: input=%s err=%s",
            tool_name, tool_input, exc,
        )
        return {"error": f"Invalid arguments for {tool_name}: {exc}"}
    except Exception as exc:  # noqa: BLE001 — protect the stream
        logger.exception("Tool '%s' raised", tool_name)
        return {"error": f"{type(exc).__name__}: {exc}"}
