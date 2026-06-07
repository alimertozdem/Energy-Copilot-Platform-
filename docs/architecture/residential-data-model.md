# Residential Data Model & Resident Identity — P1·1c design

**Status:** DRAFT design — the last design step before the P1 migration. **No DDL executed.**
**BMAD layer:** Data (entities, grain, identity) — implements the access model.
**Builds on:** `unified-access-model.md` (the access/authorization spine),
`residential-segment-architecture.md` (§3.1, §4).
**Grounded in the real repo:** building dimension = `silver_building_master`
(building_type is Title-Case, e.g. `Office`; area column = `conditioned_area_m2`);
benchmarks = `ref_building_type_profiles` (EUI + nZEB target per type); lakehouse naming is
`silver_* / gold_* / ref_*` (there is **no** `dim_*` table convention).

---

## 1. Two stores, one key discipline

The model spans the **same two stores already in production** — we add to both, we do not
introduce a third:

| Store | Holds | Residential additions |
|---|---|---|
| **Fabric lakehouse** (analytics) | medallion Bronze/Silver/Gold, **no resident PII** | unit grain + per-unit KPIs |
| **Postgres** (control plane) | orgs, users, buildings, billing, audit, overlays | unit records + **resident identity** |

**Cross-store key discipline (carry the existing building bridge):** Postgres `buildings`
already links to analytics via **`fabric_building_id`**. We mirror that exactly: a Postgres
`units` row carries **`fabric_unit_id`** that equals `silver_unit_master.unit_id`. The single
-FK chain stays **`org_id → building_id → unit_id`**, and **resident identity (PII) lives only
in Postgres** — never in the lakehouse.

---

## 2. Fabric analytics layer

### 2.1 `silver_building_master` — column deltas

```
+ unit_count        INT        -- number of residential units (NULL for non-residential)
+ common_area_m2    DOUBLE     -- Allgemeinfläche (shared/common heated area)
  building_type      STRING     -- residential rows carry 'RESIDENTIAL_MF' (the existing profile + measures token)
```
Schema evolution follows the existing pattern (mergeSchema / drop-recreate as used today).
`conditioned_area_m2` (already present) remains the **building-level** EUI denominator.

### 2.2 `ref_building_type_profiles` — `RESIDENTIAL_MF` profile **already exists** ✅

> **Correction after grounding the real loader:** an earlier draft of this doc claimed this
> row was missing and that the EUI/nZEB join would break. **That was wrong.**
> `notebooks/reference/00_reference_data_loader.py` already defines a **`RESIDENTIAL_MF`**
> profile (the 9th building type — *Mehrfamilienhaus*) with EUI bands
> **50 / 80 / 120 / 180 / 40** (excellent / good / average / poor / nZEB, kWh/m²·yr), and the
> token is already used in the measures-applicability reference data. **No profile migration
> is required.**

The approved E2 values (50 / **75** / **115** / 180 / 40) differ from the in-code values only
at `good` (80) and `average` (120) — a ≤5 kWh cosmetic gap. **Recommendation: keep the
existing in-code values** (production, dormant until a residential building exists,
sourced-equivalent to the Energieausweis scale). An optional nudge to 75 / 115 is available
but adds churn for no analytical benefit.

### 2.3 NEW `silver_unit_master`  *(naming refinement of "dim_unit")*  **[CONFIRM]**

```
silver_unit_master
  unit_id          STRING   PK          -- business key; == Postgres units.fabric_unit_id
  building_id      STRING   FK -> silver_building_master.building_id
  floor            STRING                -- e.g. 'EG','1','2' (DE floor labels)
  area_m2          DOUBLE                -- per-unit heated living area  (basis decided in E1)
  unit_type        STRING                -- enum, see E4
  is_heated        BOOLEAN               -- excludes unheated cellars/garages from KPI denom
  -- NO names, NO emails, NO tenant PII
```

**Why `silver_unit_master`, not `dim_unit`:** the repo has no `dim_*` tables; the building
dimension is literally `silver_building_master`. Naming the unit dimension `silver_unit_master`
keeps the convention consistent and self-documenting. (The brief's `dim_unit` was a generic
placeholder.)

### 2.4 Forward references — designed now, **built in P2/P3** (not P1)

- **Silver:** submetered sources gain the `unit_id` grain →
  `{building_id, unit_id, timestamp, energy_type, value, unit}` (P2 ingestion).
- **Gold:** per-unit **climate-adjusted (HDD) heating kWh/m²/yr** (the §8.6 KPI), common-area
  split (default 70/30, §3.2), and **UVI-ready monthly aggregates** (P3).

P1 only creates the **dimension + the column hooks**; the measures land with their data.

---

## 3. Postgres control-plane layer

### 3.1 Consultant skeleton — `org_type` + `partner_client_link`

Specified in `unified-access-model.md` §2 (approved). Listed here so the **P1 migration
manifest is in one place** — see §6. Not re-detailed.

### 3.2 NEW `units` (mirrors the `buildings` bridge)

```sql
units
  id               PK
  building_id      FK -> buildings(id)          -- Postgres buildings (already has fabric_building_id)
  fabric_unit_id   text UNIQUE                   -- == silver_unit_master.unit_id (the bridge)
  label            text                          -- human label, e.g. 'Whg 3.2' (manager-facing)
  created_at       timestamptz
```

