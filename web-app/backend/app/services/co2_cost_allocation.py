"""CO2KostAufG cost-allocation service (building grain).

Computes the landlord/tenant split of the heating-fuel CO₂ price for ONE building,
following the German Kohlendioxidkostenaufteilungsgesetz (CO2KostAufG):

  * Residential / mixed-use → statutory 10-step model on kg CO₂ per m² of LIVING
                              AREA (Wohnfläche) — Anlage zu § 7.
  * Non-residential        → flat 50/50 (the NWG step model is planned but not yet
                              in force — keep 50/50 until enacted).

Heating-fuel basis: only fuels that incur the national CO₂ price (Brennstoffe — gas,
heating oil) count. Refrigerant (F-gas) and grid electricity are NOT part of the levy.

Data source by building type (so the official Wohnfläche basis is used for residential
and B011-style residential buildings are covered):
  * Residential → gold_residential_unit_kpi: Σ area_m2 (Wohnfläche) and
    Σ heating_dhw_kwh_annual × gas EF → heating CO₂.
  * Non-residential (or residential without unit data) → gold_ghg_scope:
    Σ (scope1_gas + scope1_diesel) tCO₂ for the latest reporting year; gross floor
    area from silver_building_master.

Visibility is enforced by the router (get_building_for_user → 404) before calling.

— ENERGY / LEGAL ASSUMPTIONS (STATED — reviewer: Mert) —
  * 10-step table = the statutory model (Vermieter 0/10/…/80/95 %; <12→0/100, ≥52→95/5).
  * Split basis = kg CO₂ / m² LIVING AREA per year (residential).
  * Gas EF = 0.201 kg CO₂/kWh (BEHG natural-gas factor, Heizwert). The legally-binding
    figure is the supplier-reported Brennstoffemissionen on the heating bill; our value
    is an estimate from metered/allocated consumption × EF.
  * Price 2026 = €65/t — top of the nEHS auction corridor (€55–65/t); matches notebook 05.
  * Price ETS2 = €80/t in 2028 — INDICATIVE. EU ETS2 was postponed to 1 Jan 2028
    (EU decision Nov 2025); the market price is uncertain (a stability mechanism targets
    ~€45). Shown as a forward-looking estimate only.
  * Decision-support, not legal or tax advice.
"""
from typing import Any

from app.integrations import fabric_sql
from app.schemas.co2_cost import (
    Co2CostAllocationResponse,
    Co2StairTier,
    Co2UnitAllocation,
)

# 2026 national nEHS auction corridor €55–65/t → €65 (cap, conservative; aligns 05).
CO2_PRICE_EUR_T_2026 = 65.0
# EU ETS2 onset price — INDICATIVE; ETS2 postponed to 2028 (EU, Nov 2025).
CO2_PRICE_EUR_T_ETS2 = 80.0
ETS2_YEAR = 2028
# BEHG natural-gas emission factor (Heizwert). Estimate basis; real billing uses the
# supplier-reported Brennstoffemissionen.
GAS_EF_KG_KWH = 0.201

# Statutory residential 10-step model: (tier, min_kg_m2, max_kg_m2|None, landlord%, tenant%)
STAIR: list[tuple[int, float, float | None, int, int]] = [
    (1, 0.0, 12.0, 0, 100),
    (2, 12.0, 17.0, 10, 90),
    (3, 17.0, 22.0, 20, 80),
    (4, 22.0, 27.0, 30, 70),
    (5, 27.0, 32.0, 40, 60),
    (6, 32.0, 37.0, 50, 50),
    (7, 37.0, 42.0, 60, 40),
    (8, 42.0, 47.0, 70, 30),
    (9, 47.0, 52.0, 80, 20),
    (10, 52.0, None, 95, 5),
]

_NOTE = (
    "Landlord/tenant split under the CO2KostAufG. Residential/mixed buildings use the "
    "statutory 10-step model on kg CO₂ per m² of living area (Wohnfläche); non-residential "
    "uses the flat 50/50 split (NWG step model not yet in force). Heating-fuel CO₂ only "
    "(gas + oil). The 2026 price is within the €55–65/t nEHS auction corridor; the ETS2 "
    "forward figure is indicative (ETS2 starts 2028). Decision-support, not legal advice."
)


