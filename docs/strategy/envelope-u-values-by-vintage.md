# EnergyLens — Envelope U-Values by Construction Vintage (Method & Source)

> **Status:** APPROVED approach (Mert, 2026-06-12) — *platform-wide, year_built → typical U*.
> **Principle:** every value is **indicative / screening-grade**, states its basis, and cites a
> source. A building-specific energy audit (real measured U-values) always supersedes these ranges.
> **Single source:** the table below is materialised as the Fabric reference table
> `ref_envelope_u_by_vintage` (built in `00_reference_data_loader.py`) and consumed by
> `04_simulation_engine.py`.

## 1. Why this exists

The simulation engine estimates a building's **current** envelope heat loss to size heat-pump and
insulation measures. It previously applied **one hard-coded "current" U-value to every building**
(`WALL_U_CURRENT = 0.60`, roof `0.25`, window `2.80` W/m²K). That value is roughly a 1980s–90s wall —
too good for a 1970s building, too poor for a 2018 one. For B011 (1973 MFH) it understated the heat
demand by ~½ (77 vs ~103 kWh/m²·yr space-heat transmission) and produced a heat pump that *lost*
money. The fix reads each building's **construction year** (`silver_building_master.year_built`) and
looks up a **typical as-built component U-value for that era**.

## 2. The vintage → U table (typical as-built, W/m²K)

Construction-era U-values are primarily set by the building-energy code in force when the building
was built. We anchor the bands to the German regulatory breaks (WSchV 1977 / 1984 / 1995 → EnEV
2002 / 2009 / 2014 → GEG 2020), using the IWU **TABULA** residential building typology for the
empirical pre-code values and the regulatory component limits thereafter.

| Construction era | Regulatory basis | Wall U | Roof U | Window U |
|---|---|---:|---:|---:|
| ≤ 1918 (Gründerzeit) | Pre-norm (DIN 4108 from 1952) | 1.5 | 1.0 | 2.7 |
| 1919–1948 | Pre-norm | 1.4 | 1.0 | 2.7 |
| 1949–1968 (post-war) | Pre-WSchV | 1.4 | 0.9 | 2.8 |
| **1969–1978** | **Pre-WSchV / DIN 4108** | **1.2** | **0.8** | **2.7** |
| 1979–1983 | WSchV 1977 | 0.8 | 0.5 | 2.8 |
| 1984–1994 | WSchV 1984 | 0.6 | 0.45 | 2.8 |
| 1995–2001 | WSchV 1995 | 0.5 | 0.30 | 1.8 |
| 2002–2008 | EnEV 2002 / 2004 | 0.40 | 0.30 | 1.7 |
| 2009–2013 | EnEV 2009 | 0.28 | 0.20 | 1.4 |
| 2014–2019 | EnEV 2014 / 2016 | 0.24 | 0.20 | 1.3 |
| ≥ 2020 | GEG 2020 / 2024 | 0.24 | 0.20 | 1.3 |

The **1969–1978** row (1.2 / 0.8 / 2.7) is bolded because it is B011's band and matches the
independently-stated "U before" column of `residential-retrofit-calculations.md` exactly.

## 3. How the engine uses it (resolution order)

In `04_simulation_engine.py`, each simulated building resolves its envelope U-values as:

1. **Current U** — `year_built` range-joined to `ref_envelope_u_by_vintage` → era U-values.
2. **Target U** (post-retrofit) — per-building `target_*_u_value` from `ref_simulation_inputs`.
3. **Fallback** — if `year_built` is missing (no band) or no explicit target, the original module
   constants apply (`WALL_U_CURRENT 0.60` / `WALL_U_TARGET 0.20`, etc.). So any building without a
   vintage behaves exactly as before — **zero silent regression**.

Heat-pump product selection was also corrected: a residential MFH (`RESIDENTIAL_MF`) no longer
auto-selects a ground-source heat pump on the >2000 m² rule (urban apartment blocks rarely drill
geothermal) — it gets an air-source unit, matching the calc doc.

## 4. Scope of impact

Only buildings that have a row in `ref_simulation_inputs` are simulated (the engine inner-joins it):
currently **B001, B002, B003, B011**. So this change moves the heat-pump / insulation economics for
those four only; B004–B010 are untouched (they were never simulated). For the three commercial
buildings the vintage values (B001 2005, B002 1998, B003 2018) are **better** than the old 0.60/2.80
constant, so their computed envelope losses — and any insulation savings — **decrease**, which is the
more correct result (a 2018 logistics hub should not show a large wall-insulation payback). Re-check
their recommendations after re-running.

## 5. Honesty notes (must be surfaced)

1. **Screening-grade, not an audit.** These are *typical* values for an era, not the specific
   building. Real walls vary with construction, partial past renovations, and thermal bridges.
2. **Non-residential approximation.** TABULA is a *residential* typology. Component U-values by era
   are code-driven and broadly transfer to offices/retail/logistics, but the German non-residential
   typology (IWU **ENOB:dataNWG**) would refine them — a deferred enhancement.
3. **Space-heat transmission, not total consumption.** The engine's HDD × U-area method estimates
   transmission heat loss; a consumption baseline (e.g. the calc doc's 150 kWh/m²·yr) also includes
   domestic hot water, ventilation and distribution losses, so the two will not be identical.
4. **Heat-pump economics stay price-sensitive.** With cheap gas and a standard electricity tariff a
   gas→heat-pump switch is near break-even in DE; its real lever is CO₂ pricing (ETS2) and
   regulation, exactly as the retrofit calc doc states.

## 6. Sources

- [IWU TABULA — German residential building typology (Episcope)](https://www.iwu.de/research/gebaeudebestand/tabula-en/?L=1)
- [TABULA Scientific Report Germany — IWU (Episcope PDF)](https://episcope.eu/fileadmin/tabula/public/docs/scientific/DE_TABULA_ScientificReport_IWU.pdf)
- [Wärmeschutzverordnung 1977 / 1984 / 1995 — energie-experten.org](https://www.energie-experten.org/energie-sparen/energieberatung/gebaeudeenergiegesetz/waermeschutzverordnung)
- [Entwicklung der Regelwerke zur Energieeinsparung (WSchV→EnEV→GEG) — BauNetz Wissen](https://www.baunetzwissen.de/nachhaltig-bauen/fachwissen/regelwerke/entwicklung-der-regelwerke-zur-energieeinsparung-674672)
- [Beispielhafte U-Werte (typical U-values) — BBSR GEG-Portal](https://www.bbsr-geg.bund.de/GEGPortal/DE/Praxishilfen/Wirtschaftlichkeit/Tabellen/PDF/UWerte.pdf)
- Pairs with: `residential-retrofit-calculations.md` (the retrofit method this feeds).
