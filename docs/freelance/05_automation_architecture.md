# Freelance Job Automation — Architecture Proposal

**For:** Ali Mert Özdemir
**Date:** 2026-05-26
**Status:** **AWAITING APPROVAL** — do not build before sign-off

> **Reading guide (tr):** Bu doküman henüz kod değil — mimari kararı. Aşağıdaki 7 karar noktasına "onay" verirsen `scripts/freelance_bot/` klasörünü kurmaya başlarım. Ücretsiz veya çok ucuz bir stack seçtim (~€0/ay), ama her kararın trade-off'u var, geçmeden önce gör.

---

## 1. Goal (the one job this tool does)

> Every 30 minutes, surface only the jobs that are a true fit for our CSRD + Fabric niche, with a ready-to-submit proposal and a 1-page client briefing — to Mert's phone via Telegram — so he can review and submit in 60 seconds without opening a laptop.

What it does NOT do:
- Auto-submit proposals on any platform (ToS violation, account ban risk on Malt/Upwork/freelance.de)
- Replace your judgment — every proposal still gets your eyeballs
- Scrape platforms aggressively (we use public RSS + email forwarding only)

---

## 2. End-to-End Flow

```
                ┌─────────────────────────────────────────────┐
                │  GitHub Actions cron — every 30 minutes     │
                └──────────────────┬──────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
[1] RSS Feeds              [2] Email Inbox             [3] (Future)
   - freelance.de RSS         - Malt project alerts       - Toptal direct
   - Indeed feeds             - Contra weekly digest        invites (manual)
   - LinkedIn job alerts        forwarded to dedicated
     (via email)                 Gmail → IMAP
                                   │
                                   ▼
                  ┌─────────────────────────────────────┐
                  │   Job Normalizer                    │
                  │   - common schema:                  │
                  │     {id, source, title, desc,       │
                  │      budget, client, url, posted}   │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │   Dedup Check (SQLite)              │
                  │   - skip if job_id already seen     │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │   Filter Engine                     │
                  │   - Tier 1: keyword include/exclude │
                  │   - Tier 2: budget threshold        │
                  │   - Tier 3: LLM semantic score 1-10 │
                  │     (Gemini Flash)                  │
                  └──────────────────┬──────────────────┘
                                     │  (score ≥ 7)
                                     ▼
                  ┌─────────────────────────────────────┐
                  │   Enrichment Phase                  │
                  │   - Web fetch client website (if    │
                  │     URL extractable)                │
                  │   - LLM → 1-page client brief       │
                  │   - LLM → proposal draft (P1-P4 +   │
                  │     5-ingredient template)          │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │   Telegram Push                     │
                  │   - One message per matched job     │
                  │   - Markdown formatted              │
                  │   - "View on platform" button       │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │   SQLite (audit log)                │
                  │   - jobs_seen                       │
                  │   - jobs_matched                    │
                  │   - proposals_generated             │
                  │   - status (drafted/submitted/won)  │
                  └─────────────────────────────────────┘

                  Mert reviews on phone (~60 sec) → manually submits on platform
```

---

## 3. Decision Points (need your approval)

### Decision 1 — LLM Provider

| Option | Cost | Quality | Risk |
|---|---|---|---|
| **Google Gemini Flash (Recommended)** | **€0** (1500 req/day free, way more than we need) | Excellent for our task (job classification, proposal drafting, summarization) | Google could change free tier (low risk) |
| Groq (Llama 3.3 70B) | €0 free tier | Very good, blazingly fast | Less polished writing than Gemini |
| OpenAI GPT-4o-mini | ~€2-5/month at our volume | Reference quality | Costs scale if volume grows |
| Local Ollama (Llama 3.1 8B) | €0 (your PC) | Acceptable for filtering, weaker for proposal writing | Requires PC always on |

**Recommendation: Gemini Flash primary + Groq backup if Gemini hits a limit.**

### Decision 2 — Hosting / Scheduling

| Option | Cost | Always-on | Setup effort |
|---|---|---|---|
| **GitHub Actions (Recommended)** | **€0** (free tier 2000 min/month, we use ~720 min/month at 30-min cadence) | Yes | Low — push code to private repo, add secrets |
| Windows Task Scheduler on your PC | €0 | Only when PC is on | Lowest setup, but PC must run |
| Railway / Render free tier | €0 free, capped | Yes but spins down | Medium setup |
| VPS (Hetzner CX11) | €4-5/month | Yes | Medium setup |

**Recommendation: GitHub Actions.** Free, always runs, your PC can be off. Code lives in private repo `freelance-automation` (or as a subfolder of EnergyLens repo if you prefer).

### Decision 3 — Push Channel

| Option | Cost | Mobile UX | Markdown? |
|---|---|---|---|
| **Telegram Bot (Recommended)** | **€0** | Excellent — push notification, fast | Yes, native |
| Discord webhook | €0 | Good | Yes |
| Email digest (Gmail) | €0 | Okay — but you scroll past emails | Yes via HTML |
| WhatsApp Business API | €0 free tier (capped) | Excellent | Limited |

