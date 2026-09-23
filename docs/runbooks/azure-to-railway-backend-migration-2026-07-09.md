# Backend Migration: Azure Container Apps → Railway (2026-07-09)

> **STATUS 2026-07-09 — RESOLVED.** The EnergyLens web app went down because the
> Azure subscription that hosted the backend was accidentally deleted. The backend
> was migrated off Azure to **Railway**, the Vercel frontend was re-pointed to it,
> and the Power BI report was fixed by re-publishing. The authenticated app (login +
> embedded report) is verified working. Public URL is unchanged:
> `https://energy-copilot-platform.vercel.app`.

**TL;DR (TR):** Yanlışlıkla silinen Azure aboneliği backend'i (Azure Container Apps)
yok etti → site açılıyordu ama giriş çalışmıyordu. Backend **Railway**'e taşındı,
Vercel `BACKEND_URL` yeni adrese çevrildi, Power BI raporu yeniden yayınlanarak
düzeltildi. Girişli uygulama (login + gömülü rapor) çalışıyor. Kullanıcı adresi
değişmedi. Railway hesabı **trial** — kalıcılık için Hobby plana geçilmeli.

---

## 1. What broke (root cause)

The production **backend** (FastAPI) ran on **Azure Container Apps** in an Azure
subscription named **"Mert"** (resource group `rg-energylens`, app `energylens-api`,
region `germanywestcentral`). That subscription was accidentally deleted, which
destroyed the container app + its container registry.

- The **Vercel frontend** stayed up (it is not on Azure), so the site still loaded.
- But every request — including login — is proxied server-side to `BACKEND_URL`,
  which pointed at the now-dead Azure host. Result: **"site loads, login fails."**
- The deleted "Mert" subscription was **not recoverable** from the portal (a
  cancelled sub would show as *Disabled*; it was fully gone), so reactivation was
  not possible. → migrated off Azure instead.

**Not affected by the deletion:** frontend (Vercel), database (Supabase), code
(GitHub), Microsoft Entra service principal (lives in the tenant, not the sub),
Microsoft Fabric capacity + semantic model (tenant-level trial).

---

## 2. Architecture after migration

```
Browser ──► Vercel (Next.js frontend, NextAuth)      [git push auto-deploys]
                 │  server-side proxy (BACKEND_URL, never exposed to browser)
                 ▼
           Railway (FastAPI, Docker + ODBC 18)        [git push auto-deploys]
             ├─► Supabase Postgres     (auth, orgs, buildings, billing…)
             ├─► Fabric SQL endpoint   (KPIs via pyodbc, service principal)
             └─► Power BI REST          (embed tokens; report on Fabric capacity)
```

Only the **backend host changed** (Azure → Railway). Everything else is the same.
`web-app/DEPLOYMENT.md` still describes the old Azure path — this runbook supersedes
the backend-hosting section of that file.

---

## 3. What was changed (in order)

1. **Backend → Railway.** New Railway project, deployed from the GitHub repo, root
   directory `web-app/backend`, Dockerfile builder. Generated a public domain.
2. **Start-command fix (code).** Railway honored `railway.json`'s
   `deploy.startCommand: "./start.sh"`, but `start.sh` is committed non-executable
   (git mode `100644`) → "permission denied" on container start. Removed
   `startCommand` from `web-app/backend/railway.json` so Railway uses the robust
   `Dockerfile` `CMD` (inline `alembic upgrade` + `uvicorn`). Committed + pushed.
3. **Env vars.** All 25 backend env vars set on Railway (values pasted from local
   `web-app/backend/.env`), plus `CORS_ORIGINS` / `FRONTEND_URL` = the Vercel URL
   (these two were previously injected by the old Azure script, not in `.env`).
4. **Vercel re-point.** Updated the frontend env var `BACKEND_URL` to the Railway
   URL and redeployed production.
5. **Power BI report fix.** The app's report was rendering blank; fixed by
   re-publishing from Power BI Desktop (see §6).

---

## 4. Railway configuration (reference)

| Thing | Value |
|---|---|
| Project | `adequate-caring` — id `5cf76786-a28b-47b7-bba4-ca74d1dcfc3a` |
| Service | `Energy-Copilot-Platform-` — id `16912e37-a449-4afa-a53e-2b3c50f54d69` |
| Environment | `production` |
| Source | GitHub `alimertozdem/Energy-Copilot-Platform-`, branch `main`, auto-deploy ON |
| Root Directory | `web-app/backend` |
| Builder | Dockerfile (`web-app/backend/Dockerfile`) |
| Start command | Docker `CMD` (railway.json `startCommand` removed) |
| Public URL | `https://energy-copilot-platform-production.up.railway.app` |
| Domain target port | `8080` (app listens on `$PORT`, Railway injects it) |
| Healthcheck | `/health` → `{"status":"healthy"}` |
| Plan | **TRIAL** (limited credit) — must upgrade, see §8 |

**Env vars set on Railway (25).** Values live in `web-app/backend/.env` (do NOT
commit that file). Names, grouped:

- Power BI embed: `PBI_TENANT_ID`, `PBI_CLIENT_ID`, `PBI_CLIENT_SECRET` (secret),
  `PBI_WORKSPACE_ID`, `PBI_REPORT_ID`
- DB / auth: `DATABASE_URL` (secret), `INTERNAL_API_KEY` (secret, must match Vercel),
  `JWT_SECRET` (secret)
