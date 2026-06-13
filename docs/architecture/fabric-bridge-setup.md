# EnergyLens — Automated Fabric Bridging: Setup Guide (Phase 3.2)

_Status: **SETUP GUIDE** — written 2026-06-06. Companion to
[`self-serve-fabric-bridging.md`](./self-serve-fabric-bridging.md) §5 (Phase 3.2)._

This guide lists everything that must be provisioned in **Azure** and **Microsoft
Fabric** before the automated bridge (`FabricBridgeOrchestrator`) can run live. The
backend code is written to be **capacity-independent**: it ships behind a feature flag
(`BRIDGE_AUTOMATION_ENABLED`), and the manual Phase-3.1 path keeps working until the
flag is turned on.

> **Hard prerequisite, read first.** Automated bridging triggers a **Fabric job**
> (the parameterised medallion notebook). A Fabric job needs an **active F-capacity**
> (or a Trial capacity) assigned to the workspace. As of 2026-06-06 EnergyLens has **no
> running paid capacity** and the original trial has expired. Everything below can be
> *prepared* at €0, but the live run in §6 only succeeds once a capacity is attached.
> Steps that are blocked by capacity are marked **⛔ needs capacity**.

---

## 0. What we already have (reuse — do not recreate)

From the existing Power BI / Fabric SQL integration (`integrations/fabric_sql.py`,
`integrations/pbi_embed.py`) these are already in `web-app/backend/.env`:

| Existing var | Meaning | Reused for 3.2? |
|---|---|---|
| `PBI_TENANT_ID` | Azure AD tenant GUID | ✅ same SP |
| `PBI_CLIENT_ID` | Service principal (app) client GUID | ✅ same SP |
| `PBI_CLIENT_SECRET` | SP secret | ✅ same SP |
| `PBI_WORKSPACE_ID` | Fabric/Power BI workspace GUID | ✅ reused as workspace target |
| `PBI_REPORT_ID` | Embedded report GUID | — (embed only) |
| `FABRIC_SQL_SERVER` | Lakehouse SQL Analytics Endpoint host | — (read path only) |
| `FABRIC_SQL_DATABASE` | Lakehouse name | reference only |

**Key fact:** the existing SP authenticates to the **SQL Analytics Endpoint**, which is
**read-only** in Fabric. Automated bridging needs to *write* (land bronze) and *trigger*
(run a notebook job). Those go through **OneLake** + the **Fabric REST API**, not the SQL
endpoint — which is why the SP needs the extra roles in §2–§3 and why bronze landing uses
OneLake (§4), not `INSERT`.

---

## 1. Decide the automation boundary (already chosen)

- **Armed one-click** (chosen 2026-06-06): the backend performs all five bridge steps,
  but a human (founder) presses **Go live** in `/admin`. The energy-logic QA gate stays.
- This means the orchestrator is invoked by an **admin endpoint**, not by the customer
  wizard directly. The customer still files a Phase-3.1 request; the founder fulfils it
  with the automated path instead of running notebooks by hand.

No change needed here — it just explains why the trigger lives behind the admin gate.

---

## 2. Azure AD app (service principal) — extra permissions

We reuse the **existing** app (`PBI_CLIENT_ID`); we only **add** permissions. (If you
prefer an isolated app, create a new one and set the `FABRIC_BRIDGE_*` creds in §5
instead of reusing `PBI_*`.)

1. **Azure Portal → Microsoft Entra ID → App registrations →** select the EnergyLens app.
2. Confirm a **client secret** exists and is not near expiry (Certificates & secrets). If
   you rotate it, update `PBI_CLIENT_SECRET`.
3. **API permissions** — the Fabric REST API is governed by the **workspace role** (§3),
   not Graph scopes, so usually no delegated/application Graph permission is required for
   item-job execution. Leave existing Power BI permissions as-is.
4. Note the **tenant setting**: in the **Fabric Admin portal → Tenant settings**, the
   switch **“Service principals can use Fabric APIs”** (and **“…can call Power BI APIs”**)
   must be **On**, scoped to a security group your SP belongs to. This is the single most
   common reason automated calls 401 even when roles look correct.