**Recommendation: Telegram Bot.** Create via `@BotFather` in 2 minutes. Bot pushes to your personal account or a private channel. You can also reply with `/snooze`, `/submitted`, `/won`, `/lost` to update SQLite from your phone.

### Decision 4 — Job Sources (which feeds to monitor)

| Source | Method | Volume | Quality |
|---|---|---|---|
| **freelance.de** (Recommended) | RSS public feed | ~30-50 new/day | High — kurumsal clients |
| **Malt alerts → Gmail** (Recommended) | Email forwarding to dedicated Gmail, IMAP poll | ~10-20/day | High |
| **Contra digests → Gmail** (Recommended) | Email forwarding, IMAP poll | ~5-10/week | Medium-High |
| **LinkedIn Saved Searches → Email** | Email forwarding to Gmail, IMAP poll | ~5-10/day | Variable |
| **Indeed RSS** | RSS public feed | Many, mostly noise | Low (good for volume early) |
| Upwork RSS | RSS public feed | High volume | N/A (excluded due to past account) |
| Toptal | None — they assign jobs to you | N/A | N/A |

**Recommendation: Start with freelance.de RSS + Malt email + Contra email + LinkedIn email.** Add Indeed only if volume is too low after 2 weeks.

(tr: Tüm email kaynaklarını **özel bir Gmail hesabına** yönlendirmeni öneriyorum — örn. `mert.freelance.bot@gmail.com`. Bu hesap sadece otomasyon için. Filterlar ve labellar daha temiz olur. Manuel emaillerle karışmaz.)

### Decision 5 — Filter Thresholds (when does a job become a "match"?)

```
Tier 1 — Keyword Include (any one match required):
  Microsoft Fabric, Power BI, DAX, ESG, CSRD, ESRS, GHG, Scope 1, Scope 2, Scope 3,
  sustainability dashboard, energy dashboard, carbon accounting, EnPI, ISO 50001,
  EPC, building energy, BMS dashboard, IoT building, smart building dashboard

Tier 1 — Keyword Exclude (any one match → skip):
  Tableau only, Looker only, blockchain, crypto, NFT, web3, marketing analytics,
  SEO, ecommerce, Shopify, social media, data entry only, manual data entry,
  WordPress, Webflow, video editing, graphic design only

Tier 2 — Budget Filter:
  Fixed budget: ≥ €500
  Hourly: ≥ €30/hr (we'll bid €60 but accept search threshold at €30)
  No budget stated: pass to Tier 3

Tier 3 — LLM Semantic Score (Gemini Flash, prompt below):
  Score 1-10 on fit. Pass if ≥ 7.
```

**LLM scoring prompt (draft):**
```
You are screening freelance job postings for a specialist who builds CSRD/ESG 
reporting dashboards and energy analytics on Microsoft Fabric + Power BI.

Score this job 1-10 on fit:
- 10 = perfect match (CSRD/ESG + Fabric/PBI explicitly mentioned)
- 8-9 = strong match (energy/sustainability + BI tools)
- 6-7 = moderate (Power BI generic + tangential domain)
- 1-5 = poor match

Return JSON: {"score": int, "reasoning": "1 sentence why"}

Job posting:
{job_description}
```

**Recommendation: ≥7 score gets pushed. Tune after first week of data.**

### Decision 6 — Proposal Generation Approach

Two templates per productized package (P1/P2/P3/P4), one for hourly fallback. LLM picks template + fills variables based on job description.

**5-ingredient template structure (from positioning brief):**
```
1. Pain mirror — opening line repeats client pain in client's language
2. EnergyLens artifact — one screenshot reference or 1-line achievement
3. Specific question — proves we read the brief
4. Productized package match — "this looks like a fit for P1 / P2 / P3 / P4"
5. Domain jargon paragraph — proves CSRD/Fabric literacy in 2 sentences

Sign-off: short, direct, with Calendly link
Total length: 250-320 words
```

**Recommendation: Generate the proposal as a *draft*, not auto-submit. You see it, edit if needed, copy-paste to platform.**

### Decision 7 — Notification Volume & Anti-Spam

Even with strict filtering, we might still get 5-15 matches/day in good weeks.

**Anti-spam rules:**
- Max 10 Telegram notifications per day (rest queued, sent next morning)
- One "Daily Summary" message at 9 AM if no matches that day
- "Weekly Digest" Sunday evening with stats: jobs seen, matched, submitted, replied

**Recommendation: Approved.**

---

## 4. Tech Stack Summary

| Component | Tool | Cost |
|---|---|---|
| Language | Python 3.11 | €0 |
| RSS parser | `feedparser` | €0 |
| HTTP client | `httpx` | €0 |
| Email reader | `imap-tools` | €0 |
| LLM | `google-generativeai` (Gemini Flash) | €0 |
| Telegram push | `python-telegram-bot` | €0 |
| Web scraping (client research) | `httpx` + `beautifulsoup4` + `mcp_workspace_web_fetch` if available | €0 |
| Storage | SQLite (file in repo) | €0 |
| Hosting | GitHub Actions | €0 |
| Total | | **€0/month** |