- Fabric SQL: `FABRIC_SQL_SERVER`, `FABRIC_SQL_DATABASE` (`EnergyCopilotLakehouse`),
  `FABRIC_SQL_DRIVER`
- Fabric/bridge: `FABRIC_WORKSPACE_ID`, `FABRIC_LAKEHOUSE_ID`,
  `FABRIC_BRIDGE_NOTEBOOK_ID`, `FABRIC_GHG_NOTEBOOK_ID`,
  `FABRIC_COMPLIANCE_NOTEBOOK_ID`, `FABRIC_ONELAKE_HOST`, `BRIDGE_AUTOMATION_ENABLED`
- App/misc: `LLM_PROVIDER=mock`, `ANTHROPIC_API_KEY` (secret),
  `STRIPE_SECRET_KEY` (secret), `DEMO_EMAILS`, `ADMIN_EMAILS`
- Added for prod: `CORS_ORIGINS` + `FRONTEND_URL` = `https://energy-copilot-platform.vercel.app`

> Do **not** set `PORT` — Railway injects it.

---

## 5. Vercel configuration (reference)

| Thing | Value |
|---|---|
| Project | `energy-copilot-platform` (team `energylens-demo`, Hobby plan) |
| Public URL | `https://energy-copilot-platform.vercel.app` (**unchanged**) |
| Changed var | `BACKEND_URL` → `https://energy-copilot-platform-production.up.railway.app` |
| Must match | `INTERNAL_API_KEY` (same value as the Railway backend) |
| Redeploy | Production redeploy done after the env change |

OAuth redirect URIs did **not** need changes (they are based on the frontend URL,
which did not change).

---

## 6. Power BI report fix

The app embeds report `PBI_REPORT_ID`. Two reports exist in workspace
`Energy-Copilot-Platform` (id `6b78345d-d672-40ed-8ac5-258b58d60af9`):

| Report | Id | State found |
|---|---|---|
| **Energy Co Pilot (yedek)** — the current/intended one | `77bbe8c3-3cd8-4710-b147-b88e009ef5eb` | Rendered **black** (stale cloud copy) |
| Energy Co Pilot — older copy | `91c53038-20fc-4fb7-b8e4-43ca9556da5f` | Renders, but old data + 2 broken visuals |

The semantic model **`EnergyCopilotModel`** is healthy (refreshed same day).
Fix: **re-published `Energy Co Pilot (yedek).pbix` from Power BI Desktop** to the
workspace → overwrote report `77bbe8c3` with the current definition → now renders
with data. `PBI_REPORT_ID` remains `77bbe8c3…`.

**Open item (cosmetic, not from this migration):** the public `/demo` page's embed
renders blank. The embed request is correct (HTTP 200, right report). Cause: the
public demo path uses the model's **`Demo` RLS role** (restricts to buildings
B001–B006 via a DAX filter — see `web-app/backend/app/integrations/pbi_embed.py`),
and that role currently matches no rows in the refreshed data. The **authenticated**
report pages use the per-user RLS path and render correctly (verified on
B003 – Hamburg Logistics Hub Gamma).

---

## 7. Git changes

| Commit | Change |
|---|---|
| `06d098c` | `railway: drop startCommand so Dockerfile CMD is used` — removed `deploy.startCommand` from `web-app/backend/railway.json` |

No other code changed. All other migration work was configuration in the Railway /
Vercel dashboards and a Power BI Desktop re-publish.

---

## 8. Action required

1. **Upgrade Railway off trial.** The account shows "days / credit left". Move the
   service to a paid plan (Hobby ≈ $5/mo) so the backend stays online; otherwise it
   stops when the trial credit runs out.
2. **Set a billing budget/alert** on whatever hosts you keep (Railway, and any future
   Azure) so an accidental spend/deletion is caught early.
3. **Never delete the Azure subscription** again while any resource depends on it. If
   you must, snapshot/export first.
4. (Optional) Fix the `/demo` embed by aligning the `Demo` RLS role / demo building
   ids (B001–B006) with the current model data.

---

## 9. How to change things later (quick reference)

- **Change which report the app embeds:** Railway → service → Variables →
  `PBI_REPORT_ID` → new report id → Deploy (backend restarts).
- **Update backend code:** push to `main` (touching `web-app/backend/**`) → Railway
  auto-deploys.
- **Update frontend:** push to `main` → Vercel auto-deploys.
- **Re-point the frontend to a different backend:** Vercel → project → Settings →
  Environment Variables → `BACKEND_URL` → redeploy.
- **Backend not starting:** check Railway → Deployments → View logs. The start command
  is the Docker `CMD`; do not re-add `startCommand` to `railway.json` unless
  `start.sh` is made executable (`git update-index --chmod=+x web-app/backend/start.sh`).
- **Health check:** `GET https://energy-copilot-platform-production.up.railway.app/health`.

---

## 10. What did NOT change

- Public app URL: `https://energy-copilot-platform.vercel.app`
- Database: Supabase (unchanged)
- Microsoft Entra **service principal** (`PBI_CLIENT_ID`) — lives in tenant
  `9351fcd8-f713-4fd5-aebe-5ecd03126a51`, unaffected by the subscription deletion
- Microsoft Fabric capacity + `EnergyCopilotModel` semantic model
- OAuth providers / redirect URIs

---

*Old (dead) Azure backend, for the record: subscription "Mert" (deleted),
`rg-energylens` / `energylens-api` / env `energylens-env` /
region `germanywestcentral`. Not recoverable.*