def _f(v: Any) -> float | None:
    return float(v) if v is not None else None


def _stair_tiers() -> list[Co2StairTier]:
    return [
        Co2StairTier(tier=t, min_kg_m2=lo, max_kg_m2=hi, landlord_pct=lp, tenant_pct=tp)
        for (t, lo, hi, lp, tp) in STAIR
    ]


def _resolve_tier(intensity_kg_m2: float) -> tuple[int, int, int]:
    """Return (tier, landlord_pct, tenant_pct) for a residential building."""
    for tier, lo, hi, lp, tp in STAIR:
        if intensity_kg_m2 >= lo and (hi is None or intensity_kg_m2 < hi):
            return tier, lp, tp
    return STAIR[-1][0], STAIR[-1][3], STAIR[-1][4]


def _base(fabric_building_id: str) -> Co2CostAllocationResponse:
    return Co2CostAllocationResponse(
        fabric_building_id=fabric_building_id,
        building_name="",
        building_type="",
        country_code=None,
        is_residential=False,
        reporting_year=None,
        has_data=False,
        floor_area_m2=None,
        area_basis="",
        heating_co2_tonnes=None,
        energy_content_kwh=None,
        co2_intensity_kg_m2=None,
        gas_emission_factor_kg_kwh=GAS_EF_KG_KWH,
        co2_price_eur_t=CO2_PRICE_EUR_T_2026,
        co2_price_eur_t_ets2=CO2_PRICE_EUR_T_ETS2,
        ets2_year=ETS2_YEAR,
        total_co2_cost_eur=None,
        total_co2_cost_eur_ets2=None,
        model="",
        tier=None,
        landlord_pct=None,
        tenant_pct=None,
        landlord_cost_eur=None,
        tenant_cost_eur=None,
        landlord_cost_eur_ets2=None,
        tenant_cost_eur_ets2=None,
        stair=_stair_tiers(),
        note=_NOTE,
        data_source="",
    )


