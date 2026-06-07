# freelance-bot

Finds CSRD/ESG + Microsoft Fabric jobs across freelance platforms, drafts
proposals in Mert's voice, and pushes the top matches to Telegram every 30
minutes. Costs €0/month to run.

> **Why this exists** — instead of manually scrolling Malt and freelance.de
> every day, jobs that match our niche show up on the phone with a ready-to-
> submit draft. Mert reviews in 60 seconds, copy-pastes to the platform.

---

## Quick start

### 1. One-time setup (~20 minutes total)

#### a. Create a Gemini API key
1. Go to https://aistudio.google.com/apikey
2. Sign in with Google, click "Create API key"
3. Copy the key (it starts with `AIza...`)
4. Save for Step 2

> Free tier: 1500 requests/day. We use ~50-100/day. Plenty of headroom.

#### b. Create a Telegram bot
1. In Telegram, search for `@BotFather` and start a chat
2. Send `/newbot`, follow prompts (pick any name, username must end with `bot`)
3. Copy the bot token BotFather gives you (looks like `123456:ABC-XYZ...`)
4. Send your new bot a `/start` message
5. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
6. Look for `"chat":{"id":<NUMBER>...}` — copy that chat ID

#### c. (Optional, recommended) Dedicated Gmail for platform alerts
1. Create a Gmail account like `mert.freelance.bot@gmail.com`
2. Enable 2-step verification
3. Create an **App Password**: https://myaccount.google.com/apppasswords
4. In your real Gmail, set up forwarding filters that send Malt/Contra/LinkedIn
   alert emails to the new account, and have Gmail apply labels
   `Malt`, `Contra`, `LinkedIn` to them (labels appear as IMAP folders)

> If you skip (c), the bot still works on RSS sources only (freelance.de).

#### d. Get the freelance.de RSS URL
1. Log into freelance.de
2. Go to your project search, set filters (English, remote, Power BI / Data)
3. Click the RSS feed icon — copy the URL
4. Paste into `config/sources.yml` → `rss_sources[0].url`

### 2. Local first run (smoke test)

```bash
cd scripts/freelance_bot
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

# Set secrets in shell
export GEMINI_API_KEY="AIza..."
export TELEGRAM_BOT_TOKEN="123456:ABC..."
export TELEGRAM_CHAT_ID="123456789"
# Optional:
export FREELANCE_GMAIL_USER="mert.freelance.bot@gmail.com"
export FREELANCE_GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# Dry run first (no Telegram push, no DB changes that affect future runs)
python -m src.main --dry-run

# If logs look sane, push to Telegram for real:
python -m src.main
```

### 3. Deploy to GitHub Actions

1. Push this folder to a **private** GitHub repo (or include in your existing
   EnergyLens repo)
2. Repo settings → Secrets and variables → Actions → add these secrets:
   - `GEMINI_API_KEY`
   - `GROQ_API_KEY` (optional, for fallback — get one at https://console.groq.com)
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `FREELANCE_GMAIL_USER` (optional)
   - `FREELANCE_GMAIL_APP_PASSWORD` (optional)
3. The workflow runs automatically every 30 minutes once the file is on `main`

> **Permissions:** the workflow commits `data/jobs.db` back to the repo so dedup
> state persists across runs. Make sure repo settings → Actions → General →
> Workflow permissions → "Read and write permissions" is enabled.

---

## How it works (architecture)

```
GitHub Actions cron (every 30 min, UTC)
  │
  ├─► RSS sources (freelance.de + optional Indeed)
  ├─► Email sources (Malt / Contra / LinkedIn via Gmail IMAP)
  │
  ▼
For each new job:
  1. Tier 1 — keyword include/exclude  (filters.yml)
  2. Tier 2 — budget threshold         (filters.yml)
  3. Tier 3 — LLM semantic score 1-10  (Gemini Flash)
        score < 7 → log & skip
        score ≥ 7 → continue
  4. Generate proposal draft           (Gemini Flash, 5-ingredient template)
  5. Generate client briefing          (Gemini Flash, ≤250 words)
  6. Push one Telegram message         (respects quiet hours & daily cap)
  7. Store everything in SQLite        (jobs.db, dedup + audit)

Mert reviews on phone (~60 sec) → manually submits on platform
```

---

## Files you will edit

| File | When to edit |
|---|---|
| `config/sources.yml` | When you add/remove a job source or update an RSS URL |
| `config/filters.yml` | When you want to tune keywords or thresholds |
| `config/personal.yml` | When your packages, prices, or proof artifacts change |
| `config/templates/*` | When the proposal voice needs tweaking |

You should NOT edit code in `src/` for normal tuning — configs cover that.

---

## Common operations

### Tune filter aggressiveness

Edit `config/filters.yml`:

- Too few matches → lower `llm_score.min_score_to_push` from 7 to 6
- Too many irrelevant matches → raise to 8, or add to `exclude_keywords`
- Budget filter blocking real jobs → lower `fixed_min_eur` from 500 to 300

### Inspect what happened

```bash
sqlite3 data/jobs.db
sqlite> SELECT job_id, llm_score, llm_reason FROM jobs ORDER BY seen_at DESC LIMIT 20;
sqlite> SELECT proposal_id, job_id, status FROM proposals ORDER BY drafted_at DESC LIMIT 20;
sqlite> SELECT * FROM runs ORDER BY started_at DESC LIMIT 5;
```

### Mark a proposal as submitted / won / lost

There's no UI yet — for now, update directly:

```bash
sqlite3 data/jobs.db
sqlite> UPDATE proposals SET status='submitted', last_status_at=datetime('now') WHERE proposal_id=42;
```

A future improvement is a Telegram command (`/submitted 42`, `/won 42`).

### Manually run a daily summary or weekly digest

```bash
python -m src.main --mode daily_summary
python -m src.main --mode weekly_digest
```

---

## Cost summary

| Component | Cost |
|---|---|
| Gemini Flash | €0 (free tier covers our usage) |
| GitHub Actions | €0 (free tier, ~720 minutes/month used) |
| Telegram bot | €0 |
| SQLite | €0 (file in repo) |
| **Total monthly cost** | **€0** |

Optional paid upgrades:
- Switch to OpenAI GPT-4o-mini if Gemini quality is insufficient (~€2-5/month)
- Hetzner CX11 VPS if GitHub Actions becomes restrictive (€4.51/month)

---

## Roadmap

- [ ] Telegram command interface (`/submitted`, `/won`, `/lost`)
- [ ] Multi-job parsing in LinkedIn aggregator emails
- [ ] A/B test proposal templates (track reply rate per template variant)
- [ ] Web dashboard (Streamlit Cloud) for portfolio metrics
- [ ] Toptal job invite integration (manual paste → bot parses)
- [ ] Auto-generate per-job Calendly slot reservation
