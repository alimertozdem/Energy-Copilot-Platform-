# EnergyLens — Going Live (Vercel + Azure Container Apps + Supabase)

Goal: a public URL where anyone can open the real app, log in (incl. Google),
and see live dashboards.

> **Backend hosting (updated 2026-06-14):** the backend runs on **Azure Container
> Apps**, deployed from **source** (not git). An earlier version of this file
> described **Railway** — that path was abandoned (the Railway project is empty).
> Don't look there. See "Backend on Azure Container Apps" below.

## Architecture

```
Browser ──► Vercel (Next.js frontend, NextAuth)            [git push auto-deploys]
                  │  server-side proxy (Bearer JWT), never exposes token to browser
                  ▼
            Azure Container Apps (FastAPI, Docker + ODBC 18)  [GitHub Actions auto-deploys]
              ├─► Supabase Postgres   (auth, orgs, buildings, billing …)
              ├─► Fabric SQL endpoint (KPIs via pyodbc, service principal)  *see caveat
              └─► Power BI REST        (embed tokens, F4 capacity)
```
\* Network caveat (below): Container Apps Consumption can't reach Fabric SQL, so the
KPI pages are served from a captured snapshot fallback. Embeds still work (REST/443).

The DB already lives on **Supabase** — nothing new to host there.

---

## Backend on Azure Container Apps

**Resources** (subscription = your Azure account; `az account show --query id -o tsv`):

| Thing | Value |
|---|---|
| Resource group | `rg-energylens` |
| Container Apps environment | `energylens-env` |
| Container app | `energylens-api` |
| Container registry (ACR) | `cab42c1b7ac5acr` (admin enabled) |
| Region | `germanywestcentral` |
| Public URL | `https://energylens-api.jollyglacier-ee2b4614.germanywestcentral.azurecontainerapps.io` |
| Min replicas | 1 (always-on, no cold start) |

**Environment variables** — set on the container app; **preserved across deploys**
(an image update does not reset them):
`DATABASE_URL` (Supabase Session Pooler, IPv4), `JWT_SECRET`, `INTERNAL_API_KEY`
(must match the frontend), `PBI_TENANT_ID` `PBI_CLIENT_ID` `PBI_CLIENT_SECRET`
`PBI_WORKSPACE_ID` `PBI_REPORT_ID`, `FABRIC_SQL_SERVER` `FABRIC_SQL_DATABASE`,
`LLM_PROVIDER=mock`, `CORS_ORIGINS` (the Vercel URL), `FRONTEND_URL` (the Vercel
URL), `FABRIC_SQL_LOGIN_TIMEOUT=6`. **Do NOT set `PORT`** — the platform injects it.

### Deploy — automatic (preferred)

A push to `main` that touches `web-app/backend/**` triggers
`.github/workflows/deploy-backend.yml`: it runs the backend unit tests, then builds
the image and updates `energylens-api` **in place**. One-time secret setup below.

### Deploy — manual (first deploy / fallback)

```bash
cd web-app/backend
az containerapp up \
  --name energylens-api \
  --resource-group rg-energylens \
  --environment energylens-env \
  --source .
```

This packages the **local** files (not git), cloud-builds the Dockerfile in ACR, and
rolls a new revision. First build takes a few minutes (installs `msodbcsql18`).

> ⚠️ Because deploy reads **local source**, a plain `git push` does NOT update the
> backend by itself. Use the GitHub Actions workflow, or run the command above.

Health: `https://<backend>/health` → `{"status":"healthy"}`.

### Auto-deploy (GitHub Actions) — one-time setup

The workflow needs ONE repo secret to authenticate to Azure:

1. Create a service principal scoped to the resource group (least privilege):
   ```bash
   sub=$(az account show --query id -o tsv)
   az ad sp create-for-rbac --name energylens-gha \
     --role Contributor \
     --scopes /subscriptions/$sub/resourceGroups/rg-energylens \
     --sdk-auth
   ```
2. Copy the whole JSON output → GitHub repo → **Settings → Secrets and variables →
   Actions → New repository secret** → name **`AZURE_CREDENTIALS`**, value = the JSON.
3. Done. Backend pushes now auto-deploy; you can also trigger it from
   **Actions → deploy-backend → Run workflow** (workflow_dispatch).

### Network caveat — why KPI pages use a snapshot (Plan B)

Container Apps (Consumption) can open TCP to the Fabric SQL gateway but can't complete
the SQL **Redirect** step (backend node ports 11000–11999), so `pyodbc` times out and
live Fabric queries fail **from inside Azure** (they work from a laptop). The backend
degrades gracefully:
- `/portfolio`, `/actions`, `/alerts`, building KPIs → `app/data/sample_fallback.json`
  (a captured snapshot of the real portfolio).
- `/demo` → static `_DEMO_FALLBACK` (6 buildings).
- Power BI **embeds** are unaffected (Power BI REST over 443).

Refresh the snapshot after data/logic changes: from `web-app/backend` (with laptop
Fabric access) run `python -m scripts.capture_sample_data`, commit the updated
`app/data/sample_fallback.json`, and let the workflow redeploy.

