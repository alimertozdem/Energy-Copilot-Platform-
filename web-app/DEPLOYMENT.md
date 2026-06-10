# EnergyLens — Going Live (Vercel + Railway + Supabase)

Goal: a public URL where Boris can open the real app, log in (incl. Google),
and see live dashboards.

## Architecture

```
Browser ──► Vercel (Next.js frontend, NextAuth)
                  │  server-side proxy (Bearer JWT), never exposes token to browser
                  ▼
            Railway (FastAPI backend, Docker + ODBC Driver 18)
              ├─► Supabase Postgres   (auth, orgs, buildings, billing …)
              ├─► Fabric SQL endpoint (live KPIs via pyodbc, service principal)
              └─► Power BI REST        (embed tokens, F4 capacity)
```

Nothing new to host for the DB — it already lives on **Supabase**.

---

## STEP 0 — Commit & push the deploy changes

A stale lock may exist from tooling. In the repo root:

```bash
# Windows PowerShell / cmd:
del .git\index.lock          # ignore "not found" — only if it exists

git add web-app/backend/Dockerfile web-app/backend/start.sh web-app/backend/.dockerignore \
        web-app/backend/railway.json web-app/backend/requirements.txt \
        web-app/backend/main.py web-app/backend/app/db/database.py \
        web-app/backend/.env.example web-app/frontend/.env.example \
        web-app/DEPLOYMENT.md .gitignore .gitattributes
git commit -m "chore: deploy config (Docker/Railway, env examples, encoding fixes)"
git push
```

> The frontend `.tsx` files showing as "modified" are line-ending-only noise — safe to leave or `git add` too.

---

## STEP 1 — Backend on Railway

1. Railway → **New Project → Deploy from GitHub repo** → pick this repo.
2. Service **Settings → Root Directory** = `web-app/backend`
   (Railway then auto-uses the `Dockerfile` + `railway.json` there.)
3. **Variables** tab — paste these (values come from your local `web-app/backend/.env`):

   | Variable | Notes |
   |---|---|
   | `DATABASE_URL` | Supabase **Session Pooler** URL (IPv4) |
   | `JWT_SECRET` | same as local |
   | `INTERNAL_API_KEY` | same as local — must match the frontend |
   | `PBI_TENANT_ID` `PBI_CLIENT_ID` `PBI_CLIENT_SECRET` `PBI_WORKSPACE_ID` `PBI_REPORT_ID` | all 5 required |
   | `FABRIC_SQL_SERVER` `FABRIC_SQL_DATABASE` | Fabric SQL endpoint |
   | `LLM_PROVIDER` | `mock` |
   | `CORS_ORIGINS` | set later (Step 3) to the Vercel URL — for now `*` is fine to start |
   | `FRONTEND_URL` | set later to the Vercel URL |

   Optional: `FABRIC_SQL_CACHE_TTL=45`, Stripe keys (leave out → billing simply disabled).
   **Do NOT set `PORT`** — Railway injects it.
4. Deploy. First build takes a few minutes (it installs the Microsoft ODBC driver).
5. Settings → **Networking → Generate Domain**. Copy it, e.g. `https://energylens-backend.up.railway.app`.
6. Test: open `https://<backend>/health` → should return `{"status":"ok"}` (or 200).

---

## STEP 2 — Frontend on Vercel

1. Vercel → **Add New → Project** → import this GitHub repo.
2. **Root Directory** = `web-app/frontend` (Framework auto-detects **Next.js**).
3. **Environment Variables** (from your local `web-app/frontend/.env.local`):

   | Variable | Value |
   |---|---|
   | `NEXTAUTH_URL` | your Vercel URL, e.g. `https://energylens.vercel.app` |
   | `NEXTAUTH_SECRET` | `openssl rand -base64 32` (or reuse local) |
   | `BACKEND_URL` | the Railway URL from Step 1.5 |
   | `INTERNAL_API_KEY` | **same value** as the backend |
   | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | from Google Cloud |
   | `AZURE_AD_CLIENT_ID` / `AZURE_AD_CLIENT_SECRET` / `AZURE_AD_TENANT_ID` | from Azure |
   | `NEXT_PUBLIC_SITE_URL` | your Vercel URL |

