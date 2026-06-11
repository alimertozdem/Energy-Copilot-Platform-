# CP-2 — Embedded-Report RLS: Smoke Test & Design (decision-gated)

_Status: **PROPOSED 2026-06-11.** This gates CP-2 Phase 4–5 for the **embedded Power BI
report**. The custom (pyodbc) reads — `/portfolio`, `/actions`, `/alerts` — are already
server-side isolated (`_get_visible_fabric_ids` derives the building-id list from the JWT user's
org); this document is **only** about closing the embedded-report gap._

## 0. The gap (why this exists)

The logged-in app mints its embed token via `main.py /embed/token`, which sends **no
`identities[]`/effectiveIdentity** — the token can read the **entire** semantic model (all orgs,
all buildings). Isolation today is a **client-side building-id filter** in the browser. That is a
UX convenience, **not** a security boundary: a customer can lift the filter via devtools and read
another customer's buildings. CP-2 Phase 5 ("zero cross-customer leakage in the embedded report,
in every visual/slicer/filter") therefore **fails an adversarial probe** as built.

The capability to fix this already exists: `app/integrations/pbi_embed.py` mints
effectiveIdentity tokens for the public `/demo` (a single static `Demo` role → B001–B006). The
work is to (a) generalise that to a **dynamic** per-customer role and (b) route the logged-in
endpoint through it. **But** memory `feedback_pbi_directlake_rls.md` records that the DirectLake
model once **rejected** `identities[]` at GenerateToken. So we **smoke-test the mechanism live
before wiring anything**.

---

## 1. Target design — dynamic RLS via `CUSTOMDATA()`

**Pattern:** app-owns-data multi-tenant embedding. Customers have **no** AAD identity, so we use
`CUSTOMDATA()` (not `USERNAME()`): the backend stamps the caller's **visible building-id list**
into the embed token's `customData`; one static DAX role filters the model to it server-side.

**Why this is the right fit (not USERNAME-based RLS):**

- **No AAD identity needed** — customers never have one; `CUSTOMDATA()` carries the scope directly.
- **No mapping table in the model, no per-customer model change.** The customer→building map
  already lives in **Postgres** (onboarding writes it). USERNAME-based RLS would force us to
  duplicate that map into the model and refresh it on every new customer. `CUSTOMDATA()` avoids
  that entirely → **new-customer onboarding is zero-touch on the model side** (see §3.2).
- **One source of truth.** The exact list `_get_visible_fabric_ids()` already computes for the
  pyodbc pages is what we put in `customData`. Both read paths scope identically — they can never
  drift.

### 1.1 The DAX role (apply once in the semantic model)

Create a role **`CustomerRLS`** with a table filter on the building dimension
(`silver_building_master` — the dim with active relationships to every fact table, so the filter
cascades to all 10 pages):

```DAX
PATHCONTAINS( CUSTOMDATA(), silver_building_master[building_id] )
```

- `customData` is a `|`-delimited list, e.g. `"B001|B004|B007"`. `PATHCONTAINS` does whole-token
  matching, so `B001` never false-matches `B0011`, and a single building (`"B001"`) works too.
- **Fail-closed:** if `customData` is blank, the filter returns nothing → no accidental wide-open
  token. (Founder/internal viewing happens directly in the workspace, **not** through this token,
  so it is unaffected by the role.)
- **Cascade requirement:** every fact table (`gold_kpi_daily`, GHG, forecast, …) must filter
  *through* `silver_building_master[building_id]` via an active relationship. Step A below checks
  this across pages — if a page stays unfiltered, that fact table needs its relationship to the
  building dim (or its own role filter).

---

## 2. The smoke test (~15 min) — run this BEFORE any code change

Two layers. **A** proves the DAX cascades correctly; **B** proves DirectLake accepts the token
(the historical failure point). Both must pass.

### Step A — Model-side: cascade check (proves the DAX)
1. Open the semantic model (Fabric web model editor; or Power BI Desktop **only if** the model is
   local — a live-connection report has *Manage roles / View as* disabled, which is expected).
