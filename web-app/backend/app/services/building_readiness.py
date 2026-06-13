"""Building readiness + Data Score engine.

Single source of truth for "what data unlocks which report" and the gamified
**Data Score** (0-100). The score measures DATA COMPLETENESS — not how sustainable
the building is — so a high score means "we can produce more reports for you",
which indirectly nudges the customer to provide more and act on more savings.

Stateless: `compute_readiness(attrs, consumption_months)` takes a plain dict of the
building's attributes + how many months of consumption exist, and returns the score,
the per-signal breakdown, the per-report status (ready / partial / locked / n.a.) and
the prioritised "add X → +N points → unlocks Y" actions. The same function backs the
GET endpoint (existing buildings) and the onboarding wizard's live preview.

Envelope U-values / insulation year are not yet stored on the Building model — the
attrs getter returns None for them, so they read as "missing" (GEG shows locked with an
"add U-values" action) until the comprehensive wizard + schema land. Forward-compatible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


# --- Signals: each unit of data the customer can provide -----------------------
@dataclass(frozen=True)
class Signal:
    key: str
    label: str
    points: int
    # present(attrs, consumption_months) -> the data is on file
    present: Callable[[dict, int], bool]
    # applicable(attrs) -> counts toward the score (e.g. PV only if the building has PV)
    applicable: Callable[[dict], bool] = field(default=lambda a: True)
    help: str = ""


def _has(attrs: dict, *keys: str) -> bool:
    return all(attrs.get(k) not in (None, "") for k in keys)


SIGNALS: list[Signal] = [
    Signal("consumption", "12 months of energy use", 30,
           lambda a, m: m >= 1, help="Upload a utility bill or monthly meter export."),
    Signal("area", "Floor area", 8, lambda a, m: _has(a, "area"),
           help="Gross / conditioned m² — drives every intensity figure."),
    Signal("building_type", "Building type", 4, lambda a, m: _has(a, "building_type")),
    Signal("construction_year", "Year built", 3, lambda a, m: _has(a, "construction_year")),
    Signal("country", "Country", 3, lambda a, m: _has(a, "country"),
           help="Sets the grid CO₂ factor and which national rules apply."),
    Signal("heating", "Heating system & fuel", 12, lambda a, m: _has(a, "heating_system"),
           help="Unlocks Scope 1, the CO₂ cost split and the GEG §71 heating check."),
    Signal("u_values", "Envelope U-values", 15,
           lambda a, m: _has(a, "wall_u_value", "roof_u_value", "window_u_value"),
           help="Wall / roof / window U-values unlock the GEG conformity check."),
    Signal("epc_class", "Energy certificate (EPC)", 6, lambda a, m: _has(a, "epc_class"),
           help="Makes the EPC exact (otherwise it is estimated from your EUI)."),
    Signal("insulation_year", "Insulation year", 4, lambda a, m: _has(a, "insulation_year")),
    Signal("occupants", "Typical occupants", 5, lambda a, m: _has(a, "typical_occupants")),
    Signal("pv", "Solar PV details", 7, lambda a, m: _has(a, "pv_capacity"),
           applicable=lambda a: bool(a.get("has_pv")) or a.get("pv_capacity") not in (None, ""),
           help="Capacity (kWp) + roof — unlocks the solar KPIs."),
]
SIGNAL_BY_KEY = {s.key: s for s in SIGNALS}


# --- Reports: required + improving signals -------------------------------------
@dataclass(frozen=True)
class ReportDep:
    key: str
    label: str
    required: tuple[str, ...]
    improving: tuple[str, ...] = ()
    applicable: Callable[[dict], bool] = field(default=lambda a: True)
    estimated_note: str = ""


REPORTS: list[ReportDep] = [
    ReportDep("energy", "Energy KPIs & EUI", ("consumption", "area")),
    ReportDep("ghg", "GHG Inventory (Scope 1/2/3)", ("consumption", "area"), ("heating", "country"),
              estimated_note="Scope 1 needs the heating fuel; Scope 3 is always estimated."),
    ReportDep("esrs", "ESRS E-1 (Climate)", ("consumption", "area")),
    ReportDep("vsme", "VSME report", ("consumption", "area")),
    ReportDep("gresb", "GRESB readiness", ("consumption", "area")),
    ReportDep("crrem", "CRREM stranding", ("consumption", "area", "country")),
    ReportDep("epc", "EPC pre-assessment", ("consumption", "area"), ("epc_class",),
              estimated_note="Estimated from your EUI; add the EPC class to make it exact."),
    ReportDep("geg", "GEG conformity", ("u_values", "heating"), ("insulation_year", "country")),
    ReportDep("co2_cost", "CO₂ Cost Split", ("heating", "area"), ("consumption",)),
    ReportDep("enefg", "EnEfG plan", ("consumption",)),
    ReportDep("recommendations", "Retrofit recommendations", ("consumption", "area"),
              ("heating", "u_values", "construction_year")),
    ReportDep("solar", "Solar KPIs", ("pv",), applicable=lambda a: bool(a.get("has_pv"))),
]


def compute_readiness(attrs: dict, consumption_months: int) -> dict:
    """Return the Data Score + per-signal + per-report readiness for a building."""
    present: dict[str, bool] = {}
    applicable: dict[str, bool] = {}
    for s in SIGNALS:
        applicable[s.key] = s.applicable(attrs)
        present[s.key] = applicable[s.key] and s.present(attrs, consumption_months)

    earned = sum(s.points for s in SIGNALS if present[s.key])
    possible = sum(s.points for s in SIGNALS if applicable[s.key]) or 1
    score = round(earned / possible * 100)

    signals_out = [
        {"key": s.key, "label": s.label, "points": s.points,
         "present": present[s.key], "applicable": applicable[s.key], "help": s.help}
        for s in SIGNALS
    ]

    reports_out = []
    for r in REPORTS:
        if not r.applicable(attrs):
            reports_out.append({"key": r.key, "label": r.label, "status": "not_applicable",
                                "missing": [], "note": ""})
            continue
        missing_req = [k for k in r.required if not present.get(k)]
        missing_imp = [k for k in r.improving if not present.get(k)]
        if missing_req:
            status = "locked"
        elif missing_imp or r.estimated_note:
            status = "partial"
        else:
            status = "ready"
        reports_out.append({
            "key": r.key, "label": r.label, "status": status,
            "missing": [SIGNAL_BY_KEY[k].label for k in (missing_req or missing_imp)
                        if k in SIGNAL_BY_KEY],
            "note": r.estimated_note if status == "partial" else "",
        })

    # Next best actions: missing+applicable signals, highest points first, with what they unlock.
    actions = []
    for s in sorted(SIGNALS, key=lambda x: -x.points):
        if applicable[s.key] and not present[s.key]:
            unlocks = [r.label for r in REPORTS if r.applicable(attrs)
                       and s.key in r.required
                       and all(present.get(k) or k == s.key for k in r.required)]
            actions.append({"key": s.key, "label": s.label, "points": s.points,
                            "help": s.help, "unlocks": unlocks})

    return {
        "data_score": score,
        "points_earned": earned,
        "points_possible": possible,
        "signals": signals_out,
        "reports": reports_out,
        "next_actions": actions,
    }


def building_attrs(building) -> dict:
    """Map a Building ORM row to the attrs dict (getattr so future columns just work)."""
    def g(name):
        v = getattr(building, name, None)
        return float(v) if hasattr(v, "__float__") and not isinstance(v, bool) else v
    pv = g("pv_capacity_kwp")
    return {
        "area": g("floor_area_m2"),
        "building_type": g("building_type"),
        "construction_year": g("construction_year"),
        "country": g("country_code"),
        "heating_system": g("heating_system"),
        "epc_class": g("epc_class"),
        "typical_occupants": g("typical_occupants"),
        "pv_capacity": pv,
        "has_pv": pv not in (None, "", 0, 0.0),
        # Envelope fields are not on the model yet — getattr returns None (missing).
        "wall_u_value": g("wall_u_value"),
        "roof_u_value": g("roof_u_value"),
        "window_u_value": g("window_u_value"),
        "insulation_year": g("insulation_year"),
    }
