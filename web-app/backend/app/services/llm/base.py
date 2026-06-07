"""LLM Provider abstraction — streaming chat with tool use.

Design notes:
    1. Provider streams a SINGLE model turn (one round-trip). The tool-use
       loop runs at the orchestrator layer (routers/copilot.py) so the
       provider stays DB-agnostic — no user_id / visibility filter / Fabric
       SQL knowledge here.

    2. StreamEvent is LLM-agnostic. Each provider maps its native event
       stream into these normalized types so the orchestrator + frontend
       speak one protocol.

    3. ToolDefinition uses JSON Schema (Anthropic's input_schema spec).
       Providers translate to their own format if needed (e.g. OpenAI's
       function.parameters).

    4. AsyncIterator + async generator pattern — required for FastAPI SSE
       streaming endpoints.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal


@dataclass(frozen=True)
class ToolDefinition:
    """LLM-agnostic tool schema.

    Fields:
        name:         Unique tool name (e.g. "query_kpi"). Used in tool
                      dispatcher routing.
        description:  Natural-language description shown to the LLM. Be
                      specific — this is how the model decides when to
                      call the tool.
        input_schema: JSON Schema dict describing tool arguments. Matches
                      Anthropic's `input_schema` field 1:1.
    """

    name: str
    description: str
    input_schema: dict[str, Any]


EventType = Literal[
    "text_delta",            # streaming assistant text chunk
    "tool_use_start",        # model began emitting a tool_use block
    "tool_use_input_delta",  # tool args JSON streaming in (partial)
    "tool_use_end",          # tool_use block complete, full parsed input ready
    "message_complete",      # turn finished — final meta in event.data
    "error",                 # provider-level error mid-stream
]


@dataclass(frozen=True)
class StreamEvent:
    """Normalized event emitted from LLMProvider.chat_stream().

    The final event of every successful stream is always type=message_complete,
    with data containing:
        {
            "stop_reason": str,        # 'end_turn' | 'tool_use' | 'max_tokens'
            "text": str,               # accumulated assistant text
            "tool_uses": list[dict],   # [{"id", "name", "input"}, ...]
            "tokens_input": int,
            "tokens_output": int,
        }

    The orchestrator inspects stop_reason to decide whether to loop
    (tool_use → run dispatcher → feed tool_result back → re-call chat_stream)
    or terminate (end_turn → persist + return to client).
    """

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract LLM provider.

    Subclass contract:
        - chat_stream() is an async generator yielding StreamEvents.
        - The LAST yielded event MUST be type=message_complete with full
          meta in data (stop_reason, text, tool_uses, tokens_*).
        - Tool-use loop is NOT the provider's responsibility. Provider
          emits tool_use_end with parsed input; orchestrator decides
          whether to call the dispatcher and start another turn.
        - All errors mid-stream should yield a StreamEvent(type="error",
          data={"message": str}) then return.
    """

    @abstractmethod
    async def chat_stream(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamEvent]:
        """Stream a single model turn.

        Args:
            system:     System prompt (role-style instructions). Not stored
                        in DB — template-driven at orchestrator layer.
            messages:   Conversation history in provider-native format.
                        For Anthropic: [{"role": "user"|"assistant",
                        "content": str | list[content_block]}].
            tools:      Available tools for this turn. None = pure chat.
            model:      Override default model.
            max_tokens: Max tokens for assistant response.

        Yields:
            StreamEvent for each parsed delta. Final event always
            type=message_complete with full meta.
        """
        ...
        # Required to make this an async generator stub for type checking.
        if False:  # pragma: no cover
            yield StreamEvent(type="error", data={})

    @property
    @abstractmethod
    def default_model(self) -> str:
        """The model used when chat_stream() called without `model` arg."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Short identifier persisted in copilot_conversations.provider."""
        ...
