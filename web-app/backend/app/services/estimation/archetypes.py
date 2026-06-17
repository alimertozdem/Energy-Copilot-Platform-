"""Archetype priors (L0) + heating fraction (A1) + monthly heating shape (A4).

Ported from the Fabric ``ref_building_type_profiles`` table and validated against
external benchmarks (2026-06-17 research pass):
  * Residential band + heat_frac calibrated to Heizspiegel 2025 (MFH gas
    heating+DHW reference ~114 kWh/m2/yr, range ~70-200) and the RWI/AGEB
    Anwendungsbilanz (residential space-heating + hot-water ~80% of final energy)
    -> band 90-180 -> 100-240, heat_frac 0.65 -> 0.72.
  * Non-residential bands cross-checked vs CIBSE TM46 typical benchmarks
    (e.g. general office: elec 95 + fossil-thermal 120 = ~215 kWh/m2/yr total).
Static module (matches reference_factors.py / baseline_estimate.py convention);
screening-grade -- a real building can sit +-30%+ inside its type.
"""
from typing import NamedTuple, Optional


class Archetype(NamedTuple):
    building_type: str
    eui_lo: float           # kWh/m2/yr, total final energy = heating + DHW + electricity
    eui_hi: float
    heat_frac: float        # A1: heating + DHW share of total final energy (climate-sensitive)
    modeled: bool = True


# (eui_lo, eui_hi, heat_frac). heat_frac signed off 2026-06-17; Residential
# revised in the 2026-06-17 research pass (band 90-180 -> 100-240, hf 0.65 -> 0.72).
_PROFILES: dict[str, tuple[float, float, float]] = {
    "Office":      (120.0, 220.0, 0.40),
    "Retail":      (180.0, 320.0, 0.30),
    "Hotel":       (220.0, 380.0, 0.45),
    "Healthcare":  (250.0, 450.0, 0.35),
    "Logistics":   (40.0, 110.0, 0.55),
    "Residential": (100.0, 240.0, 0.72),
    "School":      (60.0, 190.0, 0.55),
    "Lab":         (200.0, 520.0, 0.45),
    "Mixed":       (120.0, 220.0, 0.45),
}
_DEFAULT = (120.0, 220.0, 0.45)
# IT load dominates -> an area-based estimate is not meaningful; show no number.
_UNSUPPORTED = {"datacenter", "data_center"}

# DE heating-energy monthly shape (share of annual heating per calendar month),
# screening-grade, HDD-proportional (Central-EU). Normalised at use. (A4)
HEATING_MONTHLY_SHAPE = [0.170, 0.145, 0.120, 0.075, 0.035, 0.012,
                         0.006, 0.008, 0.030, 0.078, 0.135, 0.166]

_SYNONYMS = {
    "office": "Office", "buro": "Office", "buerogebaeude": "Office",
    "retail": "Retail", "shop": "Retail", "mall": "Retail", "ekz": "Retail",
    "hotel": "Hotel", "hospitality": "Hotel",
    "healthcare": "Healthcare", "hospital": "Healthcare", "clinic": "Healthcare",
    "krankenhaus": "Healthcare",
    "logistics": "Logistics", "warehouse": "Logistics", "lager": "Logistics",
    "industrial": "Logistics",
    "residential": "Residential", "residential_mf": "Residential", "apartment": "Residential",
    "mehrfamilienhaus": "Residential", "mfh": "Residential", "housing": "Residential",
    "school": "School", "university": "School", "education": "School", "schule": "School",
    "lab": "Lab", "laboratory": "Lab", "research": "Lab",
    "mixed": "Mixed", "mixed_use": "Mixed", "other": "Mixed",
}


def _normalize(building_type: Optional[str]) -> Optional[str]:
    if not building_type:
        return "Mixed"
    key = str(building_type).strip()
    if key in _PROFILES:
        return key
    low = key.lower()
    if low in _SYNONYMS:
        return _SYNONYMS[low]
    if key.title() in _PROFILES:
        return key.title()
    return None


def get(building_type: Optional[str]) -> Optional[Archetype]:
    """Resolve an archetype, or ``None`` for deliberately-unmodeled types
    (e.g. Datacenter) where an honest area-based estimate is impossible."""
    bt = (building_type or "").strip().lower()
    if bt in _UNSUPPORTED:
        return None
    norm = _normalize(building_type) or "Mixed"
    lo, hi, hf = _PROFILES.get(norm, _DEFAULT)
    return Archetype(building_type=norm, eui_lo=lo, eui_hi=hi, heat_frac=hf, modeled=True)
