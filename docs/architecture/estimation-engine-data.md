# EnergyLens — Estimation Engine — Data Design (BMAD: Data)

> **Status:** DRAFT — pending product-owner approval. Follows `estimation-engine-architecture.md`
> (v0.2, approved 2026-06-17).
> **Purpose:** define the engine's **input schema**, **reference data**, and the **source assembler**
> that lets Tier A "cover all platform data" from Postgres alone.
> **Grounded in the live schema** — verified against Supabase project `energylens` (eu-central-1),
> 2026-06-17. *(Row-count/population check was blocked by a transient connector timeout; to confirm at
> backtest — see §4.)*

---

## 0. What the live database already gives us (verified)

**Key finding:** most inputs and almost all gold **already exist in Postgres**. The engine is largely an
**assembler + a thin reference port**, not new storage. This makes "cover all our databases' data"
achievable on the free path with **zero live Fabric bridge**. *[Kesin — schema verified; population
to confirm]*

- **`buildings`** (input / metadata) already carries: `building_type`, `floor_area_m2`,
  `construction_year`, `country_code`, `city`, `latitude`, `longitude`, `epc_class`,
  `floors_above_ground`, `heating_system`, `has_gas_heating`, `wall_u_value`, `roof_u_value`,
  `window_u_value`, `insulation_year`, `pv_capacity_kwp`.
- **`building_consumption`** (partial bill): `period` ('YYYY-MM'), `energy_kwh`, `cost_eur`, `source`.
- **`mv_` mirror** (Fabric gold in Postgres) is broad: `mv_building_master` (`conditioned_area_m2`,
  `year_built`, `climate_zone`, U-values, `energy_certificate`…), `mv_kpi_daily` (**real**
  `total_consumption_kwh`, `eui_kwh_m2`, `climate_adjusted_eui`, `hdd_day`, `cdd_day`…), plus
  `mv_ghg_scope`, `mv_compliance_results`, `mv_recommendations`, `mv_iot_daily_summary`,
  `mv_residential_*`, `mv_anomaly_log`, `mv_sync_log`.

**Three implications that change the design:**

1. **HDD is already in gold.** `mv_kpi_daily.hdd_day` exists for bridged buildings, so L2 reuses it
   there; a free HDD normal is only needed for *screening-only* buildings (no gold yet).
2. **L5 EPC is NOT dead for Germany.** `buildings.epc_class` / `mv_building_master.energy_certificate`
   are **user-entered**. The only DE-unavailable part is public-register **auto-lookup**. So
   L5 = anchor on user-supplied EPC class (available everywhere) + optional public auto-fill (UK).
3. **The estimate retires when real gold exists.** If `mv_kpi_daily` has consumption for the building,
   the engine surfaces the **actual** climate-adjusted KPIs instead of an estimate.

---

## 1. `EngineInput` — assembled, not a new table

A dataclass assembled from existing rows. Everything is optional except building type and
area-or-footprint; missing fields simply mean fewer layers fire (and a wider band).

| Field | Source | Layer | Required |
|---|---|---|---|
| `building_type` | `buildings.building_type` | L0 | yes (else default `Mixed`) |
| `floor_area_m2` | `buildings.floor_area_m2` → `mv_building_master.conditioned_area_m2` → L3 footprint | L0 / L3 | area or footprint |
| `construction_year` | `buildings.construction_year` / `mv.year_built` | L1 | optional |
| `country_code` · `climate_zone` · `lat/lon` | `buildings` / `mv_building_master` | L2 | optional |
| `epc_class` | `buildings.epc_class` / `mv.energy_certificate` | L5 | optional |
| partial bills | `building_consumption` (period, energy_kwh, cost_eur) | L4 | optional |
| real gold | `mv_kpi_daily` (consumption, climate-adj EUI, hdd) | retire-estimate | optional |

No new input table is needed — `EngineInput` is a **read-time assembly** over tables that already exist.

---

## 2. Reference data — Python modules, NOT new DB tables (decision)

The codebase convention for static reference knowledge is **hardcoded Python modules**
(`reference_factors.py`, `baseline_estimate.py`) — not DB tables. For a few hundred static rows this is
the better fit: **zero migration, zero DB latency, trivially unit-testable, keeps Tier A pure-functional,
and avoids adding to the RLS-off public-table surface.** So we port reference knowledge as modules:

| Module | Holds | Ported from |
|---|---|---|
| `archetype_profiles.py` | type → EUI low/typical/high · heating_share · monthly_shape | Fabric `ref_building_type_profiles` (supersedes the 7-entry dict in `baseline_estimate`) |
| `vintage_factors.py` | construction era → EUI multiplier band | Fabric `ref_envelope_u_by_vintage` |
| `climate_hdd.py` | HDD normal by `climate_zone` / country (handful of zones) | seeded **offline once** from open-meteo / DWD (free) |
| *(reuse)* `reference_factors.py` | tariff + grid emission factor | unchanged |

*Trade-off:* modules vs tables — if a customer ever needs **per-org archetype overrides**, revisit to a
table then. Not now. *[Muhtemel — modules are the right call at this scale]*

---

## 3. Source Assembler — the "cover all data" resolver (precedence)

Given a `building_id`, assemble the best-available evidence and pick the path, highest → lowest:

```
1. mv_kpi_daily has real consumption?   → ACTUAL  (climate-adjusted EUI already computed in gold)
                                          → estimate retires (available=false); surface real KPIs.   [bridged / deep]
2. else building_consumption has bills?  → L4 ANCHOR  (>=12 mo → baseline_kpi run-rate; <12 mo → seasonal blend)
3. else                                  → PRIOR  L0 archetype × L1 vintage × L2 HDD [× L5 user EPC]
   floor area:  buildings.floor_area_m2 → mv.conditioned_area_m2 → L3 footprint (gap-fill, wide band)
```

All reads are from **Postgres** (incl. the `mv_` mirror). The **deep tier (paid)** may additionally pull
**live Fabric gold**; the free/screening tier never does.

---

## 4. Gap table — present vs. to-build

| Status | Item |
|---|---|
| **Present** | `buildings` inputs · `building_consumption` · `mv_` gold (incl. `hdd_day`, `climate_adjusted_eui`) · `reference_factors` · `baseline_estimate` · `baseline_kpi` |
| **To build** (Logic / Impl) | `archetype_profiles.py` (port) · `vintage_factors.py` (port) · `climate_hdd.py` (offline-seed normals) · the **source assembler** · the per-layer math (L1/L2/L4 blend) · the **confidence scorer** |
| **To confirm** | `mv_` population / row counts (connector timed out at design time) → confirm at backtest |

---

## 5. Open decisions (for approval)

1. **Reference as Python modules** (recommended) vs DB tables. *(Matches convention; €0; pure-functional.)*
2. **HDD as static offline-seeded normals by `climate_zone`** (recommended) vs a live open-meteo call per
   request. *(Static keeps Tier A deterministic, offline, and €0.)*
3. **Confirm the assembler precedence:** real gold > partial bill > archetype prior.

> On approval → **Logic phase**: the per-layer math (how each layer shifts/narrows the band) + the
> confidence-and-range formula + the energy-domain assumptions for your sign-off.
