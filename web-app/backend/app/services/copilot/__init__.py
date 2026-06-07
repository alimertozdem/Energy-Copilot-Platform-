"""Copilot service package — tool definitions + dispatcher.

Public API:
    from app.services.copilot import (
        TOOL_DEFINITIONS,   # list[ToolDefinition] — feed to LLMProvider.chat_stream
        dispatch_tool,      # (tool_name, tool_input, ctx) -> dict (tool_result body)
        ToolContext,        # auth + DB handles bundle passed to each handler
    )
"""
from app.services.copilot.dispatcher import (
    ToolContext,
    dispatch_tool,
)
from app.services.copilot.tools import TOOL_DEFINITIONS

__all__ = [
    "TOOL_DEFINITIONS",
    "ToolContext",
    "dispatch_tool",
]
