"""Mock LLM provider — keyword routing + simulated streaming.

Purpose:
    Frontend development without Anthropic credits. The orchestrator's
    full tool-use loop runs against this provider — Postgres and Fabric
    SQL are queried for real, and SSE events flow exactly as they would
    with Claude. Only the "language generation" part is simulated.

Selection:
    Set LLM_PROVIDER=mock in .env to activate (default: anthropic).

How it behaves:
    Turn 1 (no prior tool_result):
        Inspect the latest user message for keywords + building_id pattern
        (B001-B999). Emit a tool_use_start / tool_use_end pair for the
        best-matching tool. stop_reason='tool_use'.

    Turn 2 (orchestrator passed back a tool_result):
        Read the latest user message (which is now a list of tool_result
        blocks) and produce a one-paragraph summary citing the data.
        stop_reason='end_turn'.

    No tool keywords matched:
        Plain text reply. stop_reason='end_turn'.

The simulated text is intentionally short and templated — the value is
the round-trip + event format, not the prose.
"""
from __future__ import annotations

import json
import re
from typing import Any, AsyncIterator
from uuid import uuid4

from app.services.llm.base import LLMProvider, StreamEvent, ToolDefinition

BUILDING_ID_RE = re.compile(r"\bB\d{3}\b", re.IGNORECASE)

MODEL_NAME = "mock-claude-sonnet"


# ----- Tool routing heuristics -----------------------------------------


def _pick_tool(user_text: str) -> tuple[str, dict[str, Any]] | None:
    """Return (tool_name, input_dict) or None when no tool matches.

    Order matters — more specific keywords first.
    """
    text = user_text.lower()
    bldg_match = BUILDING_ID_RE.search(user_text)
    bldg_id = bldg_match.group().upper() if bldg_match else None

    # battery scenarios
    if any(k in text for k in ("battery", "batarya", "pil", "depolama", "storage")):
        if bldg_id:
            return "simulate_battery_scenario", {"building_id": bldg_id}

    # anomalies
    if any(k in text for k in ("anomali", "anomaly", "spike", "sapma")):
        if bldg_id:
            return "get_anomalies", {"building_id": bldg_id, "severity": "all", "days": 30}

    # recommendations
    if any(k in text for k in ("öneri", "recommendation", "suggest", "iyileştir", "öner")):
        if bldg_id:
            return "list_recommendations", {"building_id": bldg_id, "limit": 5}

    # compare
    if any(k in text for k in ("compare", "karşılaştır", "kıyas", "rank", "sırala", "worst", "best")):
        # extract all building IDs
        ids = [m.group().upper() for m in BUILDING_ID_RE.finditer(user_text)]
        if len(ids) >= 2:
            return "compare_buildings", {
                "building_ids": ids,
                "metric": "energy",
                "days": 30,
            }
        # ask for portfolio-wide compare
        return None

    # query_kpi default for any building mention + metric keyword
    metric = None
    if any(k in text for k in ("co2", "carbon", "karbon", "emisyon", "emission")):
        metric = "co2"
    elif any(k in text for k in ("maliyet", "cost", "eur", "fiyat", "para")):
        metric = "cost"
    elif any(k in text for k in ("eui", "kwh/m", "verim")):
        metric = "eui"
    elif any(k in text for k in ("tüket", "enerji", "energy", "kwh", "consumption")):
        metric = "energy"

    if bldg_id and metric:
        return "query_kpi", {"building_id": bldg_id, "metric": metric, "days": 30}
    if bldg_id:
        # default to energy when only building is mentioned
        return "query_kpi", {"building_id": bldg_id, "metric": "energy", "days": 30}

    return None


# ----- Tool result summarization ---------------------------------------


