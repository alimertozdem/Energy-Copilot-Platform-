# Unified 4-Level Access & Authorization Model
## Consultant (Partner) + Residential (Resident) — P1 design

**Status:** DRAFT design — schema direction approved (residential brief §9.3, 2026-06-04).
DDL / migration **not yet executed**; this document is the spec that migration will follow.
**BMAD layer:** Architecture → Data (access / authorization)
**Builds on:** `residential-segment-architecture.md` (§9 Consultant, §5 access crux),
the existing 3-layer access model, and the Day-15 / 23 / 25 / 29 platform findings.

---

## 1. One spine, two features

```
partner_org (consultant)         ← Level 0  advisory firm; manages many clients
  └─ client_org (building owner)  ← Level 1  the paying customer / Hausverwaltung
       └─ building                ← Level 2  existing grain
            └─ unit (resident)     ← Level 3  residential occupant
```

One authorization model serves the **consultant** layer (top) and the **resident** layer
(bottom). It reuses the existing **3-layer access** model — RLS (data) · AppNav (module) ·
tier (commercial) — and only **extends the data/RLS layer down to `unit` and up to
`partner`.**

**Only ONE new principal type: the `resident`** (a lightweight, unit-bound token). A
**partner is *not* a new principal** — it is an ordinary NextAuth user who is a **member of
an org whose `org_type = 'partner'`.** That is precisely why the consultant layer is cheap:
it rides the existing org-member + `/admin` cross-org machinery instead of inventing a second
tenancy system.

---

## 2. Control-plane schema deltas (Postgres)

### 2.1 `organizations.org_type`  *(refinement of approved §9.3)*

```sql
org_type  ENUM('customer','partner')  NOT NULL  DEFAULT 'customer'
```

- `customer` — a normal tenant that owns buildings. **Every existing org migrates to this →
  zero behavior change.**
- `partner` — an advisory / consultancy firm that manages *other* orgs' buildings; may own
  zero buildings of its own.

**Why two values, not the three (`standalone / client / partner`) sketched in §9.3:**
"client" is **not an intrinsic property of an org** — it is a *role in a relationship*. An org
is a "client" exactly when an active `partner_client_link` points at it, and the **same org
can be both self-serve and partner-assisted** at once. Encoding "client" as a column would
denormalize that fact and let it drift out of sync with the link. So we **derive**
client-status from the link and keep `org_type` minimal. (Platform-admin stays the existing
`is_platform_admin` *user* flag — it is not an org type.)

> **[CONFIRM]** This is a small normalization refinement of the approved §9.3 — same intent,
> fewer moving parts. Flagging it because it changes one approved detail.

### 2.2 `partner_client_link` — the only genuinely new table

```sql
partner_client_link
  id                    PK
  partner_org_id        FK organizations(id)   -- must be org_type = 'partner'
  client_org_id         FK organizations(id)   -- the managed customer org
  relationship_status   ENUM('pending','active','suspended','revoked')  DEFAULT 'pending'
  scope                 ENUM('read_only','full_manage')                 DEFAULT 'read_only'
  commission_model      JSONB         -- e.g. {"type":"percent","value":15,"currency":"EUR"}  [design-time]
  invited_by            FK users(id)
  client_consent_at     timestamptz   -- DSGVO: client must accept before status can be 'active'
  granted_at            timestamptz
  revoked_at            timestamptz NULL
  UNIQUE (partner_org_id, client_org_id) WHERE revoked_at IS NULL   -- one live link per pair
  INDEX (partner_org_id),  INDEX (client_org_id)
```