---

## 3. Fabric workspace — grant the SP write + execute

The SP currently has at least **Member** (enough for SQL read). For automated bridging it
needs to **run items** and **write to OneLake**.

1. **Fabric → your workspace → Manage access.**
2. Add the service principal (search by the app name / client ID) with role
   **Contributor** (can run notebooks/jobs) or **Member**. **Admin** is not required.
   - *Contributor* lets the SP execute item jobs and write to the Lakehouse's OneLake.
3. Capture the workspace GUID (same as `PBI_WORKSPACE_ID`; confirm it's the workspace that
   holds the **gold Lakehouse** and the bridge notebook).

---

## 4. Lakehouse + bronge landing zone (OneLake)

Bronze landing mechanism (chosen): **backend writes a parquet file to OneLake Files; the
parameterised notebook reads it.** No Fabric→Postgres networking required.

1. Identify the **gold Lakehouse** (the one behind `FABRIC_SQL_DATABASE`). In Fabric, open
   it and copy its **item ID** (GUID) from the URL or **⋯ → Copy SQL endpoint / details**.
   This is `FABRIC_LAKEHOUSE_ID`.
2. The OneLake path the backend writes to (ABFS / DFS endpoint):

   ```
   https://onelake.dfs.fabric.microsoft.com/{workspaceId}/{lakehouseId}/Files/bridge_inbox/{building_uuid}/consumption.csv
   ```

   (CSV, not parquet — the backend writer is stdlib-only, no pyarrow dependency.)
   The SP authenticates with an **OneLake/Storage token** (`https://storage.azure.com/.default`
   scope) using the same client-credentials flow. Contributor role (§3) covers the write.
3. Create the `Files/bridge_inbox/` folder once (the backend will create per-building
   subfolders automatically). Optional but tidy.

---

## 5. The parameterised bridge notebook

The notebook lives at `notebooks/bridge/40_bridge_baseline.py` (built in this phase).
After importing it into Fabric:

1. **Import** the `.py` as a Fabric notebook in the same workspace, attached to the gold
   Lakehouse as its default Lakehouse.
2. Confirm it exposes a **parameters cell** (tagged *Parameters*) with:
   `building_uuid`, `fabric_building_id`, `building_meta` (JSON), `bronze_path`.
3. Copy the notebook's **item ID** (GUID) → `FABRIC_BRIDGE_NOTEBOOK_ID`.
4. The notebook is **idempotent** (MERGE on `building_id` + date), so a re-run for the same
   building overwrites rather than duplicates — safe to retry.

### 5b. Report notebooks (full report set — Phase 2, 2026-06-13)

To populate GHG / GEG / recommendations for a bridged building, import these three batch
notebooks too. Each has an **optional** `BRIDGE_BUILDING_ID` parameter cell — empty = full
batch (unchanged); set to a `fabric_building_id` = single-building incremental run.

1. Import `notebooks/gold/09_ghg_scope_engine.py`, `notebooks/compliance/05_compliance_checker.py`,
   `notebooks/recommendation/06_recommendation_engine.py` into the same workspace, attached to
   the gold Lakehouse.
2. In each, mark the **`BRIDGE_BUILDING_ID`** cell (top of the notebook) as the *Parameters* cell.
3. Copy each notebook's **item ID** → `FABRIC_GHG_NOTEBOOK_ID` / `FABRIC_COMPLIANCE_NOTEBOOK_ID`
   / `FABRIC_RECOMMENDATION_NOTEBOOK_ID` (§7). **All optional** — any left unset is simply
   skipped, and the bridge still goes live with the baseline.
4. Scoped runs are safe to re-run: 09/05 MERGE on the key, 06 deletes-then-appends the
   building's rows. Other buildings are never touched.

---

## 6. ⛔ needs capacity — attach a capacity & run

This is the only step that costs money / needs the trial.

1. **Fabric Admin portal → Capacities** (or Azure → *Microsoft Fabric Capacity*). Attach an
   **F-SKU** (e.g. F2 is the smallest) **or** an active **Trial** capacity to the workspace.