def _summarize_tool_result(tool_name: str, result: dict[str, Any]) -> str:
    """Produce a short human summary of a tool_result JSON dict."""
    if "error" in result:
        return f"Tool '{tool_name}' returned an error: {result['error']}"

    if tool_name == "query_kpi":
        name = result.get("building_name") or result.get("building_id")
        metric = result.get("metric")
        unit = result.get("unit")
        val = result.get("current_value")
        delta = result.get("delta_pct")
        delta_str = ""
        if delta is not None:
            arrow = "↓" if delta < 0 else "↑"
            delta_str = f" ({arrow}{abs(delta):.1f}% vs prior period)"
        return (
            f"{name}'s {metric} over the last {result.get('period_days', 30)} "
            f"days: {val:,.2f} {unit}{delta_str}."
        )

    if tool_name == "compare_buildings":
        ranked = result.get("ranked", [])
        unit = result.get("unit", "")
        if not ranked:
            return "No data available for the requested buildings."
        top = ranked[0]
        bot = ranked[-1] if len(ranked) > 1 else None
        line = (
            f"Highest: {top.get('building_name')} ({top.get('value'):,.2f} {unit})"
        )
        if bot is not None and bot is not top:
            line += f"; lowest: {bot.get('building_name')} ({bot.get('value'):,.2f} {unit})"
        return line + "."

    if tool_name == "list_recommendations":
        recs = result.get("recommendations", [])
        if not recs:
            return f"No open recommendations for building {result.get('building_id')}."
        top = recs[0]
        return (
            f"Found {len(recs)} recommendation(s). Highest-impact: "
            f"\"{top.get('title')}\" "
            f"(~{top.get('estimated_savings_eur', 0):,.0f} EUR/year savings)."
        )

    if tool_name == "get_anomalies":
        n = result.get("count", 0)
        by_sev = result.get("by_severity") or {}
        if n == 0:
            return f"No anomalies for building {result.get('building_id')} in the last 30 days."
        critical = by_sev.get("CRITICAL", 0)
        high = by_sev.get("HIGH", 0)
        return (
            f"{n} anomaly event(s) found"
            + (f", {critical} CRITICAL" if critical else "")
            + (f", {high} HIGH" if high else "")
            + "."
        )

    if tool_name == "simulate_battery_scenario":
        scenarios = result.get("scenarios", [])
        if not scenarios:
            return f"No battery simulation scenarios available for {result.get('building_id')}."
        best = scenarios[0]
        return (
            f"Best battery scenario: {best.get('chemistry')} with "
            f"{best.get('strategy')} strategy — "
            f"~{best.get('annual_savings_eur', 0):,.0f} EUR/year savings, "
            f"payback {best.get('payback_years', 0):.1f} years."
        )

    if tool_name == "update_action_status":
        if result.get("success"):
            return f"Status updated to '{result.get('new_status')}' for recommendation {result.get('fabric_recommendation_id')}."
        return "Status update did not succeed."

    return f"Tool '{tool_name}' completed."


# ----- The provider ----------------------------------------------------


