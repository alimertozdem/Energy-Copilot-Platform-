"""Anthropic Claude LLM provider — streaming + tool use.

Maps Anthropic's native event stream (content_block_start /
content_block_delta / content_block_stop / message_stop) to our
normalized StreamEvent type.

Reference: https://docs.anthropic.com/en/api/messages-streaming
"""
from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator

from anthropic import AsyncAnthropic

from app.services.llm.base import LLMProvider, StreamEvent, ToolDefinition


DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider(LLMProvider):
    """Concrete LLMProvider backed by Anthropic's Python SDK.

    Env:
        ANTHROPIC_API_KEY (required) — created at
            https://console.anthropic.com/settings/keys.

    Cost (2026-05 pricing, claude-sonnet-4-6):
        $3 / 1M input tokens
        $15 / 1M output tokens
        Average copilot turn: ~2K input + ~500 output = ~$0.013 / turn
        Average 5-turn conversation: ~$0.065
    """

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Add it to web-app/backend/.env "
                "and restart uvicorn. Get a key at "
                "https://console.anthropic.com/settings/keys"
            )
        self._client = AsyncAnthropic(api_key=key)

    @property
    def default_model(self) -> str:
        return DEFAULT_MODEL

    @property
    def provider_name(self) -> str:
        return "claude"

    async def chat_stream(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamEvent]:
        # Translate our ToolDefinition list to Anthropic's tool format.
        anthropic_tools = (
            [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema,
                }
                for t in tools
            ]
            if tools
            else []
        )

        # Per-turn accumulators.
        accumulated_text = ""
        tool_uses: list[dict[str, Any]] = []
        current_tool: dict[str, Any] | None = None
        current_tool_json_buffer = ""

        try:
            async with self._client.messages.stream(
                model=model or DEFAULT_MODEL,
                system=system,
                messages=messages,
                tools=anthropic_tools if anthropic_tools else None,  # SDK: omit if empty
                max_tokens=max_tokens,
            ) as stream:
                async for event in stream:
                    etype = getattr(event, "type", None)

                    # ---- text + tool_use block START ----
                    if etype == "content_block_start":
                        block = event.content_block
                        if block.type == "tool_use":
                            current_tool = {
                                "id": block.id,
                                "name": block.name,
                            }
                            current_tool_json_buffer = ""
                            yield StreamEvent(
                                type="tool_use_start",
                                data={
                                    "tool_use_id": block.id,
                                    "name": block.name,
                                },
                            )
                        # text block start — nothing to emit, text comes via deltas

                    # ---- text / tool_use_input DELTA ----
                    elif etype == "content_block_delta":
                        delta = event.delta
                        dtype = getattr(delta, "type", None)
                        if dtype == "text_delta":
                            chunk = delta.text
                            accumulated_text += chunk
                            yield StreamEvent(
                                type="text_delta",
                                data={"text": chunk},
                            )
                        elif dtype == "input_json_delta":
                            partial = delta.partial_json
                            current_tool_json_buffer += partial
                            yield StreamEvent(
                                type="tool_use_input_delta",
                                data={"partial_json": partial},
                            )

                    # ---- block STOP ----
                    elif etype == "content_block_stop":
                        if current_tool is not None:
                            # Finalize tool_use block: parse buffered JSON.
                            try:
                                parsed_input = (
                                    json.loads(current_tool_json_buffer)
                                    if current_tool_json_buffer
                                    else {}
                                )
                            except json.JSONDecodeError:
                                parsed_input = {}
                            full_tool = {
                                "id": current_tool["id"],
                                "name": current_tool["name"],
                                "input": parsed_input,
                            }
                            tool_uses.append(full_tool)
                            yield StreamEvent(
                                type="tool_use_end",
                                data=full_tool,
                            )
                            current_tool = None
                            current_tool_json_buffer = ""

                    # message_stop carries usage stats — we capture final message below

                # Stream context exited cleanly — pull final message for usage stats.
                final = await stream.get_final_message()
                stop_reason = getattr(final, "stop_reason", "end_turn") or "end_turn"
                usage = getattr(final, "usage", None)
                tokens_input = getattr(usage, "input_tokens", 0) if usage else 0
                tokens_output = getattr(usage, "output_tokens", 0) if usage else 0

                yield StreamEvent(
                    type="message_complete",
                    data={
                        "stop_reason": stop_reason,
                        "text": accumulated_text,
                        "tool_uses": tool_uses,
                        "tokens_input": tokens_input,
                        "tokens_output": tokens_output,
                    },
                )

        except Exception as exc:  # noqa: BLE001 — surface to orchestrator
            yield StreamEvent(
                type="error",
                data={
                    "message": f"{type(exc).__name__}: {exc}",
                },
            )
