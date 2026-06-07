"""LLM provider package.

Implementations:
    AnthropicProvider  — claude-sonnet-4-6 via Anthropic API (production)
    MockLLMProvider    — deterministic stand-in for dev without credits

Selection (env var LLM_PROVIDER):
    "anthropic" (default)  — AnthropicProvider, needs ANTHROPIC_API_KEY + credits
    "mock"                 — MockLLMProvider, no API calls, free
"""
import os

from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.base import (
    LLMProvider,
    StreamEvent,
    ToolDefinition,
)
from app.services.llm.mock_provider import MockLLMProvider

__all__ = [
    "LLMProvider",
    "StreamEvent",
    "ToolDefinition",
    "AnthropicProvider",
    "MockLLMProvider",
    "get_llm_provider",
]


def get_llm_provider() -> LLMProvider:
    """Factory — picks provider from LLM_PROVIDER env var.

    Defaults to 'anthropic'. Set LLM_PROVIDER=mock in .env to switch to
    the deterministic mock provider (no API credits required).
    """
    choice = (os.getenv("LLM_PROVIDER") or "anthropic").strip().lower()
    if choice == "mock":
        return MockLLMProvider()
    return AnthropicProvider()
