# Job Targeting & Application Playbook

**For:** Ali Mert Özdemir
**Created:** 2026-06-07 (replaces the scattered targeting notes in 00/04)
**Status:** Active operating manual. Prices below are **provisional/opening** — we calibrate them after a market scan of live postings.

> **TR — bu dosya ne işe yarar:** "Hangi işleri arayacağım, nerede, nasıl başvuracağım, işi alınca nasıl sistemli teslim edeceğim" sorusunun tek cevabı bu. Bot da bu dosyadaki başlıklar etrafında kurulu. Önce §3 (iş başlıkları) ve §6 (bul→yap→teslim hattı) ezberlenecek seviyede oku.

---

## 1. The niche in one line

> I turn fragmented building & portfolio energy data into a **live, CSRD-ready compliance and analytics layer** on **Microsoft Fabric + Power BI** — auditable Scope 1/2/3, plus **EU Taxonomy / EPBD-MEPS / CRREM** exposure.

Three things make this defensible (say them in every pitch):
1. **Microsoft Fabric engineering** (certified, production medallion + Direct Lake)
2. **EU energy/ESG regulation** (CSRD, ESRS E1, GHG Protocol, EPBD recast, EU Taxonomy)
3. **Senior Power BI / DAX** (v60 production measure library)

Almost nobody on the freelance market sits in all three. Power BI people don't know regulation; ESG people don't know Fabric. **That intersection is your moat.**

---

## 2. Who hires (ICPs — refined)

| ICP | Who they are | What they buy | Where to find |
|---|---|---|---|
| **A — ESG / sustainability consultancies** (PRIMARY) | Small/mid firms building CSRD offerings for their clients, short on technical/BI muscle | Productized dashboards, white-label delivery, Fabric build-out | Malt, LinkedIn, freelance.de |
| **B — Property / real-estate portfolio managers** | 20–500 buildings, EPC/MEPS exposure, manual Excel today | Energy KPI dashboards, EPC/CRREM stranding radar | freelance.de, Malt, LinkedIn |
| **C — Mid-cap internal sustainability / data teams** | Already bought Fabric or Power BI, missing the energy/ESG layer | Fabric audit, Scope 1/2/3 build, DAX/perf help | Toptal, Malt, freelance.de |

> **TR:** Bot ve proposal tonu her zaman bir ICP'ye göre ayarlanır. İş ilanını okurken önce "bu hangi ICP?" diye sor — cevabı pitch'in açılış cümlesini belirler.

---

## 3. Job titles to hunt — THE list

This is the heart of the system. Every posting headline maps to one of these tiers. The bot keyword set in `scripts/freelance_bot/config/filters.yml` mirrors this list.

### Tier A — Core (pursue aggressively, drop other things)
These are direct hits. Apply within 24h, personalized.

```
Power BI Developer / Consultant — (ESG / energy / sustainability / real estate context)
Microsoft Fabric Engineer / Consultant / Architect
CSRD Reporting Consultant / CSRD Implementation Specialist
ESG Data Analyst / ESG Reporting Analyst / ESG Reporting Specialist
Sustainability Data Analyst (technical / BI side)
Carbon Accounting Specialist / GHG Reporting Analyst
ESRS / Double Materiality Consultant (data & systems side)
Energy Data Analyst / Energy Management Analyst
Power BI + Azure Data Engineer (sustainability / energy domain)
Sustainability Dashboard Developer
```

### Tier B — Strong adjacent (pursue if budget + scope are good)
You can win these on domain edge even against generalists.

```
Azure Data Engineer (win on energy/ESG domain)
BI Consultant / Analytics Engineer
DAX Developer / Power BI Semantic Model specialist
Data Visualization Specialist (corporate reporting)
Lakehouse / OneLake / Delta Lake engineer
EPC / building performance analyst
EnPI / ISO 50001 energy monitoring specialist
EU Taxonomy alignment analyst
CRREM / real-estate decarbonisation analyst
Real-estate / portfolio ESG analyst
Energy modelling / building energy benchmarking
```

### Tier C — Opportunistic / gateway (low-effort apply; can grow)
Use a small fixed package (P4-style quick win) to get a foot in the door, then expand.

```
"Build me a Power BI report" one-offs
Excel → Power BI migration
"We have ESG/energy data in spreadsheets, need a dashboard"
Data cleaning for ESG / energy datasets
Sustainability report (PDF) where the real need is data plumbing
Power BI refresh / performance fix
```

