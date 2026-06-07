"""Tier 1 — keyword filter.

Pure string matching. Fast, cheap, deterministic. Runs before any LLM call.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KeywordResult:
    passed: bool
    matched_include: list[str]
    matched_exclude: list[str]


def check_keywords(
    title: str,
    description: str,
    include: list[str],
    exclude: list[str],
) -> KeywordResult:
    """Pass if at least one include matches AND no exclude matches."""
    haystack = f"{title}\n{description}".lower()

    matched_inc = [k for k in include if k.lower() in haystack]
    matched_exc = [k for k in exclude if k.lower() in haystack]

    passed = bool(matched_inc) and not matched_exc
    return KeywordResult(passed=passed, matched_include=matched_inc, matched_exclude=matched_exc)
