"""financing.py — portfolio financing & subsidy summary (decision-support).

Joins the recommendation catalog (Fabric/Postgres gold_recommendations, same source
as /actions and the MACC) with the building master (type / EPC / area / country) and
runs the pure finance_model to produce, for everything the user can see:

  * Per-measure: unit-aware subsidy (programme, rate range, eligible cost, grant range),
    simple payback, and a base-scenario discounted NPV.
  * Portfolio: total CapEx, grant range, net after grant, and total NPV under THREE
    scenarios (conservative / base / high) that escalate energy + carbon prices.
  * Indicative EPC-driven value uplift for renovation-priority (F-G-H) buildings.
  * Full assumptions + currency stamp for a transparent method panel.

SUPPORT, NOT ADVICE. Every forward figure is screening-grade and shown as a range.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.integrations import fabric_sql, gold_read
from app.repositories import building as building_repo
from app.services import finance_model as fm
from app.services.abatement import _lifetime_for, _safe_float
from app.schemas.financing import (
    FinancingMeasure,
    FinancingPortfolio,
    FinancingResponse,
    FinancingScenario,
    FinancingValueUplift,
)

START_YEAR = 2026


def get_financing_for_user(
    db: Session,
    *,
    user_id: UUID,
    building_id: str | None = None,
    has_isfp: bool = False,
    limit: int = 500,
) -> FinancingResponse:
    """Portfolio financing summary for everything the user can see."""
    note = (
        "Indicative financing support — not financial advice. Subsidy programmes, "
        "bonuses and carbon prices change; verify against the live programme and apply "
        "BEFORE signing any contract. Forward figures are scenario ranges, not forecasts."
    )
    empty = FinancingResponse(
        measures=[],
        portfolio=FinancingPortfolio(scenarios=[]),
        assumptions=fm.assumptions(),
        note=note,
    )

    visible = building_repo.list_buildings_for_user(db, user_id=user_id)
    by_fid = {b.fabric_building_id: b for b in visible if b.fabric_building_id}
    fabric_ids = list(by_fid.keys())
    if not fabric_ids:
        return empty
    if building_id is not None:
        if building_id not in by_fid:
            return empty
        fabric_ids = [building_id]

    ph, params = fabric_sql.format_in_clause(fabric_ids)
    sql = f"""
    SELECT TOP (?)
        building_id, action_type, title_en,
        annual_saving_eur, co2_saving_kg, capex_eur, net_capex_eur
    FROM [dbo].[gold_recommendations]
    WHERE building_id IN ({ph})
    """
    rows = gold_read.query(sql, (limit, *params))

    measures: list[FinancingMeasure] = []
    # portfolio scenario accumulators
    scen_npv = {s: 0.0 for s in fm.SCENARIOS}
    tot_capex = tot_grant_low = tot_grant_high = tot_net = 0.0

    for r in rows:
        bid = r["building_id"]
        b = by_fid.get(bid)
        btype = getattr(b, "building_type", None)
        area = _safe_float(getattr(b, "floor_area_m2", None)) or None
        action_type = r.get("action_type")
        title = r.get("title_en")
        gross_capex = _safe_float(
            r.get("capex_eur") if r.get("capex_eur") is not None else r.get("net_capex_eur")
        )
        annual_saving = _safe_float(r.get("annual_saving_eur"))
        co2_t = _safe_float(r.get("co2_saving_kg")) / 1000.0

        units = fm.estimate_units(btype, area)
        sub = fm.estimate_subsidy(action_type, gross_capex, btype, units, has_isfp=has_isfp)
        grant_mid = (
            ((sub["grant_low_eur"] or 0) + (sub["grant_high_eur"] or 0)) / 2.0
            if sub["eligible"] else 0.0
        )
        net_capex = max(0.0, gross_capex - grant_mid)
        lifetime = _lifetime_for(action_type, title)
        payback = fm.simple_payback(net_capex, annual_saving)
        base = fm.npv_case(net_capex, annual_saving, co2_t, lifetime, "base", START_YEAR)

        measures.append(
            FinancingMeasure(
                building_name=getattr(b, "name", bid),
                fabric_building_id=bid,
                title=title or action_type or "Measure",
                action_type=action_type,
                program=sub["program"],
                scheme=sub["scheme"],
                eligible=sub["eligible"],
                rate_low_pct=sub["rate_low_pct"],
                rate_high_pct=sub["rate_high_pct"],
                eligible_cost_eur=sub["eligible_cost_eur"],
                grant_low_eur=sub["grant_low_eur"],
                grant_high_eur=sub["grant_high_eur"],
                units_basis=sub["units_basis"],
                subsidy_note=sub["note"],
                capex_gross_eur=round(gross_capex),
                net_capex_eur=round(net_capex),
                assumed_lifetime_years=lifetime,
                simple_payback_years=payback,
                npv_base_eur=base["npv_eur"],
            )
        )

        # Portfolio totals + scenario NPV use the grant-eligible measure set (solar/
        # other are funded separately and excluded from the financing case).
        if sub["eligible"] and gross_capex > 0:
            tot_capex += gross_capex
            tot_grant_low += sub["grant_low_eur"] or 0
            tot_grant_high += sub["grant_high_eur"] or 0
            tot_net += net_capex
            for s in fm.SCENARIOS:
                scen_npv[s] += fm.npv_case(net_capex, annual_saving, co2_t, lifetime, s, START_YEAR)["npv_eur"]

    measures.sort(key=lambda m: (m.npv_base_eur is None, -(m.npv_base_eur or 0)))

    scenarios = [
        FinancingScenario(
            scenario=s,
            total_npv_eur=round(scen_npv[s]),
            carbon_2030_eur_t=round(fm.carbon_price(s, 2030)),
            energy_inflation_pct=round(fm.ENERGY_INFLATION[s] * 100, 1),
        )
        for s in fm.SCENARIOS
    ]

    # Indicative value uplift for renovation-priority buildings (assume ~2-class lift).
    fg = [b for b in visible if (getattr(b, "epc_class", None) or "").strip().upper()[:1] in {"F", "G", "H"}]
    value_uplift = None
    if fg:
        sample = fm.value_uplift("F", "D")  # representative 2-band jump
        value_uplift = FinancingValueUplift(
            priority_buildings=len(fg),
            assumed_band_jump=2,
            uplift_low_pct=sample["uplift_low_pct"],
            uplift_high_pct=sample["uplift_high_pct"],
            note=(f"{len(fg)} renovation-priority building(s) (EPC F-G-H). A typical deep "
                  "retrofit lifts ~2 EPC classes; the 'green premium' is market-specific and "
                  "applies to your own valuation. Indicative estimate."),
        )

    portfolio = FinancingPortfolio(
        total_capex_gross_eur=round(tot_capex),
        total_grant_low_eur=round(tot_grant_low),
        total_grant_high_eur=round(tot_grant_high),
        total_net_after_grant_eur=round(tot_net),
        eligible_measure_count=sum(1 for m in measures if m.eligible),
        scenarios=scenarios,
        value_uplift=value_uplift,
    )
    return FinancingResponse(
        measures=measures, portfolio=portfolio, assumptions=fm.assumptions(), note=note
    )
