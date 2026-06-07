"""Thin Gemini client.

Reads GEMINI_API_KEY from env. Falls back to GROQ_API_KEY → Llama 3.3 70B
if Gemini errors. Never silently fails — caller sees an error and decides.

Why this module exists: we keep prompt construction OUT of the LLM client.
The client takes a fully-formed prompt and returns text. Filter/proposal/brief
modules build prompts in their own files for clarity.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Optional

import httpx


GEMINI_MODEL = "gemini-2.0-flash"  # free tier, 1500 req/day, fast + capable
GROQ_MODEL = "llama-3.3-70b-versatile"  # fallback


class LLMError(RuntimeError):
    """Raised when both primary and fallback LLMs fail."""


@dataclass
class LLMResponse:
    text: str
    provider: str   # 'gemini' | 'groq'
    model: str


def call_llm(
    prompt: str,
    *,
    temperature: float = 0.3,
    max_output_tokens: int = 1024,
    json_mode: bool = False,
    retries: int = 2,
) -> LLMResponse:
    """Call Gemini Flash; on failure, fall back to Groq.

    Args:
        prompt: full user prompt (system context can be prepended by caller)
        temperature: 0.0-1.0; we use 0.2 for filtering, 0.4-0.7 for writing
        max_output_tokens: cap output size
        json_mode: hint that response should be parseable JSON
        retries: how many times to retry transient errors before fallback
    """
    last_err: Optional[Exception] = None

    # Try Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        for attempt in range(retries + 1):
            try:
                text = _call_gemini(prompt, api_key, temperature, max_output_tokens, json_mode)
                return LLMResponse(text=text, provider="gemini", model=GEMINI_MODEL)
            except Exception as e:
                last_err = e
                if attempt < retries:
                    time.sleep(1.5 ** attempt)

    # Fall back to Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            text = _call_groq(prompt, groq_key, temperature, max_output_tokens, json_mode)
            return LLMResponse(text=text, provider="groq", model=GROQ_MODEL)
        except Exception as e:
            last_err = e

    raise LLMError(f"Both Gemini and Groq failed (or no keys set). Last error: {last_err}")


def _call_gemini(prompt: str, api_key: str, temperature: float, max_tokens: int, json_mode: bool) -> str:
    """Direct REST call — avoids the google-generativeai SDK to keep deps minimal."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    body: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"

    resp = httpx.post(url, json=body, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
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
    s = text.strip()
    if s.startswith("```"):
        # remove fence + optional language tag
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    return json.loads(s)
