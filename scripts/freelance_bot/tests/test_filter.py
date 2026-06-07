"""Unit tests for the deterministic filter layer.

These run without any LLM or network — they exercise pure-Python logic.
LLM-dependent tests are skipped unless GEMINI_API_KEY is set.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.filter.budget import _to_float, check_budget, parse_budget  # noqa: E402
from src.filter.keyword import check_keywords  # noqa: E402


# ────────────────────────────── Keyword ──────────────────────────────

def test_keyword_pass_on_csrd_match():
    res = check_keywords(
        title="Need CSRD Scope 1/2/3 dashboard",
        description="Looking for Power BI consultant",
        include=["csrd", "power bi"],
        exclude=["tableau only"],
    )
    assert res.passed is True
    assert "csrd" in res.matched_include


def test_keyword_reject_on_exclude():
    res = check_keywords(
        title="Power BI dashboard project",
        description="Must be Tableau only, no Power BI",
        include=["power bi"],
        exclude=["tableau only"],
    )
    assert res.passed is False
    assert res.matched_exclude == ["tableau only"]


def test_keyword_reject_when_no_include_match():
    res = check_keywords(
        title="WordPress developer needed",
        description="Build a marketing site",
        include=["power bi", "csrd"],
        exclude=[],
    )
    assert res.passed is False
    assert res.matched_include == []


def test_keyword_case_insensitive():
    res = check_keywords(
        title="MICROSOFT FABRIC architect",
        description="...",
        include=["microsoft fabric"],
        exclude=[],
    )
    assert res.passed is True


# ────────────────────────────── Budget parsing ──────────────────────────────

def test_to_float_european_format():
    assert _to_float("1.200,50") == 1200.5
    assert _to_float("1,200.50") == 1200.5
    assert _to_float("1200") == 1200.0
    assert _to_float("12,5") == 12.5  # decimal comma, short
    assert _to_float("1,234") == 1234.0  # thousands comma


def test_parse_budget_eur_range():
    fx = {"USD": 0.92, "EUR": 1.0}
    lo, hi, btype, raw = parse_budget("Budget €2,000-3,000 fixed", fx)
    assert lo == 2000.0
    assert hi == 3000.0
    assert btype == "fixed"
    assert raw is not None


def test_parse_budget_usd_hourly():
    fx = {"USD": 0.92, "EUR": 1.0}
    lo, hi, btype, raw = parse_budget("Rate: $40-80/hr", fx)
    assert btype == "hourly"
    assert lo == pytest.approx(40 * 0.92)
    assert hi == pytest.approx(80 * 0.92)


def test_parse_budget_no_amount():
    lo, hi, btype, raw = parse_budget("No budget specified", {"EUR": 1.0})
    assert lo is None and hi is None
    assert btype == "unknown"


def test_check_budget_passes_when_no_budget_allowed():
    fx = {"EUR": 1.0}
    res = check_budget(
        "We have a Power BI project",
        fixed_min_eur=500, hourly_min_eur=30, allow_no_budget=True, fx_to_eur=fx,
    )
    assert res.passed is True
    assert res.type == "unknown"


def test_check_budget_rejects_below_threshold():
    fx = {"EUR": 1.0}
    res = check_budget(
        "Quick job, budget €200 fixed",
        fixed_min_eur=500, hourly_min_eur=30, allow_no_budget=True, fx_to_eur=fx,
    )
    assert res.passed is False


def test_check_budget_passes_above_threshold():
    fx = {"EUR": 1.0}
    res = check_budget(
        "Budget €3,000-5,000 fixed",
        fixed_min_eur=500, hourly_min_eur=30, allow_no_budget=True, fx_to_eur=fx,
    )
    assert res.passed is True
    assert res.max_eur == 5000.0


# ────────────────────────────── LLM scoring (network) ──────────────────────────────

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
def test_llm_score_returns_valid_range():
    from src.filter.llm_score import score_job
    res = score_job(
        title="Build CSRD Scope 1/2/3 dashboard on Microsoft Fabric",
        description=(
            "We need a Power BI consultant to help us build a CSRD-compliant "
            "Scope 1/2/3 emissions dashboard on Microsoft Fabric. Budget €5000-10000."
        ),
    )
    assert 0 <= res.score <= 10
    assert res.score >= 7, f"strong fit should score ≥7, got {res.score} — {res.reasoning}"