A VNet-integrated Container Apps plan (or App Service / VM) could reach Fabric
directly, but needs a Pay-As-You-Go subscription (the free trial has 0 VM quota).

---

## Frontend on Vercel

1. Vercel → **Add New → Project** → import this GitHub repo.
2. **Root Directory** = `web-app/frontend` (Framework auto-detects **Next.js**).
3. **Environment Variables** (from your local `web-app/frontend/.env.local`):

   | Variable | Value |
   |---|---|
   | `NEXTAUTH_URL` | your Vercel URL, e.g. `https://energy-copilot-platform.vercel.app` |
   | `NEXTAUTH_SECRET` | `openssl rand -base64 32` (or reuse local) |
   | `BACKEND_URL` | the Azure Container Apps URL above |
   | `INTERNAL_API_KEY` | **same value** as the backend |
   | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | from Google Cloud |
   | `AZURE_AD_CLIENT_ID` / `AZURE_AD_CLIENT_SECRET` / `AZURE_AD_TENANT_ID` | from Azure |
   | `NEXT_PUBLIC_SITE_URL` | your Vercel URL |

4. Deploy. Vercel auto-deploys on every push to `main` (frontend changes go live on
   their own — only the **backend** needs the Azure step above).

---

## Connect the two

1. On the Azure container app, set `CORS_ORIGINS` and `FRONTEND_URL` to the exact
   Vercel URL (e.g. `https://energy-copilot-platform.vercel.app`), then redeploy.
2. In **Vercel**: confirm `NEXTAUTH_URL` and `NEXT_PUBLIC_SITE_URL` equal the final
   domain (custom domain later → update both + the OAuth URIs below + redeploy).

---

## OAuth redirect URIs (so login works on the live domain)

**Google Cloud Console → APIs & Services → Credentials → your OAuth client:**
- Authorized JavaScript origins: `https://energy-copilot-platform.vercel.app`
- Authorized redirect URIs: `https://energy-copilot-platform.vercel.app/api/auth/callback/google`

**Azure Portal → App registrations → your app → Authentication → Web → Redirect URIs:**
- `https://energy-copilot-platform.vercel.app/api/auth/callback/azure-ad`

(Keep the existing `http://localhost:3000/...` entries for local dev.)

---

## Power BI & Supabase sanity

- **Power BI:** F4 capacity ON. The service principal (`PBI_CLIENT_ID`) must be a
  **Member** of the workspace, and the tenant setting *"Service principals can use
  Power BI APIs"* must be enabled.
- **Supabase:** use the **Session Pooler** connection string (IPv4) — Azure egress is
  IPv4; the direct 5432 host is IPv6-only and will hang.
- **Migrations:** the backend runs `alembic upgrade head` on boot (best-effort).
  Supabase is already at head, so this is a no-op.

---

## Verify (open the live site)

- [ ] `https://<backend>/health` → `{"status":"healthy"}`
- [ ] Frontend landing page loads
- [ ] `/demo` (no login) shows sample buildings + an embedded dashboard
- [ ] Sign in with Google works end-to-end (no redirect-URI error)
- [ ] A building report embeds the Power BI dashboard (capacity on)
- [ ] `/portfolio`, `/actions`, `/alerts` load data (snapshot fallback — see caveat)

### Note on what a new visitor sees
A **fresh** Google login creates a new, empty org → onboarding with no data. To show
the real portfolio, either point them to **`/demo`** (public, no login), or pre-invite
their email into your org (Settings → Members → Invite).

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Backend changes not live after `git push` | Expected — backend deploys from **source**, not git. Run the manual `az containerapp up` or use the deploy-backend workflow. |
| GitHub Actions deploy fails at "Azure login" | `AZURE_CREDENTIALS` secret missing/invalid → recreate the SP JSON (see Auto-deploy setup). |
| GitHub Actions deploy fails at build | Dockerfile / `requirements.txt` issue → open the failing step's log; the same `az acr build` runs locally via `az containerapp up`. |
| Backend build fails on `pip install` | requirements.txt encoding (must be UTF-8). |
| Backend 500 on data pages, logs show ODBC error | ODBC driver missing → the Dockerfile installs `msodbcsql18`; ensure Root Dir = `web-app/backend`. |
| KPI pages show snapshot, not live Fabric | Expected on Azure (network caveat). Live Fabric works from a laptop only. |
| `Missing .env values: PBI_...` at startup | one of the 5 `PBI_*` vars not set on the container app. |
| `DATABASE_URL is not set` | set it on the container app; use the Supabase pooler URL. |
| Login: `redirect_uri_mismatch` | callback URL in Google/Azure must exactly match `https://<frontend>/api/auth/callback/<provider>`. |
| Login spins / 401 | `INTERNAL_API_KEY` differs between Vercel and the backend, or `BACKEND_URL` wrong. |
| CORS error in browser console | set `CORS_ORIGINS` on the container app to the exact Vercel URL, redeploy. |
| Dashboard area blank / token error | service principal lacks workspace access, or capacity paused. |
| DB calls hang then fail | using Supabase direct (IPv6) instead of the Session Pooler (IPv4). |
| Embed shows stale bundle after a deploy | hard-refresh (Ctrl+Shift+R); new visitors are unaffected. |
