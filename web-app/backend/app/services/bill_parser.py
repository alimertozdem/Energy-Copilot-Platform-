"""Heuristic utility-bill parser — extracted PDF text/tables -> monthly rows.

The Tier-1 upload (#2) needs monthly (period, kWh, optional cost). Most building
owners have a PDF utility bill, not a clean CSV. This module turns the TEXT +
TABLES already extracted from a (digital) PDF into CANDIDATE monthly rows the
user reviews before saving — it never auto-trusts the extraction.

Pure functions (no PDF library here): the endpoint extracts text/tables with
pdfplumber and hands them in, so this heuristic is unit-testable without a PDF.

Locale-aware for the target markets (DE + TR + EN): month names in three
languages, and EU (1.234,56) vs US (1,234.56) number formats. Extraction is
best-effort and flagged low-confidence — the UI shows every row for confirmation.
"""
from __future__ import annotations

import re

# Month name -> month number (EN / DE / TR). Longer names first at match time.
_MONTHS: dict[str, int] = {
    "january": 1, "januar": 1, "ocak": 1, "jan": 1,
    "february": 2, "februar": 2, "subat": 2, "şubat": 2, "feb": 2,
    "march": 3, "marz": 3, "märz": 3, "mart": 3, "mar": 3,
    "april": 4, "nisan": 4, "apr": 4,
    "may": 5, "mai": 5, "mayis": 5, "mayıs": 5,
    "june": 6, "juni": 6, "haziran": 6, "jun": 6,
    "july": 7, "juli": 7, "temmuz": 7, "jul": 7,
    "august": 8, "agustos": 8, "ağustos": 8, "aug": 8,
    "september": 9, "eylul": 9, "eylül": 9, "sept": 9, "sep": 9,
    "october": 10, "oktober": 10, "ekim": 10, "oct": 10, "okt": 10,
    "november": 11, "kasim": 11, "kasım": 11, "nov": 11,
    "december": 12, "dezember": 12, "aralik": 12, "aralık": 12, "dec": 12, "dez": 12,
}
_MONTH_NAMES_BY_LEN = sorted(_MONTHS, key=len, reverse=True)

_PERIOD_COLS = ["period", "month", "date", "monat", "datum", "ay", "tarih", "dönem", "donem", "abrechnung"]
_KWH_COLS = ["kwh", "verbrauch", "consumption", "tüketim", "tuketim", "energy", "enerji", "menge"]
_COST_COLS = ["eur", "€", "cost", "betrag", "tutar", "fiyat", "amount", "kosten", "ücret", "ucret"]

_KWH_RE = re.compile(r"([\d.,]+)\s*kwh", re.IGNORECASE)
_COST_RE = re.compile(r"(?:€|eur)\s*([\d.,]+)|([\d.,]+)\s*(?:€|eur)", re.IGNORECASE)


def parse_number(raw: str | None) -> float | None:
    """Parse a number from a cell, handling EU (1.234,56) and US (1,234.56)."""
    if raw is None:
        return None
    s = re.sub(r"[^\d.,]", "", str(raw).strip())
    if not s or not re.search(r"\d", s):
        return None
    if "." in s and "," in s:
        # the LAST separator is the decimal point
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")   # 1.234,56 -> 1234.56
        else:
            s = s.replace(",", "")                      # 1,234.56 -> 1234.56
    elif "," in s:
        # comma only: thousands if grouped (1,234 / 1,234,567), else EU decimal
        if s.count(",") > 1 or re.fullmatch(r"\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif "." in s:
        # dot only: thousands if grouped or a single 3-digit group (EU 1.234)
        if s.count(".") > 1 or re.fullmatch(r"\d{1,3}(\.\d{3})+", s) or re.fullmatch(r"\d+\.\d{3}", s):
            s = s.replace(".", "")
        # else keep the dot as a decimal (1234.5, 12.50)
    try:
        return float(s)
    except ValueError:
        return None


def normalize_period(raw: str | None) -> str | None:
    """Parse a period cell to 'YYYY-MM', or None."""
    if not raw:
        return None
    s = str(raw).strip()
    m = re.search(r"(20\d{2}|19\d{2})[-/.](\d{1,2})\b", s)        # 2024-03
    if m and 1 <= int(m.group(2)) <= 12:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    m = re.search(r"\b(\d{1,2})[-/.](20\d{2}|19\d{2})\b", s)      # 03/2024
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    low = s.lower()
    ym = re.search(r"(?:19|20)\d{2}", low)
    if ym:
        for name in _MONTH_NAMES_BY_LEN:
            if re.search(r"\b" + re.escape(name) + r"\b", low):
                return f"{ym.group(0)}-{_MONTHS[name]:02d}"
    return None


def _find_col(header: list[str], keywords: list[str]) -> int | None:
    for i, cell in enumerate(header):
        c = (cell or "").lower()
        if any(k in c for k in keywords):
            return i
    return None


def _rows_from_tables(tables: list) -> list[dict]:
    rows: list[dict] = []
    for table in tables or []:
        if not table or len(table) < 2:
            continue
        header = [str(c or "").lower() for c in table[0]]
        pcol = _find_col(header, _PERIOD_COLS)
        kcol = _find_col(header, _KWH_COLS)
        ccol = _find_col(header, _COST_COLS)
        if pcol is None or kcol is None:
            continue
        for r in table[1:]:
            if pcol >= len(r) or kcol >= len(r):
                continue
            period = normalize_period(r[pcol])
            kwh = parse_number(r[kcol])
            if not period or kwh is None or kwh <= 0:
                continue
            cost = parse_number(r[ccol]) if (ccol is not None and ccol < len(r)) else None
            rows.append({"period": period, "energy_kwh": round(kwh, 2), "cost_eur": cost})
    return rows


def _rows_from_text(text: str) -> list[dict]:
    rows: list[dict] = []
    for line in (text or "").splitlines():
        km = _KWH_RE.search(line)
        if not km:
            continue
        kwh = parse_number(km.group(1))
        period = normalize_period(line)
        if kwh is None or kwh <= 0 or not period:
            continue
        cost = None
        cm = _COST_RE.search(line)
        if cm:
            cost = parse_number(cm.group(1) or cm.group(2))
        rows.append({"period": period, "energy_kwh": round(kwh, 2), "cost_eur": cost})
    return rows


def parse_bill(text: str = "", tables: list | None = None) -> dict:
    """Extract candidate monthly rows from a bill's text + tables.

    Returns {"rows": [{period, energy_kwh, cost_eur}], "source", "warnings"}.
    Tables are tried first (most reliable), then a line-by-line text scan.
    Rows are de-duplicated by period (first wins) and sorted.
    """
    rows = _rows_from_tables(tables or [])
    source = "table"
    if not rows:
        rows = _rows_from_text(text or "")
        source = "text" if rows else "none"

    seen: dict[str, dict] = {}
    for r in rows:
        seen.setdefault(r["period"], r)
    out = sorted(seen.values(), key=lambda x: x["period"])

    warnings: list[str] = []
    if not out:
        warnings.append(
            "No monthly consumption rows could be read from this PDF. "
            "Enter the months manually or upload a CSV instead."
        )
    else:
        warnings.append(
            "Auto-extracted from the PDF — review every row (period, kWh, cost) before saving."
        )
    return {"rows": out, "source": source, "warnings": warnings}
