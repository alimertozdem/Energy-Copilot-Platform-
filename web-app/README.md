# EnergyLens Web Application

The customer-facing SaaS layer of the Energy Copilot Platform — a Next.js
frontend + FastAPI backend over the Microsoft Fabric Lakehouse. It turns the
Fabric analytics (9 Power BI report pages + gold KPI/anomaly/recommendation
tables) into a multi-tenant product.

## Structure

```
web-app/
├── frontend/   # Next.js (App Router), Tailwind, NextAuth, Power BI Embedded
└── backend/    # FastAPI, SQLAlchemy + Alembic, Fabric SQL (pyodbc), Copilot LLM
```

## Data paths (one Lakehouse, three reads)

1. **Power BI Embedded** (DirectLake semantic model) — the 9 rich report pages,
   embedded per building with route-level module gating.
2. **Direct Fabric SQL** (SQL Analytics Endpoint via pyodbc) — the app's custom
   React views: `/portfolio`, `/actions`, `/alerts`, `/solar`.
3. **PostgreSQL control plane** — operational state Fabric doesn't hold:
   organizations & members, recommendation + alert status overlays, copilot
   conversation history, and the audit log.

The custom React views join path 2 (Fabric, source of truth for analytics) with
path 3 (Postgres, customer-side operational state).

## Running locally

Two processes. Use **`http://localhost:3000`** for the frontend and
**`http://127.0.0.1:8000`** for the backend / Swagger (on Windows `localhost`
resolves to IPv6, which uvicorn does not bind by default).

### Backend — FastAPI

```
cd web-app/backend
python -m venv venv
venv\Scripts\activate          # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
alembic upgrade head           # apply database migrations
uvicorn main:app --reload --port 8000
```

Backend `.env` (gitignored) — representative keys:
`PBI_TENANT_ID`, `PBI_CLIENT_ID`, `PBI_CLIENT_SECRET`, `PBI_WORKSPACE_ID`,
`PBI_REPORT_ID`, `DATABASE_URL`, `FABRIC_SQL_SERVER`, `FABRIC_SQL_DATABASE`,
`INTERNAL_API_KEY`.

### Frontend — Next.js

```
cd web-app/frontend
npm install
npm run dev                    # http://localhost:3000
```

Frontend `.env.local` — representative keys:
`NEXTAUTH_URL`, `NEXTAUTH_SECRET`, `BACKEND_URL`, the provider client IDs/secrets
(Microsoft / Google), `INTERNAL_API_KEY`.

## Auth + Power BI embed

**App-owns-data:** the backend holds a Fabric service principal and mints Power BI
embed tokens (V2 API — DirectLake-compatible). Auth is multi-provider (Microsoft
Entra / Google / email+password) and org-centric (multi-tenant); Power BI RLS
scopes report data per customer.

## Resilience

A missing or not-yet-synced Fabric gold table surfaces as a calm "live data is
temporarily unavailable" notice (HTTP `503` with code `fabric_unavailable`),
never a hard crash — see the global `pyodbc.Error` handler in `backend/main.py`.

## Migrations

Schema changes are hand-written Alembic migrations under
`backend/alembic/versions/` (model + migration kept in lockstep). After pulling
new migrations: `alembic upgrade head`.

### Authenticated E2E tests (Playwright)

The Playwright suite has two parts:

- **Public suite** (default) — `npm run dev`, then `npx playwright test`. Covers
  public pages, SEO endpoints, auth-guard redirects and the 404. No login.
- **Authenticated suite** (opt-in) — registers only when credentials are set,
  and needs the dev server **and** the FastAPI backend up plus a real account:

  ```bash
  E2E_EMAIL=e2e@energylens.eu E2E_PASSWORD=yourpassword npx playwright test
  ```

  `e2e/auth.setup.ts` logs in once and saves the session to
  `e2e/.auth/user.json` (git-ignored); `e2e/authed.spec.ts` reuses it to assert
  the protected routes (/portfolio, /actions, /alerts, /settings, /copilot)
  render under a session instead of bouncing to the public landing. Create the
  account once via `/signup`.
