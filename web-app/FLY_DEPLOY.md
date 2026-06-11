# Backend → Fly.io (Frankfurt) — to reach Fabric SQL

**Why:** Railway (Google Cloud) can't open a DB connection to your Fabric SQL endpoint
(Azure/Germany) → "Login timeout". Fly.io allows all outbound and has a Frankfurt
region, so it should reach Fabric. Same Docker image we already built — no code change.

The frontend (Vercel) and DB (Supabase) stay exactly as they are. We only move the backend.

---

## STEP 0 — Prerequisites (only you can do these)

1. Create a Fly.io account: https://fly.io/app/sign-up — and **add a payment card**
   (Fly requires a card even on the free allowance; I can't enter payment info).
2. Install the CLI (Windows PowerShell):
   ```powershell
   pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```
   (or see https://fly.io/docs/flyctl/install/)
3. Log in:
   ```
   fly auth login
   ```

Tell me when these 3 are done — then we do the rest together (I give each command, you run it).

---

## STEP 1 — Create the app (no deploy yet)

In the repo, from the backend folder:
```
cd web-app/backend
fly launch --no-deploy --region fra --dockerfile Dockerfile
```
Answer the prompts:
- App name: e.g. `energylens-api` (must be globally unique — add a suffix if taken)
- Postgres? **No**   ·   Redis? **No**   ·   Deploy now? **No**

This creates a `fly.toml`. Open it and make sure the web service points at port **8000**:
```toml
[http_service]
  internal_port = 8000
  force_https = true
```

---

## STEP 2 — Set the secrets (values from your local web-app/backend/.env)

```
fly secrets set \
  DATABASE_URL="..." \
  JWT_SECRET="..." \
  INTERNAL_API_KEY="..." \
  PBI_TENANT_ID="..." \
  PBI_CLIENT_ID="..." \
  PBI_CLIENT_SECRET="..." \
  PBI_WORKSPACE_ID="..." \
  PBI_REPORT_ID="..." \
  FABRIC_SQL_SERVER="..." \
  FABRIC_SQL_DATABASE="..." \
  FABRIC_SQL_DRIVER="ODBC Driver 18 for SQL Server" \
  LLM_PROVIDER="mock" \
  CORS_ORIGINS="https://energy-copilot-platform.vercel.app" \
  FRONTEND_URL="https://energy-copilot-platform.vercel.app"
```
(On Windows PowerShell, put it on one line or use backtick `` ` `` for line breaks instead of `\`.)

> Do NOT set `PORT` — the app defaults to 8000, matching `internal_port` above.

---

## STEP 3 — Deploy & test

```
fly deploy
```
When it finishes:
```
# health (should be {"status":"healthy"})
curl https://<your-app>.fly.dev/health

# THE Fabric test — should return JSON buildings, NOT "fabric_unavailable"
curl https://<your-app>.fly.dev/demo/buildings
```

- If `/demo/buildings` returns building data → **Fly reaches Fabric — we won.**
- If it still says `fabric_unavailable` → the block isn't Railway-specific; the sure fix is Azure (we'll talk).

---

## STEP 4 — Point the frontend at Fly (I'll do this in the browser)

In Vercel → project env vars → set `BACKEND_URL = https://<your-app>.fly.dev` → redeploy.
Then the live site at energy-copilot-platform.vercel.app uses the Fly backend, and the
demo / data pages light up.

---

## Notes
- Cost: Fly's free allowance covers a small always-on machine; with `auto_stop_machines`
  it scales to zero when idle. Should be ~free for a demo.
- Region `fra` (Frankfurt) is closest to your Fabric capacity (Germany West Central).
- Railway can stay as-is (or be paused later); nothing else changes.
