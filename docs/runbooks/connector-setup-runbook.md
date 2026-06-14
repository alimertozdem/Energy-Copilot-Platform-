# EnergyLens — MCP Connector Setup Runbook

_For: Mert (founder). Purpose: connect Claude to your stack so the **founder-run execution gap**
(Fabric / GitHub / Stripe / DB) shrinks. Each connector is a one-time setup you do; I guide and then
use it. Date: 2026-06-14._

---

## 0. How custom connectors work (read this first)

- In the Claude desktop app: **Settings → Connectors → Add custom connector** (or **Customize →
  Connectors → "+"**). Enter a **name** + the **remote MCP URL**, optionally open **Advanced
  settings** for an **OAuth Client ID / Secret**, then **Add**.
- **Custom connectors run from Anthropic's cloud, not your laptop.** So the MCP server must be
  reachable over the public internet. Every endpoint below is a public remote endpoint → fine. Two
  *local-only* options are flagged; those can't run as cloud connectors.
- **Secrets** (GitHub token, Stripe key, DB string) are entered **directly in the connector dialog** —
  never paste them into chat. I don't need to see them.
- Order below is by **impact on your bottleneck**. Do 1–2 first; 3–5 when you reach them.

---

## 1. Microsoft Fabric (Core MCP) — **highest value, do first**

**Unlocks for me:** list your workspaces & items, see which lakehouse tables / semantic models /
notebooks exist, create & update items, manage workspace permissions.
**Honest limit:** I still **cannot run notebooks or change table data** through this — that stays
with you. But it kills half the "what's in there / what's missing" back-and-forth.

- **URL:** `https://api.fabric.microsoft.com/v1/mcp/core`
- **Auth:** OAuth via Microsoft Entra ID (browser sign-in with your Fabric account).
- **Steps:** Settings → Connectors → Add custom connector → Name `Fabric` → paste URL → Add →
  complete the Entra sign-in → approve.
- **Verify:** ask me *"list my Fabric workspaces"*.

> **Advanced / optional (local, later):** the **Fabric Pro-Dev** server (`npm install -g
> fabric-pro-dev-mcp-server`) can *deploy a semantic model* — i.e. automate your painful Tabular
> Editor step. It runs as a **local subprocess**, so it is **not** usable via the cloud connector
> flow; we'd wire it through local MCP config only if/when we automate that deploy. Skip for now.

## 2. GitHub (official MCP) — **do second**

**Unlocks for me:** read code, open pull requests & issues, manage releases and CI directly in your
repo. Bonus: a clean PR/commit history is real credibility for EXIST / investors / pilots.

- **URL:** `https://api.githubcopilot.com/mcp/`
- **Auth:** a GitHub **fine-grained Personal Access Token** (Bearer), or OAuth if offered.
- **Security:** create the token **scoped to the `Energy-copilot-platform` repo only**.
- **Steps:** GitHub → Settings → Developer settings → fine-grained PAT (repo-scoped) → copy →
  Claude → Add custom connector → Name `GitHub` → URL above → Advanced → paste token → Add.
- **Verify:** ask me *"list open issues / the last 5 commits"*.

## 3. Stripe (MCP) — **for billing go-live (your P2/P3)**

**Unlocks for me:** create products & prices, inspect subscriptions, help wire the tiers you already
designed (Free / Basic €99 / Monitor €299 / Enterprise / Residential €49+€3).

- **URL:** `https://mcp.stripe.com`
- **Auth:** OAuth, or a **restricted API key**. **Start in TEST mode** with a restricted key.
- **Steps:** Add custom connector → Name `Stripe` → URL above → authenticate (test mode) → Add.
- **Verify:** ask me *"list my Stripe products"* (expect empty in a fresh test account).
- Follow `web-app/BILLING_SETUP.md` for the authoritative amounts once connected.

## 4. Database (Supabase MCP) — **verify migrations**

**Unlocks for me:** inspect schema & data, and **confirm `alembic upgrade head` actually applied**
all your pending migrations (bridge_requests, pilot_requests, alert_status, billing, etc.).

- Your prod DB is **Supabase** → use **Supabase's official remote MCP**: URL `https://mcp.supabase.com/mcp?read_only=true` (OAuth browser sign-in), not a local Postgres MCP.
- **Auth:** Supabase access token + project ref (entered in the connector dialog).
- **Security:** keep it read-mostly; never paste the connection string into chat.
- **Verify:** ask me *"which alembic migrations are applied vs heads?"*

> If you ever move to a **self-hosted Postgres**, a local Postgres MCP would need the local-MCP route
> (cloud connectors can't reach a private DB).

## 5. Higgsfield (MCP) — **for the promo video, later**

**Unlocks for me:** generate cinematic intro/outro + b-roll for the master video from our session.
Do this **when we reach the video step**, not now.

- **URL:** get it from `higgsfield.ai/mcp` (sign in → copy your MCP URL).
- **Auth:** your Higgsfield account (**paid** subscription).

---

## After you connect each one

Tell me which are live. I'll run a quick **read-only check** on each (list workspaces / list issues /
list products / check migration head) and report what I see. Then we use them to accelerate the
real go-live work (CP-1 report, CP-2 pilot bridge + RLS, billing).

## What I still can't do (honest)

- Run Fabric notebooks or modify lakehouse data — Core MCP can't; still you.
- Click through OAuth on your behalf — you approve each connection.
- Reach anything on a private/local server that isn't exposed to the public internet.

---

_Sources: Claude Help Center — custom connectors via remote MCP; GitHub official MCP server;
Stripe MCP; Microsoft Fabric Core/Pro-Dev MCP (Microsoft Learn)._
