# EnergyLens — GHG Accounting Methodology (Page 6 / `gold_ghg_scope`)

**Version:** 2026-06-08 (after WP1–WP5 reference-layer + engine upgrade)
**Owner:** Ali Mert Özdemir · **For:** academic methodology review, audit-readiness, client trust
**Engine:** `notebooks/gold/09_ghg_scope_engine.py` · **Reference layer:** `notebooks/sustainability/reference/03_ref_factors_tariffs_loader.py`

---

## 1. Standards followed

| Layer | Standard | How we apply it |
|-------|----------|-----------------|
| Methodology | **GHG Protocol Corporate Standard** | Scope 1 / 2 / 3 split |
| Scope 2 dual reporting | **GHG Protocol Scope 2 Guidance** | location-based **and** market-based |
| Scope 3 | **GHG Protocol Corporate Value Chain (Scope 3) Standard** | material categories only (Cat 1, Cat 13) |
| Disclosure mapping | **ESRS E1-6** (CSRD) | gross Scope 1, 2, 3 + total; both location & market for S2 |
| Refrigerants | **IPCC AR-x GWP-100** + **EU F-Gas Reg (EU) 2024/573** | fugitive Scope 1 |

This document states, per scope, **the formula, the data source, and whether the number is
disclosure-grade or an explicitly-flagged estimate.** Nothing is presented as more certain
than it is.

---

## 2. Reference layer — single source of truth

Every factor is read from a sourced, year-indexed reference table (not a hardcoded constant),
so each disclosed kg CO₂ is traceable to a raw factor — the lineage an auditor expects.

| Table | What | Source |
|-------|------|--------|
| `ref_grid_emission_factors` | location-based grid factor (country × year) | **UBA** (DE official series, 2024 = 0.363) · **EEA** (other EU) · TEİAŞ (TR 0.442) |
| `ref_residual_mix` | market-based no-instrument factor | **AIB European Residual Mixes 2024** (DE = 0.725) |
| `ref_fuel_factors` | gas / diesel factors | **DESNZ/DEFRA** (gas 0.201 kg/kWh) |
| `ref_refrigerant_gwp` | refrigerant GWP-100 | **IPCC** / EU F-Gas Reg 2024/573 Annex |
| `ref_embodied_carbon` | embodied benchmark by building type | **RICS WLCA / LETI / DGNB** |

---

## 3. Scope 1 — direct emissions

```
scope1_total = scope1_gas + scope1_diesel + scope1_refrigerant      [tCO₂e/month]
```

**Gas (stationary combustion).** Where a gas meter exists, metered fuel × gas factor. Where it
does not (current demo), a screening proxy: `heating_share (25% of electricity) / boiler_eff
(0.85) × gas_factor (0.201 kg/kWh)`. *→ replaced by metered gas the moment the pilot provides it.*

**Diesel (standby generator).** Only where `has_diesel`; small contribution.

**Refrigerant (fugitive) — WP3, new.**
```
scope1_refrigerant = Σ ( annual_topup_kg × GWP-100 ) / 1000
```
`topup_kg` (the refrigerant a technician adds = what leaked) comes from the **F-Gas logbook**
(mandatory under EU 2024/573), loaded into `silver_refrigerant_log`; GWP-100 from
`ref_refrigerant_gwp` (e.g. R-410A ≈ 2088, R-32 ≈ 675). **If no logbook table exists, this term
is 0 — we do not estimate it.** This closes the single most-forgotten Scope 1 source.

---

## 4. Scope 2 — purchased electricity (dual reporting)

```
scope2_location = grid_kwh × location_factor            (ref_grid_emission_factors)
scope2_market   = grid_kwh × market_factor
market_factor   = COALESCE( supplier_ef ,  residual_mix ,  location_factor )
```

**The methodological fix (WP2).** Market-based reporting follows the GHG Protocol Scope 2
factor hierarchy:

1. **Supplier-specific factor** — from a contractual instrument (Guarantee of Origin / PPA / green tariff).
2. **Residual mix** — when there is *no* instrument. This is **not** the location average:
   once renewables are sold via GoOs, the *remaining* mix is dirtier. For Germany 2024 the AIB
   residual mix is **0.725 kg/kWh vs the location factor 0.363 — nearly 2×.** Using location for
   an unbacked supply is a common audit failure; we now use the residual mix.
3. **Location factor** — only where no residual mix applies (Austria / Netherlands have full GO
   disclosure, so residual mix does not exist; or the table is absent).

