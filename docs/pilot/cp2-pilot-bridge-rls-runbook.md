# EnergyLens — CP-2 Pilot Bridge & RLS Isolation Runbook (founder-run)

_A **runbook** = a step-by-step checklist **you** run in your Fabric / Power BI environment.
Format per step: **☐ action → ✅ verify → ⚠ if-fail.** This is the **go-live gate** for a real
pilot: it bridges one real building end-to-end and proves data never crosses customer
boundaries. Run it **after CP-1** (report renders)._

---

## Phase 0 — Prerequisites
- ☐ CP-1 complete (Pages 1–6 render with sane numbers).
- ☐ Pilot building **onboarded in-app** → has a Postgres UUID, `fabric_building_id = NULL` (pending).
- ☐ Its consumption **uploaded** (CSV/bill) → `GET /buildings/{uuid}/kpis` returns a sane baseline.
  - ✅ Baseline matches the Step-1 dry-run sanity (EUI / CO₂ = kWh×grid-factor / cost plausible).
- ☐ A **second** test org + building exists (different data) — needed for the isolation test in
  Phase 5. If not, create one and upload it a few months of (different) data.

## Phase 1 — Land the building's data in Bronze (Fabric)
- ☐ For a meter-only pilot, push the building's `building_consumption` rows into the Fabric
  **bronze** table (keyed by `building_id`). (A live building instead streams via the edge agent.)
- ✅ The bronze table contains this building's rows.

## Phase 2 — Transform Silver → Gold (parameterised by building)
- ☐ Run the medallion notebooks (silver → `03_gold_kpi_engine`) **parameterised for this
  `building_id`**.
- ✅ `gold_kpi_daily` has rows for this building, and the numbers are **comparable to the Postgres
  baseline** (same formulas → same ballpark).
- ⚠ If gold diverges wildly from the baseline, check unit / floor-area / country mapping for this building.

## Phase 3 — Assign + link the Fabric ID (pending → live)
- ☐ Mint a `fabric_building_id` (e.g. `B0xx`); write it into `silver_building_master` / `dim_building`.
- ☐ `PATCH buildings.fabric_building_id` (via `/admin` or DB) so the app flips the building **pending → live**.
- ✅ In-app the building shows **live** (not "data pending"); `/portfolio` lists it.

## Phase 4 — RLS + semantic model
- ☐ Add the building (and its org) to the **Power BI RLS** role mapping (the customer↔building map).
- ☐ **Refresh** the semantic model.
- ✅ Refresh succeeds with no RLS errors.

## Phase 5 — RLS isolation test  ⭐ (the critical gate)
- ☐ Log in as **Customer A** → open the embedded report **and** `/portfolio`, `/actions`,
  `/alerts`. Note A's building(s).
- ☐ Log in as **Customer B** (different org/building) → same pages.
- ✅ **A sees only A's building(s); B sees only B's** — in **every** visual, slicer and filter, and
  in **both** the embedded report **and** the custom (pyodbc) reads.
- ☐ Edge probes: from A's session, deep-link to B's `building_id` → must be **denied / empty**;
  change slicers/filters → **no** B rows ever appear for A.
- ⚠ **Any** cross-customer row = **STOP, do not pilot.** The RLS map or a row-filter is wrong; fix
  before exposing the building.

## Phase 6 — Module-gating sanity
- ✅ The meter-only pilot building shows **Pages 1–6**; **Pages 8/9 stay LOCKED** (no IoT/battery).
  Confirms the data-tier gating matches `bridge_readiness` (Step-1 §2b).

## Phase 7 — Go / No-Go
**GO** only if all hold: baseline ↔ gold consistent · pending→live flip worked · **zero
cross-customer leakage** · module gating correct.

---

### Done-definition
A real pilot building is **live in Fabric**, the customer sees **only their own data** across the
embedded report + custom reads, and the deep analytics render for exactly the pages the data
earns. This is the moment a paying pilot can safely begin.
