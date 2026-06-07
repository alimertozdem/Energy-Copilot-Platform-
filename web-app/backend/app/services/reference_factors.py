"""Canonical energy reference factors — backend mirror of the Fabric ``ref_`` layer.

The single source of truth lives in Fabric:
``notebooks/reference/03_ref_factors_tariffs_loader.py`` (Delta tables
``ref_grid_emission_factors`` + ``ref_electricity_tariffs``). Pending /
upload-only buildings never touch Fabric, so the baseline-KPI engine needs the
same numbers in-process. This module therefore **mirrors the notebook values
verbatim** — a deliberate, small duplication that keeps the upload→KPI path
independent of Fabric availability. When the notebook changes, update here too.

Design (matches the notebook's rationale):
  * **Year-indexed** — a building's 2024 carbon must use the 2024 grid factor,
    2025 → 2025. A single flat factor would blur "the grid got cleaner" with
    "the building improved", which auditors reject for CSRD/CRREM reporting.
  * **Location-based** grid average (not market-/supplier-specific).
  * **Confidence is carried through** (``official_series`` | ``national_single``
    | ``verify_iea_2025``) so the UI can label provenance honestly.

Values verified 2026-05-30 (sources in the notebook header: UBA, TEİAŞ, IEA,
Eurostat). Units: grid factor = kg CO₂/kWh; tariff = €/kWh (non-household,
ex-recoverable tax, Eurostat blended).
"""
from __future__ import annotations

from typing import NamedTuple

# --------------------------------------------------------------------------- #
# Result types
# --------------------------------------------------------------------------- #


class GridFactor(NamedTuple):
    """A resolved grid emission factor for one country/year."""

    country_code: str
    year: int
    emission_factor_kg_kwh: float
    confidence: str  # official_series | national_single | verify_iea_2025
    source: str


class Tariff(NamedTuple):
    """A resolved average electricity tariff for one country/year."""

    country_code: str
    year: int
    avg_eur_kwh: float
    source: str


# --------------------------------------------------------------------------- #
# Source data — verbatim mirror of notebook 03 (do not diverge silently)
# --------------------------------------------------------------------------- #

_UBA = "Umweltbundesamt (UBA) — CO₂-Emissionen pro kWh Strom"
_IEA = "IEA Emissions Factors 2025"
_TEIAS = "TEİAŞ (Türkiye Elektrik İletim A.Ş.)"
_EUROSTAT = "Eurostat nrg_pc_205 (non-household, ex-recoverable tax) + country ToU"
_EPDK = "EPDK / EXIST (approx)"

# country -> { year -> (factor_kg_kwh, confidence, source) }
_GRID: dict[str, dict[int, tuple[float, str, str]]] = {
    "DE": {
        2022: (0.433, "official_series", _UBA),
        2023: (0.386, "official_series", _UBA),
        2024: (0.363, "official_series", _UBA),
        2025: (0.363, "official_series_carryforward", _UBA),
    },
    "TR": {
        2023: (0.442, "national_single", _TEIAS),
        2024: (0.442, "national_single", _TEIAS),
        2025: (0.442, "national_single", _TEIAS),
    },
    "AT": {2024: (0.158, "verify_iea_2025", _IEA)},  # hydro-dominant
    "NL": {2024: (0.290, "verify_iea_2025", _IEA)},
    "FR": {2024: (0.052, "verify_iea_2025", _IEA)},  # nuclear-dominant
    "PL": {2024: (0.660, "verify_iea_2025", _IEA)},  # coal, declining
    "EU": {2024: (0.230, "verify_iea_2025", "Eurostat / EEA")},
}

# country -> { year -> (avg_eur_kwh, source) }
_TARIFF: dict[str, dict[int, tuple[float, str]]] = {
    "DE": {2025: (0.226, _EUROSTAT)},
    "AT": {2025: (0.190, _EUROSTAT)},
    "NL": {2025: (0.205, _EUROSTAT)},
    "TR": {2025: (0.085, _EPDK)},
    "EU": {2025: (0.190, _EUROSTAT)},
}

# Fallback country when a building's country has no reference row.
_FALLBACK_COUNTRY = "EU"


# --------------------------------------------------------------------------- #
# Resolution helpers
# --------------------------------------------------------------------------- #


def _norm_country(country_code: str | None) -> str:
    code = (country_code or "").strip().upper()
    return code if code else _FALLBACK_COUNTRY


def _resolve_year(by_year: dict[int, object], year: int) -> int:
    """Pick the best available year for ``year``.

    Prefer the latest published year *at or before* the requested year (so a
    2025 lookup uses 2024 data when 2025 isn't published yet). If the request
    predates all data, use the earliest available year.
    """
    if year in by_year:
        return year
    years = sorted(by_year)
    at_or_before = [y for y in years if y <= year]
    return at_or_before[-1] if at_or_before else years[0]


def grid_emission_factor(country_code: str | None, year: int) -> GridFactor:
    """Resolve kg CO₂/kWh for a country/year, falling back by year then to EU.

    Always returns a value (never raises) so the KPI engine can run for any
    building; provenance is carried in ``confidence`` + ``source``.
    """
    code = _norm_country(country_code)
    table = _GRID.get(code) or _GRID[_FALLBACK_COUNTRY]
    resolved_country = code if code in _GRID else _FALLBACK_COUNTRY
    y = _resolve_year(table, year)
    factor, confidence, source = table[y]
    return GridFactor(
        country_code=resolved_country,
        year=y,
        emission_factor_kg_kwh=factor,
        confidence=confidence,
        source=source,
    )


def electricity_tariff_avg(country_code: str | None, year: int) -> Tariff:
    """Resolve the average €/kWh tariff for a country/year (EU fallback)."""
    code = _norm_country(country_code)
    table = _TARIFF.get(code) or _TARIFF[_FALLBACK_COUNTRY]
    resolved_country = code if code in _TARIFF else _FALLBACK_COUNTRY
    y = _resolve_year(table, year)
    avg, source = table[y]
    return Tariff(
        country_code=resolved_country,
        year=y,
        avg_eur_kwh=avg,
        source=source,
    )
