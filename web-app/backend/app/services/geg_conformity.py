"""GEG conformity service (building grain).

Screens one building against the German Gebäudeenergiegesetz (GEG), reusing the
compliance gold table (notebook 05):

  * §71 — renewable heating: new/replaced heating must use ≥65% renewable energy. This
    binds at the NEXT heating replacement, phased on the municipal heat-planning
    (Kommunale Wärmeplanung) timeline — cities >100,000 from 2026, smaller from 2028;
    connection to a (planned) heat or H2 network also satisfies it. So it is a
    "next-replacement" duty, not an immediate retrofit.
  * §48 / Anlage 7 — component U-value limits that apply WHEN a component is renovated
    (>10% of its area): exterior wall ≤ 0.24, roof ≤ 0.24 (pitched) / 0.20 (flat),
    windows ≤ 1.30 W/m²K. §47 additionally requires top-floor-ceiling insulation.

Reads GEG flags + current U-values from gold_compliance_results and building info from
silver_building_master. Visibility is enforced by the router (404) before calling.

— ENERGY / LEGAL ASSUMPTIONS (STATED — reviewer: Mert) —
  * Limits per GEG Anlage 7. We display the roof limit as 0.20 (matching notebook 05's
    geg_roof_compliant flag, the flat-roof value); pitched roofs may use 0.24 — noted.
  * heating_compliant = the building's heating is already a renewable-compliant system
    (heat pump / district heat / biomass / solar thermal). The §71 timeline is shown as
    context; the actual trigger is the next heating replacement + municipal heat planning.
  * Screening / decision-support, not a formal GEG Nachweis or legal advice.
"""
from typing import Any

from app.integrations import fabric_sql
from app.integrations import gold_read
from app.schemas.geg_conformity import GegComponent, GegConformityResponse

# GEG Anlage 7 component U-value limits (W/m²K).
WALL_U_LIMIT = 0.24
ROOF_U_LIMIT = 0.20  # flat-roof / notebook-05 value; pitched roof ≤ 0.24
WINDOW_U_LIMIT = 1.30

_HEATING_NOTE = (
    "GEG §71: new or replaced heating must use ≥65% renewable energy. This binds at the "
    "next heating replacement — phased on the municipal heat-planning timeline (cities "
    ">100,000 inhabitants from 2026, smaller municipalities from 2028). Connection to a "
    "(planned) heat or hydrogen network also satisfies it. Existing compliant systems: "
    "heat pump, district heat, biomass, solar thermal."
)

_NOTE = (
    "GEG (Gebäudeenergiegesetz) conformity — screening. Envelope U-value limits "
    "(Anlage 7 / §48) apply when a component is renovated (>10% of its area); §47 also "
    "requires top-floor-ceiling insulation within 24 months of purchase. §71 (65% "
    "renewable heating) applies at the next heating replacement on the municipal "
    "heat-planning timeline. Decision-support, not a formal Nachweis or legal advice."
)
_SOURCE = "gold_compliance_results (GEG flags + current U-values) + silver_building_master"


def _f(v: Any) -> float | None:
    return float(v) if v is not None else None


def _b(v: Any) -> bool | None:
    return bool(v) if v is not None else None


def _base(fabric_building_id: str) -> GegConformityResponse:
    return GegConformityResponse(
        fabric_building_id=fabric_building_id,
        building_name="",
        building_type="",
        country_code=None,
        applies=False,
        has_data=False,
        geg_score=None,
        geg_status=None,
        heating_compliant=None,
        heating_note=_HEATING_NOTE,
        components=[],
        components_compliant=0,
        components_total=0,
        note=_NOTE,
        data_source=_SOURCE,
    )


def get_geg_conformity(fabric_building_id: str) -> GegConformityResponse:
    """GEG conformity screening for one building."""
    master = gold_read.query(
        """
        SELECT building_id, building_name, building_type, country_code
        FROM [dbo].[silver_building_master]
        WHERE building_id = ?
        """,
        (fabric_building_id,),
    )
    resp = _base(fabric_building_id)
    if not master:
        return resp
    b = master[0]
    resp.building_name = b.get("building_name") or fabric_building_id
    resp.building_type = b.get("building_type") or ""
    resp.country_code = b.get("country_code")
    resp.applies = (b.get("country_code") or "").upper() == "DE"

    comp = gold_read.query(
        """
        SELECT geg_score, geg_status, geg_heating_compliant,
               geg_wall_compliant, geg_roof_compliant, geg_window_compliant,
               wall_u_value_current, roof_u_value_current, window_u_value_current
        FROM [dbo].[gold_compliance_results]
        WHERE building_id = ?
        """,
        (fabric_building_id,),
    )
    if not comp:
        return resp  # known building, compliance not computed yet → doc shows a notice
    c = comp[0]

    resp.has_data = True
    resp.geg_score = _f(c.get("geg_score"))
    resp.geg_status = c.get("geg_status")
    resp.heating_compliant = _b(c.get("geg_heating_compliant"))

    components = [
        GegComponent(
            component="Exterior wall",
            current_u=_f(c.get("wall_u_value_current")),
            limit_u=WALL_U_LIMIT,
            compliant=_b(c.get("geg_wall_compliant")),
        ),
        GegComponent(
            component="Roof / top ceiling",
            current_u=_f(c.get("roof_u_value_current")),
            limit_u=ROOF_U_LIMIT,
            compliant=_b(c.get("geg_roof_compliant")),
            note="Flat-roof limit; pitched roof ≤ 0.24 per Anlage 7.",
        ),
        GegComponent(
            component="Windows",
            current_u=_f(c.get("window_u_value_current")),
            limit_u=WINDOW_U_LIMIT,
            compliant=_b(c.get("geg_window_compliant")),
        ),
    ]
    resp.components = components
    resp.components_total = len(components)
    resp.components_compliant = sum(1 for x in components if x.compliant is True)
    return resp