def get_co2_cost_allocation(fabric_building_id: str) -> Co2CostAllocationResponse:
    """Heating-fuel CO₂ cost split (CO2KostAufG) for one building."""
    master = fabric_sql.execute_query(
        """
        SELECT building_id, building_name, building_type, country_code, gross_floor_area_m2
        FROM [dbo].[silver_building_master]
        WHERE building_id = ?
        """,
        (fabric_building_id,),
    )
    resp = _base(fabric_building_id)
    if not master:
        return resp
    b = master[0]
    btype = b.get("building_type") or ""
    is_residential = "residential" in btype.lower()
    resp.building_name = b.get("building_name") or fabric_building_id
    resp.building_type = btype
    resp.country_code = b.get("country_code")
    resp.is_residential = is_residential
    resp.model = "stair_10" if is_residential else "flat_50_50"

    heating_t: float | None = None
    intensity_area: float | None = None
    energy_kwh: float | None = None
    year: int | None = None

    # Residential: official Wohnfläche basis from the residential pipeline.
    # Fetch per-unit rows so we can both aggregate (Σ Wohnfläche, Σ heating) and
    # build the per-dwelling area-pro-rata breakdown further down.
    unit_rows: list[dict[str, Any]] = []
    if is_residential:
        unit_rows = fabric_sql.execute_query(
            """
            SELECT unit_id, area_m2, heating_dhw_kwh_annual
            FROM [dbo].[gold_residential_unit_kpi]
            WHERE building_id = ?
            ORDER BY unit_id
            """,
            (fabric_building_id,),
        )
        kwh = sum((_f(r.get("heating_dhw_kwh_annual")) or 0.0) for r in unit_rows) or None
        wf = sum((_f(r.get("area_m2")) or 0.0) for r in unit_rows) or None
        if kwh is not None and kwh > 0:
            heating_t = kwh * GAS_EF_KG_KWH / 1000.0
            energy_kwh = kwh
            intensity_area = wf
            resp.area_basis = "Wohnfläche (living area)"
            resp.data_source = "gold_residential_unit_kpi (Σ heating × BEHG gas EF); CO2KostAufG model"

    # Non-residential, or residential without unit data → gold_ghg_scope Scope-1 fuels.
    if heating_t is None:
        year_val = fabric_sql.execute_scalar(
            "SELECT MAX(reporting_year) FROM [dbo].[gold_ghg_scope] WHERE building_id = ?",
            (fabric_building_id,),
        )
        if year_val is not None:
            year = int(year_val)
            rows = fabric_sql.execute_query(
                """
                SELECT SUM(COALESCE(scope1_gas_tco2, 0) + COALESCE(scope1_diesel_tco2, 0))
                       AS heating_co2_tonnes
                FROM [dbo].[gold_ghg_scope]
                WHERE building_id = ? AND reporting_year = ?
                """,
                (fabric_building_id, year),
            )
            heating_t = _f(rows[0].get("heating_co2_tonnes")) if rows else None
            if heating_t is not None:
                energy_kwh = heating_t * 1000.0 / GAS_EF_KG_KWH
        intensity_area = _f(b.get("gross_floor_area_m2"))
        resp.area_basis = "gross floor area"
        resp.data_source = "gold_ghg_scope (Scope-1 gas+diesel) + silver_building_master; CO2KostAufG model"

    resp.reporting_year = year
    resp.floor_area_m2 = intensity_area
    resp.heating_co2_tonnes = round(heating_t, 2) if heating_t is not None else None
    resp.energy_content_kwh = round(energy_kwh, 0) if energy_kwh is not None else None

    if heating_t is None or intensity_area is None or intensity_area <= 0:
        return resp  # known building, no heating-CO₂ basis yet → doc shows a notice

    intensity = round(heating_t * 1000.0 / intensity_area, 1)
    cost_2026 = round(heating_t * CO2_PRICE_EUR_T_2026, 0)
    cost_ets2 = round(heating_t * CO2_PRICE_EUR_T_ETS2, 0)

    if is_residential:
        tier, lp, tp = _resolve_tier(intensity)
    else:
        tier, lp, tp = None, 50, 50

    resp.has_data = True
    resp.co2_intensity_kg_m2 = intensity
    resp.total_co2_cost_eur = cost_2026
    resp.total_co2_cost_eur_ets2 = cost_ets2
    resp.tier = tier
    resp.landlord_pct = lp
    resp.tenant_pct = tp
    resp.landlord_cost_eur = round(cost_2026 * lp / 100.0, 0)
    resp.tenant_cost_eur = round(cost_2026 * tp / 100.0, 0)
    resp.landlord_cost_eur_ets2 = round(cost_ets2 * lp / 100.0, 0)
    resp.tenant_cost_eur_ets2 = round(cost_ets2 * tp / 100.0, 0)

    # Per-dwelling breakdown (residential only): split the building heating-CO₂
    # cost by each unit's living-area share (Wohnfläche pro-rata). This is an
    # ESTIMATE — an area split, NOT per-unit metering; the statute distributes the
    # tenant portion by measured consumption. The same building step % applies to
    # every unit (the tier is set by the building's overall intensity).
    if is_residential and unit_rows and intensity_area and intensity_area > 0:
        heating_kg = heating_t * 1000.0
        units: list[Co2UnitAllocation] = []
        for r in unit_rows:
            a = _f(r.get("area_m2"))
            if a is None or a <= 0:
                continue
            share = a / intensity_area
            u_cost = cost_2026 * share
            units.append(
                Co2UnitAllocation(
                    unit_id=str(r.get("unit_id")),
                    area_m2=round(a, 1),
                    area_share_pct=round(share * 100.0, 1),
                    co2_kg=round(heating_kg * share, 0),
                    cost_eur=round(u_cost, 2),
                    landlord_cost_eur=round(u_cost * lp / 100.0, 2),
                    tenant_cost_eur=round(u_cost * tp / 100.0, 2),
                )
            )
        resp.units = units
        resp.unit_count = len(units)
    return resp