`scope2_method` records which path was taken (`market_based_contract` /
`residual_mix_no_instrument` / `location_fallback_full_disclosure`).

---

## 5. Scope 3 — value chain (material categories only)

```
scope3_total = scope3_cat1_embodied + scope3_cat13_leased        (disclosure_grade = False)
```

**Category 1 — embodied / upfront carbon (WP4).**
```
scope3_cat1_embodied = floor_area_m² × embodied_kgCO₂e_m² / amortization_years / 12 / 1000
```
`embodied_kgCO₂e_m²` is a **published benchmark** by building type (RICS/LETI/DGNB), amortised
over a 60-year life. It is an **estimate**, flagged as such — not material-specific EPD data.

**Category 13 — downstream leased assets (tenant energy).** For a landlord this is usually the
largest Scope 3 bucket, but it requires real tenant consumption. **Currently 0, awaiting pilot
tenant data** — we do not fabricate it.

`scope3_disclosure_grade = False` and `scope3_method =
"cat1_embodied_benchmark+cat13_leased_pending"` travel with every row so the Power BI visual can
label Scope 3 honestly as *estimated, not disclosure-grade.*

---

## 6. Totals & ESRS E1-6 mapping

```
total_ghg_location = scope1_total + scope2_location + scope3_estimated
total_ghg_market   = scope1_total + scope2_market   + scope3_estimated
```

| ESRS E1-6 datapoint | Field |
|---------------------|-------|
| Gross Scope 1 | `scope1_total_tco2` |
| Gross Scope 2 (location-based) | `scope2_location_tco2` |
| Gross Scope 2 (market-based) | `scope2_market_tco2` |
| Gross Scope 3 | `scope3_estimated_tco2` (estimate-flagged) |
| Total GHG | `total_ghg_location_tco2` / `total_ghg_market_tco2` |

---

## 7. What is disclosure-grade today vs an estimate

| Number | Status | To make it fully audit-ready |
|--------|--------|------------------------------|
| Scope 2 location-based | **Disclosure-grade** (real consumption × sourced factor) | real meter data (pilot) |
| Scope 2 market-based | **Method-correct**; equals residual mix until contracts arrive | supply contract + GoOs |
| Scope 1 gas | Disclosure-grade with a gas meter; proxy otherwise | gas meter / bills |
| Scope 1 refrigerant | Method-correct; **0 until the F-Gas logbook is loaded** | F-Gas logbook (`silver_refrigerant_log`) |
| Scope 3 Cat 1 (embodied) | **Benchmark estimate**, flagged | material EPDs / a whole-life carbon assessment |
| Scope 3 Cat 13 (leased) | **Pending** (0) | tenant energy via green-lease clauses |

> **Honest framing for any audience:** *"Scope 1 and location-based Scope 2 are auditable with
> row-level lineage. Market-based Scope 2 is method-correct and uses the AIB residual mix until
> supplier contracts are connected. Scope 3 is a flagged, category-structured estimate. This is
> ESRS-E1-aligned reporting support — the auditor issues assurance, not the tool."*

---

## 8. Data lineage

```
raw bill / meter  →  silver_building_master (+ silver_refrigerant_log)
        +  reference layer (ref_grid / ref_residual_mix / ref_fuel / ref_refrigerant_gwp / ref_embodied)
                        ↓  09_ghg_scope_engine (this methodology)
                  gold_ghg_scope  →  Power BI Page 6 (ESRS E1-6 visuals)
```

---

## 9. Sources

- GHG Protocol — Corporate Standard, Scope 2 Guidance, Scope 3 Standard — ghgprotocol.org
- EFRAG — ESRS E1 (Climate change) — efrag.org
- UBA — German grid factor (363 g/kWh, 2024) — umweltbundesamt.de
- EEA — GHG emission intensity of electricity generation — eea.europa.eu
- AIB — European Residual Mixes 2024 (DE 724.56 gCO₂/kWh, Table 2) — aib-net.org/facts/european-residual-mix
- DESNZ/DEFRA — GHG conversion factors — gov.uk
- IPCC — GWP-100 values; EU F-Gas Regulation (EU) 2024/573 — eur-lex.europa.eu
- RICS Whole Life Carbon Assessment / LETI / DGNB — embodied-carbon benchmarks

*All factor values are web-verified (June 2026) and carry source + URL + year in the reference
tables. Re-verify annually; residual-mix and grid factors are published yearly.*