class MockLLMProvider(LLMProvider):
    """Deterministic stand-in for AnthropicProvider.

    Implements the same chat_stream() contract — emits the same event
    types, in the same order, with the same final message_complete shape
    — so the orchestrator can't tell the difference structurally.
    """

    @property
    def default_model(self) -> str:
        return MODEL_NAME

    @property
    def provider_name(self) -> str:
        return "mock"

    async def chat_stream(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamEvent]:
        # ----- Detect what kind of turn this is -----
        last = messages[-1] if messages else {"role": "user", "content": ""}
        last_role = last.get("role")
        last_content = last.get("content")

        is_tool_result_turn = (
            last_role == "user"
            and isinstance(last_content, list)
            and any(
                isinstance(b, dict) and b.get("type") == "tool_result"
                for b in last_content
            )
        )

        if is_tool_result_turn:
            async for ev in self._post_tool_turn(last_content):
                yield ev
            return

        # ----- First turn: maybe tool_use, maybe direct text -----
        latest_user_text = _extract_latest_user_text(messages)
        choice = _pick_tool(latest_user_text)

        if choice and tools:
            tool_name, tool_input = choice
            available = {t.name for t in tools}
            if tool_name in available:
                async for ev in self._tool_use_turn(tool_name, tool_input):
                    yield ev
                return

        # Fallback — text-only reply
        async for ev in self._text_only_turn(latest_user_text):
            yield ev

    # ----- helpers -----

    async def _tool_use_turn(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> AsyncIterator[StreamEvent]:
        """Emit a single tool_use block + message_complete(stop=tool_use)."""
        prelude = "Let me look that up for you."
        # Stream the prelude in small chunks for a realistic typing feel.
        for chunk in _word_chunks(prelude):
            yield StreamEvent(type="text_delta", data={"text": chunk})

        tool_use_id = f"toolu_mock_{uuid4().hex[:12]}"
        yield StreamEvent(
            type="tool_use_start",
            data={"tool_use_id": tool_use_id, "name": tool_name},
        )
        yield StreamEvent(
            type="tool_use_end",
            data={"id": tool_use_id, "name": tool_name, "input": tool_input},
        )

        yield StreamEvent(
            type="message_complete",
            data={
                "stop_reason": "tool_use",
                "text": prelude,
                "tool_uses": [{"id": tool_use_id, "name": tool_name, "input": tool_input}],
                "tokens_input": 100,
                "tokens_output": 30,
            },
        )

    async def _post_tool_turn(
        self,
        tool_result_blocks: list[dict[str, Any]],
    ) -> AsyncIterator[StreamEvent]:
        """Second turn: summarize each tool_result into prose."""
        summaries = []
        for block in tool_result_blocks:
            if not isinstance(block, dict):
                continue
            raw = block.get("content", "")
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
            except json.JSONDecodeError:
                parsed = {"raw": raw}
            # Best-effort tool_name extraction — content_blocks don't always carry it.
            # Fall back to scanning the JSON for hints.
            tool_name_guess = _guess_tool_from_payload(parsed)
            summaries.append(_summarize_tool_result(tool_name_guess, parsed))

        full_text = " ".join(summaries) if summaries else "Data retrieved."

        for chunk in _word_chunks(full_text):
            yield StreamEvent(type="text_delta", data={"text": chunk})

        yield StreamEvent(
            type="message_complete",
            data={
                "stop_reason": "end_turn",
                "text": full_text,
                "tool_uses": [],
                "tokens_input": 200,
                "tokens_output": len(full_text.split()),
            },
        )

    async def _text_only_turn(
        self,
        user_text: str,
    ) -> AsyncIterator[StreamEvent]:
        """Generic reply when no tool match — keeps the UI responsive."""
        if not user_text.strip():
            reply = (
                "I'm running in mock mode while we wait on API credits. "
                "Ask me about a specific building (e.g. B001) — its energy, "
                "cost, CO₂, anomalies, recommendations, or battery scenarios."
            )
        else:
            reply = (
                f"(Mock mode reply) I would normally analyse your portfolio data "
                f"to answer this. Try naming a building like B001, B005, or B009 "
                f"with a keyword such as 'energy', 'anomalies', 'recommendations', "
                f"or 'battery'."
            )
        for chunk in _word_chunks(reply):
            yield StreamEvent(type="text_delta", data={"text": chunk})

        yield StreamEvent(
            type="message_complete",
            data={
                "stop_reason": "end_turn",
                "text": reply,
                "tool_uses": [],
                "tokens_input": 80,
                "tokens_output": len(reply.split()),
            },
        )


# ----- module-level helpers --------------------------------------------


def _word_chunks(text: str, words_per_chunk: int = 3) -> list[str]:
    """Split text into small chunks so 'streaming' looks like typing."""
    parts = text.split(" ")
    out: list[str] = []
    buf: list[str] = []
    for w in parts:
        buf.append(w)
        if len(buf) >= words_per_chunk:
            out.append(" ".join(buf) + " ")
            buf = []
    if buf:
        out.append(" ".join(buf))
    return out


def _extract_latest_user_text(messages: list[dict[str, Any]]) -> str:
    """Get the most recent user message's text content (ignore tool_result turns)."""
    for m in reversed(messages):
        if m.get("role") != "user":
            continue
        content = m.get("content")
        if isinstance(content, str):
            return content
        # tool_result list — keep searching backwards for actual user text
    return ""


def _guess_tool_from_payload(payload: dict[str, Any]) -> str:
    """Cheap heuristic to guess which tool produced a result dict."""
    if not isinstance(payload, dict):
        return "unknown"
    if "scenarios" in payload:
        return "simulate_battery_scenario"
    if "anomalies" in payload or "by_severity" in payload:
        return "get_anomalies"
    if "recommendations" in payload:
        return "list_recommendations"
    if "ranked" in payload:
        return "compare_buildings"
    if "metric" in payload and "current_value" in payload:
        return "query_kpi"
    if "new_status" in payload:
        return "update_action_status"
    return "unknown"
