"""Assemble an ``EngineInput`` from platform rows (the "cover all data" resolver).

Tier A reads everything from Postgres: the ``buildings`` row (type, area, year,
country, EPC, floors, heating fuel) + uploaded ``building_consumption`` rows
(partial bills) + optionally a ``gold`` dict mirrored from Fabric (conditioned
area, climate zone, annual HDD). No Fabric / network here -- the caller supplies
already-loaded ORM objects; the engine stays pure.
"""
from __future__ import annotations

from typing import Optional

from app.services.estimation.engine import EngineInput


def _f(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def build_engine_input(building, rows, gold: Optional[dict] = None,
                       year: int = 2025) -> EngineInput:
    """Map a Building ORM object + its consumption rows (+ optional gold dict)
    onto the engine's input contract."""
    g = gold or {}

    bills = []
    for r in (rows or []):
        period = getattr(r, "period", None)
        kwh = getattr(r, "energy_kwh", None)
        if period and kwh is not None:
            bills.append((period, _f(kwh), _f(getattr(r, "cost_eur", None))))

    def bv(name):
        return getattr(building, name, None)

    return EngineInput(
        building_type=bv("building_type"),
        floor_area_m2=_f(bv("floor_area_m2")),
        conditioned_area_m2=_f(g.get("conditioned_area_m2")),
        construction_year=bv("construction_year"),
        country_code=bv("country_code"),
        climate_zone=g.get("climate_zone"),
        hdd_annual=_f(g.get("hdd_annual")),
        epc_class=bv("epc_class"),
        bills=bills,
        footprint_m2=_f(g.get("footprint_m2")),
        floors_above_ground=bv("floors_above_ground"),
        building_height_m=_f(bv("building_height_m")),
        has_gas_heating=bv("has_gas_heating"),
        heating_system=bv("heating_system"),
        year=year,
    )
