"""Unit tests for the baseline-KPI energy math + reference factors.

Pure-compute, no DB: rows/building are duck-typed stand-ins exposing the same
attributes the ORM models do (energy_kwh/cost_eur are Decimal, as the Numeric
columns return). Verifies the product-owner-approved logic: trailing-12 vs
annualize, EUI, year-indexed CO2 factor, actual-vs-estimated cost, 30-day map.
"""
from dataclasses import dataclass
from decimal import Decimal

from app.services import baseline_kpi, reference_factors

DAYS = baseline_kpi._DAYS_30_OF_YEAR


@dataclass
class Row:
    period: str
    energy_kwh: Decimal
    cost_eur: Decimal | None = None


@dataclass
class Bldg:
    floor_area_m2: Decimal | None
    country_code: str | None


def periods(start: str, n: int) -> list[str]:
    y, m = map(int, start.split("-"))
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def rows(start: str, n: int, kwh=10000, cost=None) -> list[Row]:
    c = Decimal(str(cost)) if cost is not None else None
    return [Row(p, Decimal(str(kwh)), c) for p in periods(start, n)]


# --- compute_baseline_kpis -------------------------------------------------

def test_empty_rows():
    r = baseline_kpi.compute_baseline_kpis([], Bldg(Decimal("1000"), "DE"))
    assert r["has_data"] is False
    assert r["eui_kwh_m2_yr"] is None
    assert r["annual_energy_kwh"] is None
    assert r["source"] == "uploaded_baseline"
    assert r["cost_basis"] == "unknown"


def test_twelve_months_de_no_cost():
    r = baseline_kpi.compute_baseline_kpis(rows("2024-01", 12), Bldg(Decimal("1000"), "DE"))
    assert r["is_annualized"] is False
    assert r["window"] == "trailing_12"
    assert r["months_available"] == 12 and r["window_months"] == 12
    assert r["annual_energy_kwh"] == 120000.0
    assert r["eui_kwh_m2_yr"] == 120.0
    # DE 2024 official factor
    assert r["co2_factor_kg_kwh"] == 0.363
    assert r["co2_factor_year"] == 2024
    assert r["co2_factor_confidence"] == "official_series"
    assert r["annual_co2_kg"] == round(120000.0 * 0.363, 0)
    # no uploaded cost -> estimated via DE tariff (2025 fallback for 2024)
    assert r["cost_basis"] == "estimated"
    assert r["cost_rate_eur_kwh"] == 0.226
    assert r["annual_cost_eur"] == round(120000.0 * 0.226, 0)
    # 30-day map uses the module constant
    assert r["kwh_30d"] == round(120000.0 * DAYS, 0)


def test_partial_three_months_annualized():
    r = baseline_kpi.compute_baseline_kpis(rows("2024-01", 3), Bldg(Decimal("1000"), "DE"))
    assert r["is_annualized"] is True
    assert r["window"] == "annualized_from_3"
    assert r["months_available"] == 3 and r["window_months"] == 3
    # (30000/3)*12 = 120000
    assert r["annual_energy_kwh"] == 120000.0
    assert r["eui_kwh_m2_yr"] == 120.0


def test_cost_actual_full_year():
    r = baseline_kpi.compute_baseline_kpis(
        rows("2024-01", 12, cost=2000), Bldg(Decimal("1000"), "DE")
    )
    assert r["cost_basis"] == "actual"
    assert r["cost_rate_eur_kwh"] is None
    assert r["annual_cost_eur"] == 24000.0


def test_cost_actual_annualized():
    r = baseline_kpi.compute_baseline_kpis(
        rows("2024-01", 3, cost=2000), Bldg(Decimal("1000"), "DE")
    )
    assert r["cost_basis"] == "actual"
    # (6000/3)*12 = 24000
    assert r["annual_cost_eur"] == 24000.0


def test_partial_cost_falls_back_to_estimate():
    mixed = [
        Row("2024-01", Decimal("10000"), Decimal("2000")),
        Row("2024-02", Decimal("10000"), None),
        Row("2024-03", Decimal("10000"), Decimal("2000")),
    ]
    r = baseline_kpi.compute_baseline_kpis(mixed, Bldg(Decimal("1000"), "DE"))
    assert r["cost_basis"] == "estimated"
    assert r["cost_rate_eur_kwh"] == 0.226


def test_no_area_yields_no_eui_but_keeps_energy():
    r = baseline_kpi.compute_baseline_kpis(rows("2024-01", 12), Bldg(None, "DE"))
    assert r["eui_kwh_m2_yr"] is None
    assert r["floor_area_m2"] is None
    assert r["annual_energy_kwh"] == 120000.0


def test_zero_area_treated_as_none():
    r = baseline_kpi.compute_baseline_kpis(rows("2024-01", 12), Bldg(Decimal("0"), "DE"))
    assert r["eui_kwh_m2_yr"] is None


def test_turkey_factor_year_indexed():
    r = baseline_kpi.compute_baseline_kpis(rows("2023-01", 12), Bldg(Decimal("1000"), "TR"))
    assert r["co2_factor_kg_kwh"] == 0.442
    assert r["co2_factor_year"] == 2023
    assert r["co2_factor_confidence"] == "national_single"


def test_trailing_window_uses_last_12_of_18():
    r = baseline_kpi.compute_baseline_kpis(rows("2023-07", 18), Bldg(Decimal("1000"), "DE"))
    assert r["months_available"] == 18
    assert r["window_months"] == 12
    assert r["is_annualized"] is False
    assert r["period_start"] == "2024-01"
    assert r["period_end"] == "2024-12"
    assert r["annual_energy_kwh"] == 120000.0


def test_unsorted_rows_are_ordered():
    rs = rows("2024-01", 12)
    shuffled = [rs[5], rs[0], rs[11], *rs[1:5], *rs[6:11]]
    r = baseline_kpi.compute_baseline_kpis(shuffled, Bldg(Decimal("1000"), "DE"))
    assert r["period_start"] == "2024-01"
    assert r["period_end"] == "2024-12"


# --- reference_factors -----------------------------------------------------

def test_grid_de_2024_official():
    gf = reference_factors.grid_emission_factor("DE", 2024)
    assert (gf.emission_factor_kg_kwh, gf.year, gf.confidence) == (0.363, 2024, "official_series")


def test_grid_de_before_series_uses_earliest():
    gf = reference_factors.grid_emission_factor("DE", 2021)
    assert gf.year == 2022 and gf.emission_factor_kg_kwh == 0.433


def test_grid_tr_future_resolves_latest():
    gf = reference_factors.grid_emission_factor("TR", 2030)
    assert gf.year == 2025 and gf.emission_factor_kg_kwh == 0.442


def test_grid_unknown_country_falls_back_eu():
    gf = reference_factors.grid_emission_factor("XX", 2024)
    assert gf.country_code == "EU" and gf.emission_factor_kg_kwh == 0.230


def test_grid_none_country_falls_back_eu():
    gf = reference_factors.grid_emission_factor(None, 2024)
    assert gf.country_code == "EU"


def test_tariff_de_resolves_to_2025():
    t = reference_factors.electricity_tariff_avg("DE", 2024)
    assert t.year == 2025 and t.avg_eur_kwh == 0.226


def test_tariff_unknown_country_eu():
    t = reference_factors.electricity_tariff_avg("ZZ", 2025)
    assert t.country_code == "EU" and t.avg_eur_kwh == 0.190
