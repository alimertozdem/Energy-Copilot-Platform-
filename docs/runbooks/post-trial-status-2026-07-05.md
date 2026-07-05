# EnergyLens — Post-Trial Status & Recovery (2026-07-05)

> **STATUS 2026-07-05 — BRIDGED (report is LIVE).** The original trial (EnergyOpsAdmin,
> capacity `227D13BE…`) expires ~2026-07-06. Rather than let it lapse, a fresh 60-day
> Fabric trial was started under a new tenant user (`new@energyopsdemooutlook.onmicrosoft.com`),
> that user was made a workspace Admin, and the **Energy-Copilot-Platform** workspace was
> reassigned to the new trial capacity (`Trial-20260705T211349Z…`, Capacity ID `B66C2EB1-857C-4942-8161-D1E6C7218788`).
> The embedded Power BI report is live again — verified on `energy-copilot-platform.vercel.app/demo`
> (full report renders with data). **New expiry ≈ 2026-09-03.** The "How to bring the report
> back" section applies when THIS trial ends. This is a gray-zone stopgap; the durable path is
> a paid F2 (paused) once funded.

**TL;DR (TR):** Rapor ~60 gün daha canlı (yeni-kullanıcı trial köprüsü). Hiçbir şey kayıp
değil, full yedek GitHub'da. ~2026-09-03'te karar: yeni köprü / F2 / yedekten yeniden kur.

## What's safe (nothing lost)
- **Code + docs:** repo pushed to GitHub (`origin/main`, commit `7c1c692`).
- **Full Fabric definition backup:** `fabric/_trial_backup_2026-07-05/` — all ~50 notebooks,
  full semantic model (TMDL + TMSL, 336 measures, June-final), both Report definitions
  (report.json: layout + 645 report-level measures), KQL/Eventhouse, pipelines, RLS role.
- **App runtime data:** Supabase `mv_*` (13 tables, `mv_kpi_daily` 13,242 rows). The web app
  reads pg-first, independent of Fabric.
- **Static report:** PDF export of the 10-page report (2026-07-05), taken while capacity live.

## Timeline
- **~2026-07-06:** original EnergyOpsAdmin trial capacity stops (no longer used by the workspace).
- **~2026-09-03:** the bridge trial (new user) ends. Decide before then (below).
- Attaching a paid F capacity within the retention window of any expiry revives everything in place.

## What is live at €0 right now
- **Web app** (energy-copilot-platform.vercel.app): all Supabase-backed pages.
- **Embedded Power BI report** in the app: live on the new trial capacity for ~60 days.
- **Static report PDF**: show to anyone, forever, no capacity needed.

## Why the embed needs a capacity (not a storage-mode thing)
The app embeds via **app-owns-data tokens (service principal + RLS)** — confirmed in code
(`embed token RLS`, EffectiveIdentity, "capacity unavailable" handling). This requires a
capacity regardless of DirectLake vs Import. So the report only renders in the app while a
Fabric/Premium/Embedded capacity is attached.

## How to bring the report back / keep it live (at the next expiry ~2026-09-03)
1. **Another fresh 60-day trial via a new tenant user** (repeat of what we did): create a new
   Entra user → assign Fabric (Free) → start trial → add as workspace Admin → Workspace
   settings ▸ Workspace type ▸ Edit ▸ Details capacity dropdown ▸ pick the new trial ▸ Apply.
   €0, gray-zone, Microsoft may eventually limit it.
2. **F2 pay-as-you-go, paused (durable).** Create an F2 in the `MERT` Azure subscription,
   attach to the workspace. Paused = compute €0 (storage cents only); resume for demos.
3. **Rebuild from backup** (only if items were deleted): new Lakehouse + semantic model, import
   TMDL/TMSL, deploy notebooks, re-run, redeploy `report.json`, re-add CustomerRLS. ~1-2 hours.

## Freelance note
Losing a trial does not end freelance work — client Fabric/BI work runs in the client's
capacity. Repo + full backup + report PDF are your portfolio; spin up a trial/F2 per engagement.
