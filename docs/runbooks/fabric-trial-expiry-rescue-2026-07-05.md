# Fabric Trial Expiry — Rescue Runbook (2026-07-05)

**Situation:** Trial shows "1 day left" (expires ~2026-07-06). Microsoft has ended the
repeated trial auto-extensions — this expiry is final, no renewal is coming.

**What happens at expiry (Microsoft docs):**
- Workspaces drop to shared (Pro) capacity automatically.
- Non-Power-BI Fabric items (Lakehouse, notebooks, pipelines, KQL, Eventstream) become
  **inaccessible immediately** but are retained ~**7 days** (until ~**2026-07-13**).
- Attaching the workspace to a paid **F capacity within those 7 days restores everything in full**.
- After the retention window, Fabric items are **permanently deleted**.
- Power BI items survive on shared capacity, but the DirectLake semantic model is dead
  without a Fabric capacity, so the report is effectively down anyway.

---

## 1. Already safe (no action)

| Asset | Where | Status |
|---|---|---|
| Notebook code (~60 files) | `notebooks/` in repo, audited 2026-07-03 | SAFE, except live≠repo cases below |
| Web app runtime data | Supabase: 13 `mv_*` tables (mv_kpi_daily 13,242 rows, mv_recommendations 57, mv_iot_fdd 38…) | SAFE — app runs pg-first, independent of Fabric |
| Web app itself | Vercel + Azure/Railway + Supabase | UNAFFECTED |
| Semantic model TMDL export | `semantic-model/_model_export/` | **STALE (2026-06-17)** — missing all June 18–22 report-finalization measure fixes |

## 2. At risk — exists ONLY in Fabric

1. **Semantic model, current state** — ~308 measures incl. all Page 5–10 fixes since 06-17,
   `CustomerRLS` role, fixed-identity binding. Repo copy is 3 weeks stale.
2. **Report** — 10 pages, 186 visuals, **report-level measures** (never in model exports;
   **no .pbix exists anywhere in the repo**).
3. **Live-edited notebooks that differ from repo** — known: `50_materialize` (live TABLES-dict
   version), `09_ghg_scope_engine` (live collects 6 categories). Verify 03 / 06b / 16 too.
4. Lakehouse Delta tables — regenerable from notebooks, but a snapshot saves days of re-runs.
5. KQL DB / Eventstream config (Page 8), notebook schedules, SP connection settings.

## 3. DO TODAY (before expiry) — in this order

1. **Download .pbix**: Service → open report → File → Download this file.
   Commit under `report-design/pbix/`. This captures layout + report-level measures.
2. **Run the bulk export script** (exports ALL notebooks as .ipynb, semantic model as fresh
   TMDL incl. every measure, report PBIR parts, pipelines — from every workspace):
   ```
   pip install msal requests
   python scripts\fabric_full_export.py
   ```
   Optional data snapshot (gold/silver Delta files, larger download):
   ```
   python scripts\fabric_full_export.py --data
   ```
   Sign in with the device code it prints. Commit the definition folders to git
   (not the `_onelake` data folder).
3. **Replace stale model export**: copy the exported `SemanticModel_EnergyCopilotModel`
   TMDL over `semantic-model/_model_export/` and commit.
4. **Screenshot/record**: workspace item list, notebook schedule settings, capacity settings,
   the SP/fixed-identity connection (Settings → Manage connections).
5. **Apply to Microsoft for Startups Founders Hub** (self-serve, ~$1,000 Azure credits
   instantly, no funding/VC required, solo founders eligible): portal.startups.microsoft.com.
6. Decide the bridge capacity (section 4).

## 4. Options after expiry

| Option | Cost | Notes |
|---|---|---|
| **A. Second trial in tenant** | €0 | Tenant supports up to 5 trial capacities, 1 per user. A second user in the tenant starts a trial; assign the workspace to that trial capacity → 60 more days. Requires being tenant admin. Gray-zone as a self-serve loophole — a bridge, not a plan. |
| **B. F2 pay-as-you-go, paused by default** | ~€0.36–0.40/h **only while running**; storage ~cents/GB/mo | Resume for demos/notebook runs, pause after. Realistic: €5–20/mo. Requires Azure subscription + card. **Attaching F2 within the 7-day grace fully revives everything even after expiry.** |
| **C. Founders Hub credits + B** | ~€0 | $1k credits cover option B for a very long time at this usage. |
| **D. No capacity** | €0 | Web app keeps running on Supabase; PBI report + embed dead; Fabric items permanently deleted after ~2026-07-13. Only acceptable with section 3 backups completed. |

**Recommended:** 3 (backups) today unconditionally → C application today → B as the standing
mode (paused F2 ≈ storage-only cost) → A only if a zero-cost bridge is needed before credits land.

## 5. Hard deadlines

- **~2026-07-06:** trial capacity stops. Fabric items inaccessible.
- **~2026-07-13:** retention ends. After this, only the backups above exist.

Sources: Microsoft Learn "Fabric trial capacity", "Retention and recovery in Fabric",
community-confirmed end of trial extensions (2026).
