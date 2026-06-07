# Residential Ingestion (P2) — design & contracts

**Status:** DRAFT design — BMAD **Data** step for P2 (Block 2: hardware-free ingestion).
**Builds on:** `residential-data-model.md` (§2.4 forward refs), `residential-segment-architecture.md` (§3.2).
**Nothing executed yet** — this defines the contracts the P2 notebooks implement.

P2 turns building bills and heat-cost-allocation exports into normalized consumption, with
**no new hardware** — the data the building already produces. Two sources (built in sequence
inside P2, not literally simultaneously, to bound V1):

| # | Source | Grain | First |
|---|---|---|---|
| 1 | Building bill / meter — **CSV** | building | **P2-b (now)** — lowest friction, every building |
| 2 | Heat-cost allocation (**Techem / ista / Brunata**) — CSV today, API later | **unit + heating** | P2-c — foundation of the resident view |

---

## 1. Upload mechanism  **[NEEDS APPROVAL — the one P2 decision]**

**Recommendation for V1: a Lakehouse *Files* landing folder + a scheduled notebook.**
The customer (or the manager during onboarding) drops a CSV into a known Files path; the P2
notebook reads everything there, ingests it, and archives the file. This is **Fabric-native,
zero new infrastructure, and matches how every other notebook in this repo runs.**

```
Files/landing/residential/bills/*.csv       → P2-b (building bill)
Files/landing/residential/heatcost/*.csv     → P2-c (unit heat-cost)
Files/landing/residential/_archive/...        ← processed files moved here
```

*Deferred to P4 (packaging):* an in-app upload UX (frontend form → backend → Files). It is
**not** required to prove the pipeline and adds real surface (upload auth, storage, virus
scanning). The landing-folder path is the same target either way, so P4 layers on cleanly.

> Alternative considered: app-upload first. Rejected for V1 — more work, no analytics benefit,
> and it couples the data pipeline to the web tier before the pipeline is proven.

---

## 2. CSV contracts

### 2.1 Building bill / meter — `bills/*.csv`  (building grain)

| Column | Type | Notes |
|---|---|---|
| `fabric_building_id` | string | must match `silver_building_master.building_id` (e.g. `B011`) |
| `period_start` | date `YYYY-MM-DD` | billing period start |
| `period_end` | date `YYYY-MM-DD` | billing period end |
| `energy_type` | enum | `heating` · `electricity` · `dhw` · `gas` · `district_heat` · `oil` |
| `consumption_kwh` | float | normalized to kWh (the adapter converts m³/litres → kWh, see §4) |
| `cost_eur` | float? | optional; total cost for the period |
| `meter_id` | string? | optional |
| `source` | string | e.g. `utility_bill`, `manual` |

### 2.2 Heat-cost allocation — `heatcost/*.csv`  (unit grain)

| Column | Type | Notes |
|---|---|---|
| `fabric_building_id` | string | parent building |
| `fabric_unit_id` | string | must match `silver_unit_master.unit_id` (e.g. `B011-U0301`) |
| `period_start` / `period_end` | date | period |
| `energy_type` | enum | `heating` · `dhw` |
| `consumption_kwh` | float | the allocator's reading, normalized to kWh |
| `cost_eur` | float? | allocated cost (informational; HKVO split is applied in Gold/P3) |
| `allocation_basis` | enum | `consumption` · `area` (provenance only; the 70/30 split is computed in Gold) |

> Privacy: **no resident names/emails in these files** — only `fabric_unit_id`. Identity
> stays in Postgres `resident_identity` (data-model §1). The heat-cost export already works
> this way (it bills by unit, not by name).

---

## 3. Bronze → Silver contract

```
bronze_residential_bill        (raw bill rows, per file, + _ingest_file, _ingested_at)
bronze_residential_heatcost     (raw unit heat-cost rows, + _ingest_file, _ingested_at)
        │  (BillingAdapter family normalizes + validates against silver_building_master /
        │   silver_unit_master keys; rejects unknown building_id/unit_id to a _rejects table)
        ▼
silver_residential_consumption  (the unified normalized grain)
  building_id      STRING            -- fabric_building_id (FK silver_building_master)
  unit_id          STRING  NULL      -- fabric_unit_id (FK silver_unit_master); NULL = building-level
  grain            STRING            -- 'building' | 'unit'
  period_start     DATE
  period_end       DATE
  energy_type      STRING            -- normalized vocab (§2)
  consumption_kwh  DOUBLE
  cost_eur         DOUBLE  NULL
  source           STRING            -- 'utility_bill' | 'heatcost' | ...
  ingested_at      TIMESTAMP
```

`silver_residential_consumption` is the **single normalized table** both sources land in
(building rows have `unit_id = NULL, grain='building'`; heat-cost rows carry the unit). Gold
(P3) derives per-unit climate-adjusted kWh/m²/yr, the common-area split (HKVO 70/30), and the
UVI monthly aggregates from this one table.

---

## 4. Adapter pattern (reuse, don't reinvent)

Extend the existing Phase-2 framework (`notebooks/iot/00_iot_adapter_framework.py`) with a
**billing / submetering adapter family** — same idea that already normalizes IoT protocols:

```
BillingAdapter (base)            -- validate keys, normalize units → kWh, emit the Silver contract
  ├─ UtilityBillCsvAdapter        -- P2-b: bills/*.csv → building grain
  └─ HeatCostCsvAdapter           -- P2-c: heatcost/*.csv → unit grain
       (later: TechemApiAdapter / IstaApiAdapter — same Silver contract, API source)
```

**Unit normalization (energy logic, [ASSUMPTION] — confirm conversion factors):**
gas/oil/district-heat meters often read in m³ or litres; the adapter converts to kWh using
standard calorific values (natural gas ≈ 10 kWh/m³ × ~0.95 Zustandszahl; heating oil ≈ 10
kWh/litre). Where the bill is already in kWh (most district heat / electricity), pass through.
These factors are **stated, not hidden**, and configurable per source.

---

## 5. Sub-step sequence (within P2)

| Step | Scope | Output |
|---|---|---|
| **P2-a** (this doc) | contracts + sample CSVs + adapter plan | this file + `sample-data/residential/*.csv` |
| **P2-b** | building bill ingestion notebook | `bronze_residential_bill` → `silver_residential_consumption` (building grain) |
| **P2-c** | heat-cost unit ingestion | unit grain into the same Silver table (resident-view foundation) |
| **P3** (later) | Gold per-unit KPI + common-area split + UVI | `gold_*` (not P2) |

---

## 6. Carry-over decisions (already approved — do not re-litigate)

- Heating distribution = HKVO **70/30** default (applied in Gold/P3, not ingestion).
- Heating KPI = **climate-adjusted (HDD) kWh/m²/yr** (Gold/P3).
- Per-unit area basis = **Wohnfläche (WoFlV)** (E1).
- **No resident PII in the lakehouse** — identity only in Postgres.
- `building_type = 'Residential_MF'` → token `RESIDENTIAL_MF` (already in `ref_building_type_profiles`).