2. (Optional, cost control) If you later want the backend to **resume/pause** the capacity
   around each job, you'll also need, on the Azure **Fabric Capacity** resource:
   - the **subscription ID**, **resource group**, **capacity resource name**, and
   - the SP granted **Contributor** on that resource (Azure RBAC) so it can call
     `…/suspend` and `…/resume` via the Azure Management REST API.
   - These map to `FABRIC_CAPACITY_*` vars (deferred — not needed for the first live run).
3. With capacity attached, set `BRIDGE_AUTOMATION_ENABLED=true` and run the orchestrator
   **dry-run → live** (see §8).

---

## 7. Environment variables to add

Append to `web-app/backend/.env` (values from §3–§6). The SP creds are reused from `PBI_*`.

```bash
# --- Phase 3.2 automated Fabric bridging ---
BRIDGE_AUTOMATION_ENABLED=false          # master switch; keep false until capacity is live
FABRIC_WORKSPACE_ID=                      # usually = PBI_WORKSPACE_ID (workspace GUID)
FABRIC_LAKEHOUSE_ID=                      # gold Lakehouse item GUID (§4.1)
FABRIC_BRIDGE_NOTEBOOK_ID=                # baseline bridge notebook (40_bridge_baseline) GUID (§5.3)
# --- report chain (Phase 2); each runs scoped to the bridged building.
#     Any left UNSET is skipped — the baseline still bridges. ---
FABRIC_GHG_NOTEBOOK_ID=                   # 09_ghg_scope_engine item GUID (§5b)
FABRIC_COMPLIANCE_NOTEBOOK_ID=            # 05_compliance_checker item GUID (§5b)
FABRIC_RECOMMENDATION_NOTEBOOK_ID=        # 06_recommendation_engine item GUID (§5b)
FABRIC_ONELAKE_HOST=onelake.dfs.fabric.microsoft.com   # default; rarely changes

# --- optional, deferred: capacity resume/pause (§6.2) ---
# FABRIC_CAPACITY_SUBSCRIPTION_ID=
# FABRIC_CAPACITY_RESOURCE_GROUP=
# FABRIC_CAPACITY_NAME=
```

> If you chose an **isolated SP** instead of reusing `PBI_*`, also add
> `FABRIC_BRIDGE_TENANT_ID` / `FABRIC_BRIDGE_CLIENT_ID` / `FABRIC_BRIDGE_CLIENT_SECRET`
> and the code will prefer those over `PBI_*`.

After editing `.env`: restart uvicorn (no migration needed for env changes).

---

## 8. Verification ladder (do these in order)

1. **Flag off (today, €0).** With `BRIDGE_AUTOMATION_ENABLED=false`, the `/admin` bridge
   queue still shows the manual Phase-3.1 “Fulfil & go live” action. Nothing changes for
   customers. ✅ This is the safe default we ship in.
2. **Dry-run (no capacity).** `BRIDGE_AUTOMATION_ENABLED=true` + orchestrator `dry_run=true`
   exercises step sequencing, parameter assembly, and audit logging **without** calling
   Fabric — proves the wiring without spending capacity.
3. **Live (⛔ needs capacity).** With a capacity attached, run a real bridge on **one test
   building** first. Watch `/admin` for the per-step audit trail and the building flipping
   pending → live.

---

## 9. Summary checklist

- [ ] Tenant setting: *Service principals can use Fabric APIs* = On (§2.4)
- [ ] SP has **Contributor** on the workspace (§3)
- [ ] `FABRIC_LAKEHOUSE_ID` captured (§4.1)
- [ ] `Files/bridge_inbox/` reachable by the SP (§4)
- [ ] Bridge notebook imported, parameters cell present, `FABRIC_BRIDGE_NOTEBOOK_ID` captured (§5)
- [ ] (Optional) Report notebooks 09/05/06 imported, `BRIDGE_BUILDING_ID` cell marked, ids captured (§5b) — baseline works without them
- [ ] ⛔ Active F-capacity (or Trial) attached to the workspace (§6)
- [ ] `.env` vars added, uvicorn restarted (§7)
- [ ] Dry-run passes (§8.2) before first live bridge (§8.3)