2. Add the `CustomerRLS` role. In the **Tables** list **select `silver_building_master`** and
   enter the DAX above **on that table** — *not* on `Date` or a fact table. (RLS DAX runs in the
   **row context of the table it's attached to**; `building_id` only resolves to a single value
   per row on `silver_building_master`. On any other table you get *"a single value for column
   'building_id' … cannot be determined."*) There is only **one** `CustomerRLS` role — *edit* it,
   don't create a second one (duplicate name = error). Leave every other table **unfiltered**.
3. **Cascade check via a TEMPORARY static rule.** No UI dialog can supply `customData` — *View as*
   only sets roles + USERNAME, and on a live-connection report it's disabled entirely. So to prove
   the filter *cascades*, **temporarily** change the rule to a literal:
   `silver_building_master[building_id] = "B001"`. Then test it — Desktop **View as →
   `CustomerRLS`**, or in the Fabric service the model's **Security → Test as role** — and walk
   Pages 1–6: every visual shows **only B001**.
   - ⚠ If a page stays unfiltered → that fact table doesn't cascade from `silver_building_master`;
     fix its relationship before continuing.
4. **Revert** the rule to `PATHCONTAINS( CUSTOMDATA(), silver_building_master[building_id] )` and
   Save. The real `customData` test is **Step B** (the token) — because no modelling UI inputs
   customData, the embed token is the *only* way to exercise the dynamic path.

### Step B — Token-side: does DirectLake accept effectiveIdentity? (the real risk)
From `web-app/backend` with your `.env` loaded:

```bash
# bash / macOS / Linux:
RLS_CUSTOMDATA="B001" python scripts/smoke_embed_rls.py
# PowerShell (Windows):
$env:RLS_CUSTOMDATA="B001"; python scripts/smoke_embed_rls.py
```

- ✅ **`STATUS 200`** → DirectLake **accepts** dynamic RLS. The historical block is gone. Proceed
  to §3 (wire it). Then paste the printed `token` + `embed_url` + report id into
  `scripts/embed_viewer.html` (open it in a browser) and confirm only B001 renders.
- ❌ **`STATUS 400`** with a DirectLake/identity message → the block is still there. **Do not
  wire.** Go to §4 (fallback).

### Pass criteria (the gate)
**GO** to §3 only if **A** (DAX filters all pages) **and** **B** (`200`) both pass.

---

## 3. IF IT PASSES — wiring + the operational flow

### 3.1 Backend wiring — DONE (2026-06-11): main.py + route.ts

_Implemented inline in `main.py /embed/token` (endpoint is self-contained; `pbi_embed.py` left
untouched as the logged-in path doesn't route through it). Backend `py_compile` + frontend
`tsc --noEmit` both clean. The endpoint is now authenticated, resolves `list_buildings_for_user`,
and sends `identities[customData]`; the frontend route forwards the session Bearer; the client
filter stays as belt-and-suspenders. **Runtime gate Mert runs: log in -> report shows only your
buildings.** The plan steps below are the spec it was built from._
1. **`pbi_embed.generate_embed_token`** — add a `custom_data: str | None = None` param; when set,
   add `"customData": custom_data` to the `identities[0]` dict (alongside username/roles/datasets).
2. **`main.py /embed/token`** — make it **authenticated** (`Depends(get_current_user_id)`); reuse
   the **same** `_get_visible_fabric_ids` logic the portfolio router uses; join the list with `|`;
   call `generate_embed_token(..., rls_username="rls@energylens.app", rls_roles=["CustomerRLS"],
   custom_data=<list>)`. (Empty list → fail-closed token, renders nothing — correct.)
3. **`frontend/app/api/embed-token/route.ts`** — **forward the `Authorization` header** to the
   backend (today it deliberately doesn't). Without the JWT the backend can't identify the user.
4. **`PowerBIReport.tsx`** — the client-side building filter becomes belt-and-suspenders (keep for
   UX/default view; it is no longer the boundary).
5. **`/demo` is untouched** — it keeps its own static `Demo` role via the existing public endpoint.

### 3.2 New-customer flow (the part you asked about) — RLS is zero-touch

Once `CustomerRLS` exists, **onboarding a new customer requires no RLS or model change at all:**

```
1. Sign up / onboard      -> Postgres org + building(s), fabric_building_id = NULL (pending).
2. Upload CSV / bill      -> Tier-1 baseline KPIs immediately (Postgres only, zero Fabric).
                            Customer sees baseline analytics on day one.
3. Founder bridge         -> medallion notebooks (parameterised for the building) -> Bronze->Gold;
   (deep analytics)         mint fabric_building_id (B0xx) -> write into silver_building_master;
                            PATCH buildings.fabric_building_id  -> app flips pending -> live.
4. Customer logs in       -> backend computes THIS user's building-id list from their Postgres org
                            membership (same list_buildings_for_user), stamps it into customData.
                            -> Embedded report + pyodbc pages both show ONLY their buildings.
```

**Why nothing per-customer is needed in the model:** the role is **one static rule**
(`PATHCONTAINS(CUSTOMDATA(), …)`); the *who-sees-what* lives in Postgres and is computed fresh on
every token request. No new role, no mapping row, no model refresh for RLS. The only model-side
action per customer is what the bridge already does — land their gold rows (DirectLake picks them
up). **That is the clean SaaS property:** add a customer = the existing onboarding + bridge;
isolation "just works" because both read paths derive scope from the same Postgres org→building
map.

---

## 4. Smoke-test result (2026-06-11) — RESOLVED via Fix A

**Outcome: Fix A worked.** After binding the model's OneLake data source to a fixed-identity
**Service Principal** connection (SSO **off**) in *Settings -> Cloud connections*, `GenerateToken`
with `identities[customData]` returns **`STATUS 200`** — server-side dynamic RLS is **GO** on Direct
Lake, no Import needed. The 403 below was the pre-fix state.

**Result: `STATUS 403` — `"Creating embed token with effective identity is not supported for this
datasource"`.** Per [Integrate Direct Lake Security](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-security-integration),
this is **not** a hard wall — it is the **default SSO** connection mode. A Direct Lake model defaults
to SSO (Microsoft Entra ID) and reads OneLake as *the current querying user*. App-owns-data embed has
only the service principal + embed token — no interactive user to SSO with — so effectiveIdentity is
refused. (This also explains why `/demo`'s "Demo role" never really applied server-side — it fell back
to the client filter.)

### Fix A — bind the model to a FIXED-IDENTITY cloud connection (recommended — keeps Direct Lake)
The documented pattern for embedded / read-only-consumer Direct Lake:
1. Semantic model → **Settings → Gateway and cloud connections** (data-source credentials).
2. Bind the Direct Lake source to an **explicit cloud connection with a fixed identity** — auth
   = **Service Principal** (reuse `PBI_CLIENT_ID`, already a Workspace Member) or a **Workspace
   Identity**. **Disable SSO** so the fixed identity is used for *queries*, not only refresh.
3. The fixed identity needs ≥ *Read* on the Lakehouse + *SELECT* on the tables (Direct Lake on SQL),
   or *Read*+*ReadAll* / a OneLake security role (Direct Lake on OneLake). The SP already has this as
   a Workspace Member. **Do not** grant the embedded customers any Lakehouse permission — they get
   only the token; the fixed identity reads, and our `CustomerRLS` (CUSTOMDATA) filters their rows.
4. **Re-run the Step B smoke test.** Expect `STATUS 200`. Because the RLS lives in the *semantic
   model* (not the SQL endpoint), the query stays **in-memory** — no DirectQuery fallback, full speed.

If Fix A returns 200 → proceed to §3 wiring. If it still fails, use a fallback below.

### Fallbacks (only if Fix A does not land)

**B1 — Single-customer pilot now; defer multi-tenant embed.**
Pilot #1 = one org. The client-side filter is acceptable because there is **no second tenant** to
leak to (the only live deep data that matters is theirs + sample). The pyodbc pages are already
server-isolated, so only the embedded report is soft — and with one customer that is moot. Mark
"server-side embed RLS" as a **hard gate before customer #2.** Fastest path to a running pilot;
honest about the boundary.

**B2 — Switch the embedded model (or a copy) to Import/Composite.**
DirectLake's RLS quirks vanish on an Import model; RLS-on-Import is rock-solid. Cost: lose
DirectLake's no-refresh freshness for that model → add a scheduled refresh. Option: keep DirectLake
for internal/demo, an Import copy for multi-tenant embed. Heavier model management; the proper fix
if you need multi-tenant embed **before** customer #2.

**B3 — Per-customer report/dataset (deploy-to-tenant-lite).**
Each customer gets their own thin report/dataset → real isolation by construction, no model RLS
dependency. Heavy ops (N datasets to refresh/version); reserve for a few high-value enterprise
deals (this is the capacity doc's option ③).

**Not an option — "harden the client-side filter."** The token stays unrestricted, so it remains
bypassable. Lipstick, not a boundary.

---

### Done-definition
Smoke test run; result recorded here. If **GO**, the embedded report is server-side isolated via
one `CustomerRLS` role + the backend wiring in §3.1, and CP-2 Phase 5 can pass for real with two
customers. If **NO-GO**, B1 ships pilot #1 single-customer with the multi-tenant gate documented.
