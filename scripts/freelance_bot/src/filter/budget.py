"""Tier 2 — budget extraction and threshold check.

We parse common budget patterns from posting text. Handles €, $, £, ₺ and CHF.
Returns (min, max, type) where type is 'fixed' | 'hourly' | 'unknown'.

The parsing is intentionally permissive — false positives at this stage are
better than false negatives, because the LLM (Tier 3) will catch nonsense.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


CURRENCY_SYMBOLS = {
    "€": "EUR", "EUR": "EUR",
    "$": "USD", "USD": "USD", "US$": "USD",
    "£": "GBP", "GBP": "GBP",
    "₺": "TRY", "TRY": "TRY", "TL": "TRY",
    "CHF": "CHF",
}

# Pattern: "€500", "€1,000", "EUR 1.500", "$50/hr", "€500-1500"
AMOUNT = r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+"
RANGE_SEP = r"\s*(?:-|–|to|bis)\s*"
HOURLY_HINTS = r"(?:/h|/hr|/hour|per hour|hourly|p/h|/std|pro stunde)"
FIXED_HINTS = r"(?:fixed|total|project|budget|festpreis|gesamt)"


@dataclass
class BudgetResult:
    passed: bool
    min_eur: Optional[float]
    max_eur: Optional[float]
    type: str  # 'fixed' | 'hourly' | 'unknown'
    raw_match: Optional[str]
    reason: str


def parse_budget(text: str, fx_to_eur: dict[str, float]) -> tuple[Optional[float], Optional[float], str, Optional[str]]:
    """Return (min_eur, max_eur, type, raw_match). Best-effort, never raises."""
    if not text:
        return None, None, "unknown", None

    low = text.lower()
    is_hourly = bool(re.search(HOURLY_HINTS, low))

    # Try to find a range first (€500-1500)
    for sym, code in CURRENCY_SYMBOLS.items():
        sym_esc = re.escape(sym)
        # range like "€500-1500" or "$50 to $80"
        m = re.search(
            rf"{sym_esc}\s*({AMOUNT}){RANGE_SEP}{sym_esc}?\s*({AMOUNT})",
            text, re.IGNORECASE,
        )
        if m:
            a = _to_float(m.group(1))
            b = _to_float(m.group(2))
            if a and b:
                fx = fx_to_eur.get(code, 1.0) if code != "EUR" else 1.0
                lo, hi = sorted([a * fx, b * fx])
                return lo, hi, ("hourly" if is_hourly else "fixed"), m.group(0)

        # single amount like "€2,000"
        m = re.search(rf"{sym_esc}\s*({AMOUNT})", text, re.IGNORECASE)
        if m:
            a = _to_float(m.group(1))
            if a:
                fx = fx_to_eur.get(code, 1.0) if code != "EUR" else 1.0
                return a * fx, a * fx, ("hourly" if is_hourly else "fixed"), m.group(0)

    return None, None, "unknown", None


def _to_float(s: str) -> Optional[float]:
    """Parse "1,200.50", "1.200,50", "1 200" → float."""
    if not s:
        return None
    s = s.strip().replace(" ", "")
    # If both . and , appear, assume the last one is the decimal separator
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        # heuristic: 1,234 → thousands; 12,5 → decimal
        if re.search(r",\d{3}(?!\d)", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def check_budget(
    description: str,
    *,
    fixed_min_eur: float,
    hourly_min_eur: float,
    allow_no_budget: bool,
    fx_to_eur: dict[str, float],
) -> BudgetResult:
    """Apply Tier 2 budget threshold."""
    lo, hi, btype, raw = parse_budget(description, fx_to_eur)

    if btype == "unknown":
        return BudgetResult(
            passed=allow_no_budget, min_eur=None, max_eur=None,
            type="unknown", raw_match=None,
            reason="no_budget_in_post" if allow_no_budget else "no_budget_rejected",
        )

    threshold = hourly_min_eur if btype == "hourly" else fixed_min_eur
    # Use max so a generous range like "$500-$5000" passes
    effective = hi if hi else lo

    if effective is None or effective < threshold:
        return BudgetResult(
            passed=False, min_eur=lo, max_eur=hi, type=btype, raw_match=raw,
            reason=f"below_threshold ({effective} < {threshold})",
        )

    return BudgetResult(
        passed=True, min_eur=lo, max_eur=hi, type=btype, raw_match=raw,
        reason="ok",
    )
