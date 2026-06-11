# EnergyLens — Pilot Readiness Report (Step 1 dry-run)

_Date: **2026-06-11** · Author: senior copilot pass · Scope: can a real pilot start, what is
verified, what the founder must run in Fabric._
_Related: [`architecture/iot-capacity-decision.md`](./architecture/iot-capacity-decision.md) ·
[`architecture/self-serve-fabric-bridging.md`](./architecture/self-serve-fabric-bridging.md) ·
[`architecture/data-connection-architecture.md`](./architecture/data-connection-architecture.md)_

> Note: this doc lives at `docs/pilot/…`; the relative links above point up one level to `docs/`.

## 1. Verdict

- **GO** for a **Tier-1, meter/bill-only pilot today** — with **zero Fabric dependency** for the
  customer. The upload → baseline-KPI → advisor path is verified energy-logic-correct (§2).
- **Deep Power-BI analytics** still require a **founder-run bridge** into your Fabric (§4). The
  customer never needs a Fabric account either way — this is the app-owns-data / ISV model.
- **Capacity story locked:** production default **① Decouple**, today **④ static-snapshot (€0)**
  — see the capacity decision record.
- **Key re-scoping (§6):** a typical first pilot (meter-only) shows Pages 1–6 (+Solar if PV);
  Pages 8/9 are **module-gated OFF**, so their known visual bugs are **not pilot-blocking** for
  pilot #1. This pulls the pilot *forward*.

## 2. What the dry-run verified (live engines, real-shaped data)

The backend Tier-1 engines were exercised directly (pure functions, no DB) against messy /
partial data a real customer would upload. **All sanity assertions passed.**

### 2a. Baseline KPI engine (`services/baseline_kpi.py`)

| Scenario | Result | Correct? |
|---|---|---|
| DE office, 14 mo + cost, 4200 m² | trailing-12; EUI **100**; CO₂ **152,460 kg** (=420,000×0.363); cost **actual** | ✅ |
| TR retail, 5 mo, no cost, 1200 m² | **annualized_from_5**; TR factor **0.442**; cost **estimated** @0.085; annual 216,000 | ✅ |
| DE, 12 mo, **no floor area** | EUI **None** (never invented) | ✅ |
| Empty (0 rows) | `has_data=False`, all KPIs null | ✅ |
| Messy: unsorted 3 mo, mixed cost | sorted to 2026-01…03; cost falls back to **estimated** | ✅ |
| 2026 periods, factor table ends 2025 | resolver **carries forward 2025** (never raises) | ✅ |

### 2b. Bridge readiness / data-tier gating (`services/bridge_readiness.py`)

| Profile | Tier | Pages |
|---|---|---|
| Office, 14 mo, meter-only (**typical pilot #1**) | baseline | **5 ready + 1 partial**; HVAC/IoT/Battery/Solar honestly **locked** |
| Retail, 5 mo, partial | baseline | 4 ready + 1 partial (trends partial, forecast locked) |
| Full package (IoT+battery+solar) | full | 8 ready + 2 partial |

### 2c. Ingestion parsers (the customer's first touch)

- **CSV (frontend `lib/api/consumption.ts`)** — code review: BOM strip, delimiter auto-detect
  (`, ; tab |`), quoted fields, EU `1.234,56` vs US `1,234.56`, EN/DE/TR month names. Robust.
- **PDF bill (`services/bill_parser.py`)** — tested live: DE table (EU numbers) → 3 clean rows;
  TR text (₺) → kWh parsed, cost honestly `None`; US-format `€` → correct. ✅

## 3. Minor findings / watch-items (none block the pilot)

1. **Reference-data currency.** Grid factors end **2025** (DE 0.363 carried forward; TR 0.442) and
   the tariff table has **only 2025** rows. A 2026 pilot silently uses 2025 (correct fallback) —
   but the UI should keep showing the provenance flag (`confidence`, `co2_factor_year`) so the
   carry-forward is visible. Refresh the `ref_` layer when 2026 values publish.
2. **EU thousands assumption.** `parse_number("12.345")` → **12345** (lone dot read as thousands).
   Right for DE/TR bills; would misread a rare US "12.345" decimal. Acceptable default; document it.
3. **TR cost in ₺ isn't captured** (parser matches only €/EUR), so a TR pilot's cost is always
   `estimated`. Fine given DE-primary positioning; note for TR deals.
4. **Tier-1 engines ARE unit-tested** (`backend/tests/test_baseline_kpi.py`, `test_bill_parser.py`,
   `test_bridge_readiness.py` — 379 lines), now wired to CI via `.github/workflows/backend-ci.yml`
   (added 2026-06-11). Remaining gap: the **frontend TS CSV parser** is code-reviewed only — add a
   small JS/TS unit test.

## 4. NOT verified here — founder runbook (needs your Fabric / Power BI)

These cannot run in the sandbox; run them once against a real pilot building. **This is the
remaining half of Step 1.**

1. **Onboard** the pilot building in-app → confirm it gets a Postgres UUID, `fabric_building_id=NULL`.
2. **Upload** its CSV/bill → `GET /buildings/{uuid}/kpis` returns a sane baseline (confirms the
   live wire end-to-end; the math is already proven in §2).
3. **Bridge** (founder): run the medallion notebooks parameterised for this building → land
   Bronze→Silver→Gold; mint `fabric_building_id` (B0xx); write it into `silver_building_master` /
   `dim_building`; `PATCH buildings.fabric_building_id` so the app flips pending → live.
4. **RLS + semantic model:** add the building to the Power BI RLS role mapping; refresh the model.
5. **RLS isolation test (the critical one).** Log in as a **second** customer/org that owns a
   *different* building. Confirm **customer A sees only their building(s), B sees only theirs** —
   no cross-leak in **any** visual, slicer, or filter, in **both** the embedded report **and** the
   custom reads (`/portfolio`, `/actions`, `/alerts`, pyodbc path).
6. **Pass criteria:** zero cross-customer rows anywhere · pending→live flip works · module-gated
   pages (8/9) stay locked for a no-IoT/no-battery building.

## 5. Capacity story (locked)

Production default **① Decouple** (Event Hubs + existing Container App → hot store; Fabric for
historical batch). **Today: ④ static-snapshot, €0.** F64 not required (app-owns-data embed works
on any F-SKU). Full rationale + migration trigger: `architecture/iot-capacity-decision.md`.

## 6. What this sets up for Step 2 (report punch-list)

The dry-run **re-scopes** the report work. For a meter-only pilot #1, only Pages 1–6 (+Solar if
the building has PV) are ever shown — Pages 8/9 are gated OFF. Therefore:

- **Prioritise (pilot-blocking):** Page 1–2 EUI/climate-adjust + peak (B1/B3), Page 3 single
  anomaly engine (C1/C4), Page 4 forecast F-import + confidence band (E1/E3), Page 5 tariff/relabel
  (F1/F3), Page 6 final ESG labels, **single demo-data record** (A4/I1).
- **Defer (NOT pilot-blocking unless the pilot has IoT/battery):** Page 8 broken visuals, Page 9
  ROI/RTE bug, Page 10 specific-yield. Fix these only when a pilot actually has those modules.

This means the "Page 8 is all broken" worry does **not** block your first pilot. Step 2 should
start at Pages 1–5 polish + the demo-data consolidation.
