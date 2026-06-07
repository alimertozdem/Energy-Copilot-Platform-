# Product Demo Video — Script (v2 — Web App + Copilot Forward)

**Duration target:** 3:30–4:00
**Format:** Loom screen recording + AI voiceover (ElevenLabs)
**Language:** English
**Voice:** Professional male or female ElevenLabs voice ("Adam" / "Bella")

---

## DEMO ARC — what we are saying with this video

This demo flips the old script. The old version walked through 9 Power BI pages. The new version leads with **the live web application + AI Copilot** — the differentiators Microsoft has not seen from us before — and then uses three carefully-chosen Power BI pages as supporting depth.

Why: the application layer is the "wow factor" that proves we are not just a dashboard project. The AI Copilot reasoning over the Microsoft Fabric Lakehouse via tool use is the strongest single artifact for a Microsoft for Startups reviewer.

---

## RECORDING WORKFLOW

### Step 1 — Prepare environments (15 min)

Web app:
- [ ] `npm run dev` (frontend on http://localhost:3000)
- [ ] `uvicorn main:app --reload --port 8000` (backend on http://127.0.0.1:8000)
- [ ] Verify a test account is signed in (smoke@energylens.eu) or use Mert's main account
- [ ] /portfolio loads with KPIs visible
- [ ] /copilot loads (new conversation ready)
- [ ] Mock LLM provider running (no Anthropic credit needed)

Power BI Desktop:
- [ ] Open .pbix file
- [ ] Refresh data
- [ ] Confirm Page 1 (Portfolio), Page 6 (Sustainability/CRREM), Page 9 (Battery) render correctly
- [ ] **Skip Page 8 IoT** — capacity still throttled, will be polished post-submission
- [ ] Zoom 100%, maximize window, hide notifications

### Step 2 — Record screen with Loom

- [ ] Screen only (no webcam)
- [ ] Two takes minimum
- [ ] Walk silently through scenes — voiceover dropped in post
- [ ] Move cursor deliberately, hover on key visuals

### Step 3 — Generate voiceover with ElevenLabs

- [ ] Paste each scene paragraph
- [ ] Generate audio per scene
- [ ] Save each MP3 with scene number

### Step 4 — Assemble in Descript

- [ ] Import Loom MP4
- [ ] Align ElevenLabs audio to scene markers
- [ ] Background music (Pixabay royalty-free, -20 dB)
- [ ] Title card (3 sec): "EnergyLens — Smart Energy for Smart Buildings"
- [ ] Outro card (3 sec): "energylens.eu · Microsoft for Startups Candidate"
- [ ] Export 1080p MP4

### Step 5 — Upload

- [ ] Loom unlisted or YouTube unlisted
- [ ] Copy share link → paste into application

---

## THE SCRIPT (with screen actions)

---

### SCENE 1 — Intro & Sign-in (30 seconds, 0:00–0:30)

**[SCREEN:** Title card "EnergyLens — Smart Energy for Smart Buildings" for 3 seconds. Cut to the EnergyLens landing page showing the sign-in options (Microsoft, Google, Email/Password). Cursor hovers over the three buttons. Click "Sign in with Microsoft", land on `/portfolio`.]

**VOICEOVER:**
> "EnergyLens is a Microsoft Fabric-native energy intelligence platform for European commercial buildings. It is a live web application with three-provider authentication — Microsoft Entra, Google, and email — talking directly to a production Fabric Lakehouse. In the next few minutes I will show you the application, the AI Copilot, and the regulatory depth that Microsoft for Startups would help us scale."

---

### SCENE 2 — Portfolio Overview (45 seconds, 0:30–1:15)

**[SCREEN:** `/portfolio` page. Pan cursor over the four KPI tiles (Total Energy, EUI, Cost, CO₂). Slowly scroll the buildings table — TanStack Table with sortable columns, EPC badges, EUI tier coloring. Hover on Berliner Bürogebäude Alpha (EPC B), then on Frankfurt Datacenter Iota (EPC B, high consumer).]

**VOICEOVER:**
> "This is the portfolio overview, rendered in React, reading directly from the Microsoft Fabric Lakehouse through the SQL Analytics Endpoint. Sub-second response, no embed token round-trip.
>
> Four headline KPIs: total energy, Energy Use Intensity, cost in euros, and net carbon — each compared against a prior thirty-day window. Below, every building in the portfolio is listed with EPC badge, EUI tier, anomaly count, and recommendation count. Sortable, filterable, and styled with the EnergyLens design system.
>
> This is one of three parallel data paths into the Lakehouse — purely custom React. The next page demonstrates the second path."

---

### SCENE 3 — Building Detail with Embedded Power BI (30 seconds, 1:15–1:45)

**[SCREEN:** Click a building row (Berliner Bürogebäude Alpha, B001). Land on `/buildings/B001`. Page shows app chrome on top (logo, breadcrumb, building name) and an embedded Power BI report below. Use Power BI's own page tabs to flip between Page 1 (Portfolio context) and Page 2 (Building Detail).]

**VOICEOVER:**
> "Click any building and you land on a per-building page where Microsoft Power BI is embedded through the V2 embed API, using a service principal in app-owns-data mode. This is path two: the customer sees the EnergyLens brand chrome on the outside, and inside it the full nine-page Power BI experience with DirectLake performance and row-level security ready to flip on. Same Fabric Lakehouse, different surface."

---

### SCENE 4 ★ — AI Copilot (1 minute 30 seconds, 1:45–3:15)

**[SCREEN:** Click "Copilot" in primary nav, land on `/copilot` with the violet AI accent. Start a new conversation. Type the first question slowly so the viewer reads it.]

**Type:** `What was B001's energy in the last 30 days?`

**[Wait for SSE streaming response. The chat shows: user message, then "tool call: query_kpi", then tool result chip, then final assistant message with the number.]**

**VOICEOVER (scene part 1, ~30 sec):**
> "Path three is the AI Copilot. Behind the chat input is an LLM with tool use — six production tools that talk directly to the Microsoft Fabric Lakehouse and to PostgreSQL. The user asks a question in natural language. The model picks a tool. The backend dispatches it. The tool runs a real query against gold_kpi_daily in the Lakehouse. The result streams back over Server-Sent Events and the model summarises it."

**[Tool result appears: query_kpi returned 33,294.49 kWh for B001 over the last 30 days, ↓6.4% versus prior period. The model writes: "Berliner Bürogebäude Alpha used 33,294.49 kilowatt hours over the last 30 days — a 6.4 percent reduction compared with the prior period."]**

**[Type the second question:]**

**Type:** `Compare B001 and B005 on energy.`

**[Tool: compare_buildings. Result: Berlin 33K kWh vs Frankfurt 663K kWh — the data center.]**

**VOICEOVER (scene part 2, ~25 sec):**
> "Each question is a real Lakehouse query. No retrieval-augmented hallucination — the answer is the actual number in your Fabric warehouse, summarised in plain English. Multi-building comparisons, anomaly investigations, retrofit recommendations, battery dispatch simulations — six tools, all live, all reasoning over real data."

**[Type the third question:]**

**Type:** `Show me battery scenarios for B005.`

**[Tool: simulate_battery_scenario. Result: SAMSUNG_NMC_400 with time-of-use strategy, 6,132 €/year, 8.8-year payback.]**

**VOICEOVER (scene part 3, ~30 sec):**
> "For Microsoft for Startups, the important architectural point is this: the LLM provider is abstracted. We are running on a Mock provider right now because Anthropic credit is exhausted — the tools, the dispatcher, and the Fabric queries are all real. With Azure OpenAI credit from Microsoft for Startups, we flip a single environment variable and the live Copilot becomes a production GPT-4o agent reasoning over the Lakehouse. The infrastructure is already there."

---

### SCENE 5 — Sustainability & CRREM Compliance (25 seconds, 3:15–3:40)

**[SCREEN:** In the embedded Power BI report, navigate to Page 6: Sustainability & Compliance. Hover over the CRREM stranding chart and the EPC distribution donut. Show the Scope 1/2/3 breakdown.]

**VOICEOVER:**
> "The regulatory depth that makes this an EU product, not a US import. Page six tracks every building against the CRREM 2030 carbon pathway, the German EnEfG energy efficiency law, EPC distribution, and Scope 1, 2, and 3 emissions in CSRD-ready format. This is the page our enterprise customers care about most: billions of euros in stranding risk made visible at the building level."

---

### SCENE 6 — Battery Strategy & EU 2023/1542 (25 seconds, 3:40–4:05)

**[SCREEN:** Navigate to Page 9: Battery Strategy. Show the dispatch simulation chart, then the EU compliance card highlighting carbon footprint and recycled content.]

**VOICEOVER:**
> "And page nine is where Microsoft Fabric power meets EU regulation. Twelve countries, eight battery chemistries, seven dispatch strategies — every scenario checked against EU Regulation 2023/1542 for carbon footprint labels, state of health, and recycled content. The Copilot you just saw can simulate any of these scenarios in plain English. This is what mid-market property managers cannot get anywhere else."

---

### SCENE 7 — Closing (10 seconds, 4:05–4:15)

**[SCREEN:** Fade back to the EnergyLens logo / landing page. Outro card: "energylens.eu · Microsoft for Startups Candidate"]

**VOICEOVER:**
> "EnergyLens — built on Microsoft Fabric, designed for European compliance, accessible to mid-market property managers, and already executing. We are applying to Microsoft for Startups to scale this from a single founder to the default platform for European commercial real estate. Thank you for watching."

**[End card holds 3 seconds, then fade to black.]**

---

## TIMING BREAKDOWN

| Scene | Duration | Cumulative |
|---|---|---|
| 1. Intro & sign-in | 0:30 | 0:30 |
| 2. Portfolio (custom React) | 0:45 | 1:15 |
| 3. Building detail (PBI embed) | 0:30 | 1:45 |
| **4. AI Copilot ★** | **1:30** | **3:15** |
| 5. Sustainability / CRREM | 0:25 | 3:40 |
| 6. Battery Strategy / EU 2023/1542 | 0:25 | 4:05 |
| 7. Closing | 0:10 | 4:15 |
| **Total** | **4:15** | — |

Trim 10-20 seconds from Scene 4 if total runs over 4:30.

---

## NOTES FOR THE RECORDER (Mert)

- **Page 8 IoT is deliberately skipped.** Capacity throttle on F4 trial means this page may not render cleanly. Post-Tier 2 approval we will add a brief IoT scene in v3 of this video.
- **Three Copilot questions are pre-selected** because they exercise three different tools and three different data shapes (single building, comparison, simulation). Do not improvise — these are smoke-tested.
- **Mock LLM is fine for this demo.** The responses are deterministic and template-driven, but they show the same SSE streaming, tool call lifecycle, and final text rendering as production. A reviewer will see "Mock" only if they read the source — the UX is identical.
- **If a Copilot question fails on the day**, retake just that segment. The whole video can be assembled in Descript from per-scene takes.
- **Voiceover dropped in post** — keep the screen recording silent; ElevenLabs handles the narration. This avoids accent self-consciousness and lets you focus on smooth cursor movement.

---

## VOICEOVER CONFIGURATION (ElevenLabs)

- **Voice:** Adam (professional male) or Bella (clear professional female)
- **Stability:** 50-60
- **Clarity + Similarity:** 75
- **Style Exaggeration:** 0-15
- **Speaker boost:** ON
- **Pacing:** ellipses at end of sentences for natural pauses

### Pronunciation
- "CRREM" → "kre-rem"
- "EnEfG" → "en-eff-gee"
- "DirectLake" → "direct lake" (two words)
- "Lakehouse" → "lake-house" (two syllables, slight pause)
- "SSE" → spelled "S-S-E"

---

## ALTERNATIVE — Your own voice

For a more personal version:
1. Read the script aloud 2-3 times to get comfortable
2. Record in Loom with screen + your voice
3. Edit in Descript: remove fillers, polish

**Trade-off:** Authenticity vs polish. Recommendation: AI voiceover for product demo (cleaner), your own voice for founder intro (more personal).

---

## VISUAL POLISH CHECKLIST

- [ ] Title card at start (3 sec, EnergyLens logo + tagline)
- [ ] Smooth cursor movement, deliberate hovers
- [ ] No accidental clicks, no fast scrolling
- [ ] Copilot scene: let the SSE streaming play out, do not skip ahead
- [ ] Page transitions: cut, no fancy effects
- [ ] Background music: Pixabay royalty-free, -20 dB
- [ ] End card with energylens.eu
- [ ] Auto-captions in Descript, then proofread (especially "CRREM", "EnEfG", "DirectLake")
- [ ] 1080p H.264 MP4, 30 fps, target <200 MB

---

*Script version 2.0 — May 28, 2026 (Web App + Copilot Forward)*
*Ready for: Ali Mert Özdemir to record + ElevenLabs voiceover*