### Hard NO — skip (bot auto-excludes)
```
Tableau-only / Qlik / Looker-only
Marketing / SEO / ecommerce / social-media analytics
Crypto / web3 / blockchain / NFT
Generic data entry, scraping, transcription
Full-time employment dressed as "contract" (unless you want it)
Budget < €500 fixed or < €30/hr with no upside
"Unpaid test project" beyond a 1-2 hour reasonable sample
```

> **TR:** Tier A görünce her şeyi bırak, 24 saat içinde kişisel başvur. Tier C'yi toplu/hızlı geç — kapı açmak için. Hard NO'yu bot zaten eler ama sen de gözle tanı.

---

## 4. Where + how to search (per platform)

### Malt (PRIMARY — clients reach out to you)
Malt is inbound-first; the lever is **profile keyword density + saved availability**. Make sure your skills tags carry both regulatory and technical terms (see 04_profiles §1.6). Also run weekly manual searches:
```
"Power BI ESG", "Microsoft Fabric", "CSRD Power BI",
"sustainability dashboard", "energy analytics Power BI", "ESRS reporting"
```

### freelance.de (SECONDARY — German Mittelstand, build an RSS feed)
This is the bot's main RSS source. Build the search once, English-only, then grab the RSS URL:
1. Log in → Projektsuche
2. Keywords (rotate): `Power BI`, `Microsoft Fabric`, `ESG`, `CSRD`, `Nachhaltigkeit Dashboard`, `Energiemanagement`, `Energiedaten`
3. Filters: **Remote möglich**, **Projektsprache: Englisch** (and a separate German-tolerant feed if you want volume)
4. Click the **RSS** button → copy URL → paste into `config/sources.yml`

