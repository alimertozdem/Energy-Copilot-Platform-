"""Thin Gemini client.

Reads GEMINI_API_KEY from env. Falls back to GROQ_API_KEY → Llama 3.3 70B
if Gemini errors. Never silently fails — caller sees an error and decides.

Model is env-overridable via GEMINI_MODEL so a future model retirement is a
config change, not a code edit. Two free-tier realities are handled here:
  * gemini-2.5-flash is a *thinking* model — without thinkingBudget=0 it spends
    the output budget on hidden reasoning and returns an empty body.
  * the free tier rate-limits (429), so calls are throttled to a min interval.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Optional

import httpx


GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"  # fallback (still active as of 2026-06)

# Free-tier throttle: minimum seconds between Gemini calls (env-tunable).
_MIN_INTERVAL = float(os.getenv("GEMINI_MIN_INTERVAL_S", "6"))
_last_gemini_ts = 0.0


class LLMError(RuntimeError):
    """Raised when both primary and fallback LLMs fail."""


@dataclass
class LLMResponse:
    text: str
    provider: str   # 'gemini' | 'groq'
    model: str


def _throttle() -> None:
    global _last_gemini_ts
    gap = _MIN_INTERVAL - (time.time() - _last_gemini_ts)
    if gap > 0:
        time.sleep(gap)
    _last_gemini_ts = time.time()


def call_llm(
    prompt: str,
    *,
    temperature: float = 0.3,
    max_output_tokens: int = 1024,
    json_mode: bool = False,
    retries: int = 2,
) -> LLMResponse:
    """Call Gemini Flash; on failure (incl. rate limit), fall back to Groq."""
    last_err: Optional[Exception] = None

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        for attempt in range(retries + 1):
            try:
                text = _call_gemini(prompt, api_key, temperature, max_output_tokens, json_mode)
                return LLMResponse(text=text, provider="gemini", model=GEMINI_MODEL)
            except Exception as e:
                last_err = e
                if attempt < retries:
                    time.sleep(2.0 * (attempt + 1))  # back off on 429/transient

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            text = _call_groq(prompt, groq_key, temperature, max_output_tokens, json_mode)
            return LLMResponse(text=text, provider="groq", model=GROQ_MODEL)
        except Exception as e:
            last_err = e

    raise LLMError(f"Both Gemini and Groq failed (or no keys set). Last error: {last_err}")


def _call_gemini(prompt: str, api_key: str, temperature: float, max_tokens: int, json_mode: bool) -> str:
    """Direct REST call. Disables 'thinking' so the model returns real output
    within the token budget (critical for gemini-2.5-flash)."""
    _throttle()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    body: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {"thinkingBudget": 0},  # disable thinking -> non-empty output
        },
    }
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"

    resp = httpx.post(url, json=body, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Gemini response shape unexpected: {data}") from e


def _call_groq(prompt: str, api_key: str, temperature: float, max_tokens: int, json_mode: bool) -> str:
    """Groq Cloud OpenAI-compatible endpoint."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body: dict = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    resp = httpx.post(url, json=body, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def parse_json_response(text: str) -> dict:
    """Best-effort parse of LLM JSON output. Strips markdown code fences."""
    s = (text or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    return json.loads(s)