**Consent lifecycle (privacy-critical):** a partner **cannot self-grant** access. Flow:
`invite → pending → the client accepts (client_consent_at) → active`. Consumption data is
**personal data** (residents) and **commercially sensitive** (the client's portfolio); under
DSGVO the controller (client) must authorize the processor (partner). Revocation sets
`revoked_at` and access vanishes on the next `resolve_scope` call — **no client data is ever
copied to the partner; it is only *viewed through* the live grant.**

---

## 3. Scope resolution — the single authorization primitive

Everything downstream — Fabric reads, REST endpoints, page gating, PDF export — consumes
**one** resolver that maps a principal to the set of `building_id`s (and, for residents,
`unit_id`) it may read:

```python
def resolve_scope(principal) -> Scope:
    if principal.is_platform_admin:                         # existing /admin
        return Scope(buildings=ALL, write=ALL)

    if principal.kind == "resident":                        # NEW principal type
        return Scope(units={principal.unit_id},
                     building_benchmark=ANONYMIZED(principal.building_id),
                     write=NONE)

    org = principal.org
    if org.org_type == "partner":
        links      = active_links(partner_org_id=org.id)    # relationship_status = 'active'
        client_ids = [l.client_org_id for l in links]
        return Scope(buildings=buildings_of(client_ids),
                     write=writable_clients(links))          # only where scope = 'full_manage'

    # org_type == 'customer'  → identical to today
    return Scope(buildings=buildings_of([org.id]),
                 units=ALL_UNITS_IN(org),                    # manager: per-unit (HKVO billing)
                 write=org.id)
```

**Enforcement point = a backend `building_id` filter** (carry the proven read path). Per
**Day-15** (`pyodbc` + SQL Analytics Endpoint, not DAX) and **Day-29** (DirectLake embed
tokens **reject `effectiveIdentity`**), RLS is applied as a `building_id IN (…)` filter the
backend injects — **not** as a native Power BI RLS identity. A partner is therefore simply a
**wider `IN` list** (the union of its clients' buildings). **No new read-path mechanism and no
new risk** — the partner case is the existing customer case with a different building set.

---

## 4. The 4-level scope matrix (read vs. write)

| Level | Principal | Reads | Writes |
|---|---|---|---|
| **Platform admin** | founder (`is_platform_admin`) | everything | everything — audited |
| **Partner** | member of an `org_type='partner'` org | union of **active-linked** clients' buildings, bounded by `scope` | only where `link.scope='full_manage'`; **every write audited** as `actor=partner_user`, `on_behalf_of=client_org` |
| **Manager** | member of an `org_type='customer'` org | own org's buildings + **per-unit** (HKVO billing context) + common area | own org (unchanged) |
| **Resident** | unit-bound resident token | **own unit** + **anonymized** building benchmark + common-area share | none (own profile only) |

**Privacy rails** (carry §5 + the compliance-hub legal rule): **comparative / benchmark**
analytics are always anonymized + aggregated at *every* level; **named per-unit** data is
exposed to managers / partners **only in the billing / cost-allocation purpose**. Position as
*"EED / HKVO-aligned support"*, never a legal guarantee.

---

## 5. Module (AppNav) + tier layers — carry-over, unchanged mechanism

RLS decides *which rows*; it cannot hide *pages* (Power BI limitation — see the existing
app-access model). Page visibility stays in **AppNav**:

- **Partner** → a portfolio-of-portfolios **client switcher** — the **Day-23 `/admin`
  cross-org UI**, scoped to the partner's linked clients instead of all orgs. Direct reuse.
- **Resident** → only `/residence` (no Power BI embed — license + privacy + cost).
- **Manager** → today's page set; Residential buildings add heating pages (P3).

**Tier** (commercial) is unchanged: partner seats + commission are a partner-plan concern
(brief §9.5); **resident seats are free / included.**

---

## 6. Audit — partner accountability

Reuse `audit_logs` (Day 25 / 26). Partner mutations on client data write `action=partner.*`,
`actor=<partner user>`, plus an `on_behalf_of=<client_org_id>` field, so the client can later
see exactly *which consultant changed what*. This is both DSGVO accountability and a trust
feature that makes the delegated-access model safe to sell.

---

## 7. Migration sketch — **NOT executed (this is the next gate)**

Alembic, **additive only, zero data loss**:

1. create enum `org_type`; add the column to `organizations` (default `'customer'`, backfill
   existing rows).
2. create enums `relationship_status`, `link_scope`.
3. create table `partner_client_link` (+ partial unique index, FKs, indexes).
4. existing RLS / customer path **untouched** → no regression for current tenants.

Running this migration is a **separate approval gate** — *not* part of this design step.

---

## 8. Reuse vs. build-new

| Reuse (already built) | Build new (bounded) |
|---|---|
| `/admin` cross-org repo + router (Day 23) → partner client-switcher | `org_type` column · `partner_client_link` table |
| backend `building_id` filter (Day 15 / 29) | scope resolver: partner union + resident unit path |
| `audit_logs` (Day 25 / 26) | `on_behalf_of` on partner actions |
| AppNav module gating · tier | `resident` principal type (token) — detailed in P1·1c |
| NextAuth org members | *(partners need nothing new — they are org members)* |

---

## 9. Open items → carried to P1·1c + the migration gate

- Resident identity table + magic-link token shape + unit↔resident mapping → **P1·1c**.
- `dim_building` Residential fields + the `dim_unit` grain → **P1·1c**.
- `commission_model` exact shape + payout mechanism (Stripe Connect vs. invoice) →
  design-time, post-P1.
- `scope` enum starts `read_only` / `full_manage`; a future `billing_only` is possible.

---

## 10. References

- Residential / consultant architecture: `residential-segment-architecture.md`
- Growth / business layer: `../strategy/2026-06_growth_strategy.md`
- Platform findings carried here: Day-15 (pyodbc read path), Day-23 (`/admin` cross-org),
  Day-25/26 (audit logs), Day-29 (DirectLake `effectiveIdentity` blocked).
