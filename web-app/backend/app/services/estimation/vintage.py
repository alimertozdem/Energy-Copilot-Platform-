"""Vintage -> band position p in [0,1] (A3, signed off 2026-06-17).

Older, pre-thermal-regulation stock sits toward the HIGH (worse) end of the
archetype EUI band; newer stock toward the LOW end. We REPOSITION within the
band rather than multiply it, which avoids double-counting vintage with the
archetype band that already spans old->new. Era cut points mirror the German
WSchV / EnEV / GEG component-U regime (ref_envelope_u_by_vintage).
"""
from typing import Optional


def band_position(construction_year: Optional[int]) -> Optional[float]:
    if not construction_year:
        return None
    try:
        y = int(construction_year)
    except (TypeError, ValueError):
        return None
    if y <= 1978:      # pre-WSchV (uninsulated)
        return 0.85
    if y <= 1994:      # WSchV 1977/1984
        return 0.60
    if y <= 2008:      # WSchV 1995 / EnEV 2002
        return 0.40
    if y <= 2015:      # EnEV 2009/2014
        return 0.20
    return 0.10        # GEG 2016+