> **TR:** freelance.de'nin %70'i Almanca. İki feed kur: biri English-only (öncelik), biri German-tolerant (bot LLM'i yine de skorlar, sen düşük-Almanca işleri eler). Almanca proje = stakeholder etkileşimi sınırlıysa ve teknik scope netse al.

### Contra (English-only, productized services)
Inbound + you can publish "Services" (= your packages). Set up the 4-5 service cards. Less search, more discovery — keep it current.

### Toptal (apply ONCE, premium floor)
Not a search engine — a vetting gate. Submit the application (04_profiles §4), prep the SQL/PySpark screen, then it becomes passive inbound at $80-150/hr if you pass.

### LinkedIn (cold + warm — high leverage, deferred until profiles live)
Once Malt/Contra are live, mirror the profile and search LinkedIn Jobs + posts:
```
"freelance Power BI ESG", "CSRD consultant contract", "Microsoft Fabric freelance",
"interim ESG data analyst", "sustainability reporting Power BI contract"
```
Set up 2-3 saved searches with email alerts → forward to the bot inbox.

---

## 5. 60-second qualification triage

Before writing a proposal, run a posting through this. If it fails 2+, skip.

```
[ ] Title maps to Tier A or B (or strong Tier C)?
[ ] Budget stated and ≥ floor (€500 fixed / €40/hr)? (no budget = OK to pass to call)
[ ] Language workable? (English, or German with limited interaction)
[ ] Stack overlaps? (Power BI / Fabric / Azure / DAX — OR ESG/energy data that needs plumbing)
[ ] Timeline realistic? (not "full dashboard in 2 days for €200")
[ ] A real decision-maker, not a vague agency relay?
```

**Green flags (bid fast, can charge more):** mentions CSRD deadline, names Fabric/Direct Lake, has data already, mentions auditor, recurring/ongoing, real-estate portfolio with EPC pain.

**Red flags (caution or skip):** "rockstar ninja" language, 50 required skills, equity-only, "ongoing for the right price" with no budget, asks for free full build as "test".

---

## 6. The systematic pipeline: Find → Qualify → Proposal → Call → Close → Deliver

This is the machine. Each stage has a fixed artifact so nothing is improvised.

```
1. FIND      Bot Telegram push + manual saved searches (daily 20-30 min)
                ↓
2. QUALIFY   60-sec triage (§5). Pass → continue. Fail → archive.
                ↓
3. PROPOSAL  Bot pre-drafts using the matched package + best proof artifact.
             You personalize the first 2 sentences (reference their exact pain).
             Attach a LIVE proof link: /demo or /tour (see §7).
             Always end with a discovery-call CTA.
                ↓
4. CALL      30-min discovery (study guide Part V): 6 diagnostic questions,
             screen-share EnergyLens, "position-and-propose".
                ↓
5. CLOSE     Send a 1-page scope memo (problem, deliverable, timeline, price,
             out-of-scope, payment terms: 50% upfront). They sign → start.
                ↓
6. DELIVER   Pick the delivery mode (§8):
             (a) In client's tenant — classic pbix/Fabric handover, OR
             (b) On EnergyLens — onboard their org, scoped login (optional, when you choose)
             Document for handover. Ask for a testimonial. Offer recurring.
```

> **TR:** Her aşamanın sabit bir çıktısı var → improvisation yok. Sistemin kalbi: bot bul + sen 60 sn ele + bot taslak yaz + sen kişiselleştir + demo linki + call. İlk 5 işte bu hattı disiplinle uygula; sonra refleks olur.

---

## 7. Application templates (first-message skeletons)

Keep these short. Lead with THEIR pain, not your CV. Bot pre-fills; you adjust the opener.

### Template A — CSRD / ESG job (ICP A or C)
```
Hi [name],

You're looking for [their exact ask — e.g. "a Scope 1/2/3 dashboard mapped to ESRS E1"].
That's the core of what I do: I build auditor-ready CSRD reporting on Microsoft Fabric + Power BI,
with row-level lineage from raw bill to disclosed kg CO₂e.

I've built exactly this in production — here's a live, no-login demo: [/demo link].

Quick fit: [1 sentence on their specific situation].
I'd suggest a 30-min call to scope it — I'll screen-share the build so you see the real thing.

[Closest package, provisional price/timeline]. Open to adjusting to your scope.

— Mert
```

### Template B — Power BI / Fabric build (ICP C, Tier A/B)
```
Hi [name],

[Their ask] is squarely in my lane — I'm a certified Microsoft Fabric engineer with a
production Power BI / DAX library (v60), focused on energy & ESG data.

Live example of my work (no login): [/tour or /demo link].

I can [their deliverable] in [timeline]. Happy to do a short call and walk you through
how I'd approach yours specifically.

— Mert
```

### Template C — Property / energy KPI (ICP B)
```
Hi [name],

Managing [N] buildings without a single energy view is exactly the problem I solve:
EnPI, kWh/m², EPC/MEPS compliance, anomaly detection — one dashboard, refreshable.

See it live across a 10-building demo portfolio (no login): [/demo link].

[1 sentence on their portfolio]. Shall we do a 30-min call to scope it?

— Mert
```

> **TR:** İlk iki cümleyi MUTLAKA elle kişiselleştir — bot generic yazar, sen onların tam derdine dokun. Demo/tour linki güven sıçraması yaratır; her başvuruda koy.

---

## 8. Delivery modes (choose per engagement)

Two ways to deliver. You decide each time — not locked.

**Mode A — Client's own tenant (classic, default).**
Build in their Power BI / Fabric, hand over .pbix + docs. Clean, no lock-in, what most clients expect. One-off fee.

**Mode B — On EnergyLens platform (optional, when it fits).**
Onboard their buildings into EnergyLens (org isolation + RLS already exist), give them a scoped login, deliver via the running product. Faster (you don't rebuild from scratch), and opens recurring revenue if they stay. Use when: client wants a managed/ongoing solution, has no Fabric tenant, or wants the compliance hub (MEPS/CRREM/Taxonomy) out of the box.

> **TR:** "Her zaman EnergyLens'ten teslim" diye bir zorunluluk yok — senin tercihin. Faz 3'te bu iki modu da pürüzsüz hale getireceğiz (onboarding playbook + scoped login akışı). Şimdilik default Mode A; Mode B'yi istediğin işte aç.

---

## 9. Daily / weekly cadence

**Daily (~25 min):**
- Open Telegram, review bot matches (already scored + pre-drafted)
- Triage (§5), submit 2-3 personalized proposals on the best ones
- Reply to any inbound within a few hours (speed wins on Malt/Contra)

**Weekly (~60 min):**
- Manual sweep on Malt + LinkedIn saved searches
- Check Toptal status / respond to screening
- Refresh freelance.de keywords if volume is low
- Review the week's pipeline (proposals sent → replies → calls → closes)

**Monthly:**
- Calibrate prices against what's actually closing (the deferred pricing decision)
- Update proof artifacts / case studies with any new client win

---

## 10. How the bot plugs in

The bot is the **FIND** stage on autopilot. It:
- Scans freelance.de RSS + Malt/Contra/LinkedIn email alerts every ~30 min
- Filters by the Tier A/B keyword set (§3) → budget floor → Gemini semantic score (1-10)
- Pushes ≥7 matches to Telegram with a **pre-drafted proposal** (picks the closest package + best proof artifact from `personal.yml`)
- Respects quiet hours + a daily cap so it's signal, not noise

You stay in control: bot drafts, **you** personalize + submit (no auto-apply — ToS/ban risk). Tuning happens in `config/filters.yml` (thresholds, keywords) and `config/personal.yml` (packages, proof) — never the code.

See `scripts/freelance_bot/README.md` for setup, and §"Bot canlıya alma" in our session notes for what only you can do (Gemini key, Telegram token, RSS URL, GitHub Secrets).

---

## 11. What's next (sequencing)

1. ✅ This playbook (job titles + pipeline) — done
2. Tune the bot to this exact target list (filters.yml + personal.yml)
3. Refresh the platform profiles for the current app (compliance hub, demo/tour, new case studies) — prices left provisional
4. Bot go-live (your 20-min key setup)
5. Publish profiles → first proposal wave
6. Faz 3: make demo/tour/pilot sales-ready + the Mode-B onboarding playbook

---

## 12. Energy-domain expansion (what your EnergyLens app actually qualifies you for)

Your platform is not just "Power BI + CSRD." It demonstrates real, demonstrable competence across the energy stack. The rule for which energy jobs to chase: **energy + data/analytics/dashboards = yes; pure field engineering = no.** You are the "energy data" person, not the on-site electrical/HVAC design engineer.

| Your app capability | Energy job types you can credibly pursue | Angle to pitch |
|---|---|---|
| EnPI, kWh/m², EPC scoring, building-type thresholds | Energy Analyst · Energy Management Analyst · Building Performance Analyst · ISO 50001 / EnMS data support | "I turn meter + bill + EPC data into an EnPI/benchmarking dashboard" |
| Anomaly detection, HVAC analytics, AFDD (12 rules) | Monitoring & Targeting (M&T) · Measurement & Verification (M&V/IPMVP) · energy waste / fault detection | "automated M&T with anomaly alerts and € waste estimates" |
| Battery dispatch + ROI (EU 2023/1542, 12 countries) | BESS / battery storage feasibility & ROI analyst · energy storage data analyst | "battery dispatch ROI modelling with country-specific pricing" |
| Solar PV self-consumption, specific yield | Solar PV performance / monitoring analyst · PV data analyst | "PV self-consumption + specific-yield monitoring dashboard" |
| GHG Scope 1/2/3, EPEX pricing, decarbonisation page | Carbon / energy decarbonisation analyst · Net-Zero data analyst | "Scope 1/2/3 + decarbonisation pathway, audit-traceable" |
| IoT EventStream, BACnet/Modbus/MQTT, real-time | Smart-building / IoT energy analyst · BMS data integration | "live BMS telemetry to dashboard, sub-second" |
| Compliance hub (EPBD/MEPS, CRREM, EU Taxonomy) | Real-estate decarbonisation / stranding-risk analyst · EU compliance data | "MEPS/CRREM stranding radar across a portfolio" |

**Honest fit line (say this, it builds trust):** "I'm the data and dashboard layer for energy — I work alongside your engineers/auditors, turning their domain into auditable, refreshable analytics. I don't do field surveys or electrical design."

**Energy search terms** (added to the bot too): `measurement and verification`, `monitoring and targeting`, `energy audit`, `energy benchmarking`, `battery storage`, `BESS`, `energy storage`, `solar PV`, `photovoltaic`, `demand response`, `sub-metering`, `building automation`, `heat pump`, `HVAC analytics` — always paired mentally with "is the deliverable DATA/dashboard?" If yes, pursue.

---

## 13. Where to start this week — concrete search recipe

**Order:** freelancermap (live now) → Malt (build profile) → LinkedIn (mirror) → freelance.de/Contra (optional).

### freelancermap (start here — it's already wired to your bot)
1. `Find projects` → search box, run these ONE AT A TIME and skim:
   `Power BI` · `Microsoft Fabric` · `Energy` · `ESG` · `Energiedaten` · `Nachhaltigkeit` · `BESS` · `Energiemanagement`
2. Filters: Remote + Hybrid; you already exclude nothing on DACH (good — the money is there).
3. Your daily email digest also lands automatically; the bot reads it.

### Malt (build profile first, then it's mostly inbound)
- Search weekly: `Power BI ESG` · `energy analytics` · `sustainability dashboard` · `CSRD Power BI` · `energy data`
- Malt is reverse — strong profile keywords matter more than searching. Fill the profile (04_profiles).

### LinkedIn (after Malt/Contra live)
- Saved searches with email alerts: `freelance Power BI energy` · `CSRD consultant contract` · `interim ESG data analyst` · `energy data analyst freelance` → forward alerts to the bot Gmail.

### The 3-question filter you run on every result
1. Is the deliverable DATA/dashboard/analysis (not field engineering)? 
2. Power BI/Fabric/Azure OR energy/ESG data that needs plumbing? 
3. Budget ≥ floor and remote-friendly?
If yes/yes/yes → draft + apply (use templates in §7).