4. Deploy. Copy the production URL (e.g. `https://energylens.vercel.app`).

---

## STEP 3 — Connect the two

1. Back in **Railway → Variables**: set
   `CORS_ORIGINS = https://energylens.vercel.app` and
   `FRONTEND_URL = https://energylens.vercel.app` → redeploy.
2. In **Vercel**: confirm `NEXTAUTH_URL` and `NEXT_PUBLIC_SITE_URL` equal the final domain
   (if you add a custom domain later, update both + the OAuth URIs below + redeploy).

---

## STEP 4 — OAuth redirect URIs (so login works on the live domain)

**Google Cloud Console → APIs & Services → Credentials → your OAuth client:**
- Authorized JavaScript origins: `https://energylens.vercel.app`
- Authorized redirect URIs: `https://energylens.vercel.app/api/auth/callback/google`

**Azure Portal → App registrations → your app → Authentication → Web → Redirect URIs:**
- `https://energylens.vercel.app/api/auth/callback/azure-ad`

(Keep the existing `http://localhost:3000/...` entries for local dev.)

---

## STEP 5 — Power BI & Supabase sanity

- **Power BI:** F4 capacity is ON. The service principal (`PBI_CLIENT_ID`) must be a
  **Member** of the workspace, and the tenant setting *"Service principals can use
  Power BI APIs"* must be enabled. (These already work locally → just confirm.)
- **Supabase:** use the **Session Pooler** connection string (IPv4) — Railway egress is
  IPv4, the direct 5432 host is IPv6-only and will hang.
- **Migrations:** `start.sh` runs `alembic upgrade head` on boot (best-effort). Supabase
  is already at head, so this is a no-op.

---

## STEP 6 — Verify (open the live site)

- [ ] `https://<backend>/health` → 200
- [ ] Frontend landing page loads
- [ ] `/demo` (no login) shows sample buildings + an embedded dashboard
- [ ] Sign in with Google works end-to-end (no redirect-URI error)
- [ ] A building report embeds the Power BI dashboard (capacity on)
- [ ] `/portfolio`, `/actions`, `/solar`, `/alerts` load data (Fabric SQL via ODBC)

### Note on what Boris will see
A **fresh** Google login creates a new, empty org → he lands on onboarding with no data.
To show him the real portfolio, either:
- point him to **`/demo`** (public, no login — best for a first look), or
- pre-invite his email into your org (Settings → Members → Invite) so his Google login
  lands directly in the populated workspace.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Backend build fails on `pip install` | requirements.txt encoding — already fixed (UTF-8). |
| Backend 500 on data pages, logs show ODBC error | ODBC driver missing → the Dockerfile installs `msodbcsql18`; ensure Railway used the Dockerfile (Root Dir = web-app/backend). |
| `Missing .env values: PBI_...` at startup | one of the 5 `PBI_*` vars not set in Railway. |
| `DATABASE_URL is not set` | set it in Railway; use the Supabase pooler URL. |
| Login: `redirect_uri_mismatch` | the callback URL in Google/Azure doesn't exactly match `https://<frontend>/api/auth/callback/<provider>`. |
| Login spins / 401 | `INTERNAL_API_KEY` differs between Vercel and Railway, or `BACKEND_URL` wrong. |
| CORS error in browser console | set `CORS_ORIGINS` in Railway to the exact Vercel URL, redeploy. |
| Dashboard area blank / token error | service principal lacks workspace access, or capacity paused. |
| DB calls hang then fail | using Supabase direct (IPv6) instead of the Session Pooler (IPv4). |