### 3.3 NEW `resident_identity` (minimal PII, magic-link first)

```sql
resident_identity
  id               PK
  email            citext        -- the only required PII
  display_name     text NULL
  status           ENUM('invited','active','disabled')  DEFAULT 'invited'
  created_at       timestamptz
  -- consumption data is NEVER stored here; it stays in the lakehouse, read via fabric_unit_id
```

### 3.4 NEW `unit_resident` (tenancy window — privacy-critical)  **[CONFIRM]**

```sql
unit_resident
  id                    PK
  unit_id               FK -> units(id)
  resident_identity_id  FK -> resident_identity(id)
  valid_from            date          -- move-in
  valid_to              date NULL     -- move-out (NULL = current)
  status                ENUM('active','ended')  DEFAULT 'active'
  INDEX (unit_id, valid_to)
```

**Why a tenancy window and not a simple FK:** apartments turn over (*Mieterwechsel*). A
resident must see **only consumption within their `valid_from..valid_to`** — a former tenant
must not see the new tenant's usage, and a new tenant must not see history before move-in.
This is both **DSGVO correctness** and **billing correctness**. The §3 `resolve_scope`
resident path therefore filters consumption by the tenancy window, not just by `unit_id`.

### 3.5 NEW `resident_invite_token` (magic-link) + optional account

```sql
resident_invite_token
  id               PK
  unit_resident_id FK -> unit_resident(id)
  token_hash       text          -- store a hash, never the raw token
  expires_at       timestamptz
  consumed_at      timestamptz NULL
```

**Default = passwordless magic-link** bound to the `unit_resident` row. **Optional full
account** for residents who want one is an *additive* credential on `resident_identity`
(separate from the paying B2B NextAuth users) — built only if a resident opts in, **not** on
the P1 critical path.

---

## 4. Privacy posture (carry the compliance-hub rule)

- **No resident PII in the lakehouse.** Analytics sees `unit_id` only; the email/name live in
  Postgres `resident_identity`. Data minimization by construction.
- **Purpose-based exposure** (§4 of the access model): managers/partners see named per-unit
  data **only in the billing/cost-allocation purpose**; benchmark is always anonymized.
- **Tenancy-scoped access** (§3.4): consumption visibility follows move-in/move-out.
- Position as *"EED/HKVO-aligned support"*, never a legal guarantee; DSGVO retention policy
  to be set before resident go-live (P4).

---

## 5. Energy & privacy decisions — **NEEDS APPROVAL** (this is the per-piece energy gate)

| # | Decision | Recommendation | Type |
|---|---|---|---|
| **E1** | Per-unit `area_m2` basis for the heating KPI denominator | **Wohnfläche (WoFlV living area)** — the legal DE residential standard; consistent with building-level `conditioned_area_m2` | **[ENERGY]** |
| **E2** | `RESIDENTIAL_MF` EUI bands | **Already in code** (50/80/120/180/40 ≈ approved 50/75/115/180/40); recommend keep existing | **[RESOLVED]** |
| **E3** | Tenancy window (`valid_from/valid_to`) so access follows *Mieterwechsel* | **Yes** — model it; required for DSGVO + billing correctness | **[CONFIRM]** |
| **E4** | `unit_type` enum values | `apartment`, `maisonette`, `commercial_unit` (mixed-use), `common_area` | **[ASSUMPTION]** |
| **E5** | Unit dimension name | **`silver_unit_master`** (convention-aligned) over `dim_unit` | **[CONFIRM]** |

---

## 6. Consolidated P1 migration manifest — **NOT executed (next gate)**

Two coordinated migrations, both **additive, zero data loss**:

**A — Fabric (a P1 notebook, e.g. `notebooks/transformation/2x_residential_model.py`):**
1. add `unit_count`, `common_area_m2` to `silver_building_master`; allow `Residential`.
2. ~~add the `Residential` row~~ — **already present**; `RESIDENTIAL_MF` exists in `00_reference_data_loader.py`. No action (optional value nudge only).
3. create `silver_unit_master`.

**B — Postgres (Alembic, after `unified-access-model.md` §7):**
1. create `units`, `resident_identity`, `unit_resident`, `resident_invite_token`.
2. enums for `resident_identity.status`, `unit_resident.status`.

Existing tables/notebooks for current (commercial) tenants are **untouched** → no regression.

---

## 7. Reuse vs. build-new

| Reuse (already built) | Build new (bounded) |
|---|---|
| `silver_building_master`, `ref_building_type_profiles` | + columns; + `Residential` profile row |
| Postgres `buildings.fabric_building_id` bridge | `units.fabric_unit_id` (same pattern) |
| medallion + schema-evolution pattern | `silver_unit_master` |
| NextAuth B2B users (untouched) | `resident_identity` + magic-link token (separate, lightweight) |
| overlay tables (alert_status, audit) | `unit_resident` tenancy window |

---

## 8. References

- Access model: `unified-access-model.md`
- Residential / consultant architecture: `residential-segment-architecture.md`
- Grounding: `notebooks/anomaly-detection/anomaly_detection.py` (silver_building_master,
  building_type casing), `notebooks/compliance/05_compliance_checker.py`
  (`ref_building_type_profiles` join).