Optional upgrades later:
- Switch Gemini to GPT-4o-mini if quality issue (~€2-5/month)
- Move SQLite to PostgreSQL on Supabase free tier if multi-device sync needed (€0)
- Add web dashboard (Streamlit Cloud free) for stats visualization (€0)

---

## 5. Folder Structure (preview)

```
scripts/freelance_bot/
├── README.md
├── pyproject.toml
├── .github/workflows/
│   └── cron.yml                  # GitHub Actions schedule
├── config/
│   ├── filters.yml               # keyword include/exclude/budget thresholds
│   ├── sources.yml               # RSS URLs + email folder mappings
│   ├── templates/                # proposal templates (P1.md, P2.md, ...)
│   └── personal.yml              # your portfolio facts (LLM uses for proposal)
├── src/
│   ├── __init__.py
│   ├── main.py                   # orchestrator (one cron run)
│   ├── sources/
│   │   ├── rss.py
│   │   ├── email_imap.py
│   │   └── base.py
│   ├── filter/
│   │   ├── keyword.py
│   │   ├── budget.py
│   │   └── llm_score.py
│   ├── enrich/
│   │   ├── client_brief.py
│   │   └── proposal.py
│   ├── notify/
│   │   └── telegram.py
│   ├── storage/
│   │   ├── models.py             # SQLite schema
│   │   └── db.py
│   └── llm/
│       └── gemini.py
├── data/
│   └── jobs.db                   # SQLite file (committed)
└── tests/
    └── test_filter.py            # unit tests for filter logic
```

---

## 6. Operational Loop — What Happens Day-to-Day

**Every 30 minutes (automated):**
1. GitHub Actions cron runs
2. Pulls new jobs from all sources
3. Filters, scores, drafts proposals + briefs
4. Pushes top matches to Telegram

**Every morning (your routine):**
1. Open Telegram, see 0-10 matches from overnight
2. For each: read draft proposal (30s), tweak if needed (60s), copy-paste to platform
3. Reply `/submitted JOB_ID` to bot → SQLite logs status
4. Total morning routine: 5-15 minutes

**When client replies:**
1. You manually reply on platform
2. Send `/replied JOB_ID` to bot
3. Bot tracks reply rate over time

**Weekly (automatic):**
1. Sunday 8 PM digest: "This week — 47 jobs seen, 12 matched, 8 submitted, 3 replied, 1 booked"

---

## 7. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Malt has no public RSS | Use email alert forwarding to dedicated Gmail (verified — works) |
| LLM hallucinations in proposals | Generate as draft only, you review before submit |
| Filter too tight, no matches | Lower LLM threshold to 6, monitor first week |
| Filter too loose, spam | Tighten exclude keywords, raise budget floor |
| Gemini free tier limit hit | Code falls back to Groq automatically |
| GitHub Actions limit | Move to Windows Task Scheduler (your PC) |
| Email parsing breaks when platform changes layout | Each source has its own parser; failures logged; you get a `/health` alert |
| You submit duplicate proposals | SQLite dedup check before push prevents re-pushing same job_id |

---

## 8. Time to Build

If approved today:

- **Day 1 (4-5 hours):** Project skeleton, SQLite schema, RSS source for freelance.de, first end-to-end test (job → log)
- **Day 2 (3-4 hours):** Email IMAP source, filter engine (keyword + budget + LLM)
- **Day 3 (3-4 hours):** Proposal generation, client briefing module
- **Day 4 (2-3 hours):** Telegram push, GitHub Actions deployment
- **Day 5 (2 hours):** End-to-end dry run, tune filter thresholds
- **Total: 14-18 hours over 5 days**

You can run profiles + automation in parallel — the profile setup is mostly clicking through forms with copy-paste from `04_profiles.md`, which you can do while I code.

---

## 9. Approval Checklist

Reply with which of these you approve (or want to change):

- [ ] **Decision 1 — LLM:** Gemini Flash (free) as primary, Groq as backup
- [ ] **Decision 2 — Hosting:** GitHub Actions (free)
- [ ] **Decision 3 — Push:** Telegram Bot (free)
- [ ] **Decision 4 — Sources:** freelance.de RSS + Malt/Contra/LinkedIn email forwarding to dedicated Gmail
- [ ] **Decision 5 — Filter thresholds:** Score ≥7 passes, keyword lists as drafted
- [ ] **Decision 6 — Proposal generation:** Draft only, never auto-submit
- [ ] **Decision 7 — Anti-spam:** Max 10 notifications/day + 9 AM daily summary + Sunday weekly digest

**Additional approvals needed:**

- [ ] OK to create a dedicated Gmail address for forwarding (e.g., `mert.freelance.bot@gmail.com`)?
- [ ] OK to commit SQLite DB to a private GitHub repo? (Privacy-safe: just contains job titles, scores, your draft proposals — no client PII beyond what's already public on the platform posting)
- [ ] You will create the Telegram bot via @BotFather and send me the bot token + your chat ID? (I can guide you through this — takes 3 minutes)
- [ ] You will create a Gemini API key on Google AI Studio (free) and add to GitHub Secrets? (I will guide you)

Once you approve, I move to Step 6 (filter rules + proposal templates in detail) and then Step 7 (build).
