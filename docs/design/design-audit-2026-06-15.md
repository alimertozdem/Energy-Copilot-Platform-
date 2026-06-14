# EnergyLens — Persona-Based Design Audit (2026-06-15)

_Scope: app-wide design review through six lenses — energy **engineer**, **consultant**, energy
**manager**, **auditor**, end **user/owner**, and **investor**. Method: read the design system
(`globals.css`), the app shell/nav (`AppChrome.tsx`), the public landing (`app/page.tsx`), and the
54-page surface map. **Findings first, then a prioritized plan. No code changed yet — you pick what
we implement.**_

---

## 0. Verdict up front (the honest headline)

**The problem is NOT visual craft.** The "Emerald Pulse" dark system is genuinely mature: coherent
brand tokens, a real type scale, per-page accent identity, accessibility done properly
(`:focus-visible` ring, `prefers-reduced-motion` damping, `aria-current`, skip-link), anti-layout-shift
details (`scrollbar-gutter: stable`), and a polished landing with a live demo CTA. A designer would
respect this.

**The real design levers — the ones that affect *selling* — are two:**

1. **Information architecture (IA) overload.** 9+ top-level nav items + 54 pages, one flat surface,
   no "start here."
2. **No persona-aware "first screen."** Everyone sees the same everything; the app doesn't adapt its
   face to who's looking.

For a startup that needs to convert a stranger into a pilot, **these two outweigh any pixel polish.**

---

## 1. Cross-cutting findings (priority-ordered)

### P0-1 · Navigation / IA overload
Primary nav today: Portfolio · Buildings · Residential · Actions · Alerts · Compliance · Decarbonise ·
Copilot · Solar · **+More** — then 54 routes underneath. Every persona feels this:
- **Investor / new user:** "what *is* this?" — 10 tabs dilute the one-line story; decision paralysis.
- **Energy manager:** wants a focused daily cockpit, not a 10-tab hunt.
- **Engineer/auditor:** can navigate it, but it reads "tool a solo dev kept adding to," not "product."

**Fix:** collapse into ~4 intent clusters with a clear default home. Suggested grouping:
**Monitor** (Portfolio · Buildings · Alerts) · **Act** (Actions · Decarbonise · Financing · Solar) ·
**Comply** (Compliance · Reports) · **Assist** (Copilot). Residential becomes a segment toggle, not a
peer tab. This is the **single highest perceived-quality win** and is pure front-end.

### P0-2 · No persona-aware first screen
Same nav + same landing for a facility manager, an auditor, and an investor on a demo. Each wants a
different cockpit. Your **3-layer access model (RLS + AppNav + Subscription)** already *gates* modules;
extend it to *prioritize* — a role/segment-aware default view. Minimum viable version: a real
**`/dashboard` "home"** that leads with the 3–4 things that persona acts on, with everything else one
click away.

### P1-3 · Dark-only theme is a persona tension
Single dark theme. Great for the **investor/modern** feel; but **auditors and consultants** present to
clients and review document-style data in bright offices — they often expect a light/"report" mode.
Your **PDF exports are already light** (good instinct). **Fix:** a **light/report mode for the data &
report views** (not necessarily the whole marketing shell). Flagged as a tension to decide, not a
mandate.

### P1-4 · Trust signals are thin for the skeptical personas
Landing trust strip lists **tech** (Fabric, BACnet/Modbus/MQTT, EU Reg 2023/1542, CRREM) — perfect for
engineers, weak for the people who sign: auditors, consultants, investors. They want **proof and
provenance**: "measured vs **indicative**," methodology, data source, and (eventually) a reference
logo/case study. You already built a **calc-transparency / glossary** layer — today it's a tooltip.
**Fix:** promote honesty/methodology into a *visible trust feature* (a "How we calculate / data
provenance" surface), and reserve a spot for the first pilot logo.

### P1-5 · Density without progressive disclosure (verify per page)
A 9-page report + many feature pages risk "wall of numbers." **Fix:** summary-first, drill-down on
demand on the heaviest screens. _To confirm per page in the deep-dive pass._

---

## 2. Per-persona scorecard

| Persona | Wants | Today | Gap → move |
|---|---|---|---|
| **Energy engineer** | units, method, data density | strong; calc-transparency built | surface method+assumption on *every* number, consistently |
| **Consultant** | client-presentable export | PDF reports exist (light) | + light/report mode in-app; white-label-ready header |
| **Energy manager** | daily cockpit + alert triage | Alerts/Actions badges exist | a **"Today" home**; lift triage out of the 10-tab bar |
| **Auditor** | audit trail, standards map, provenance | compliance hub + audit logs exist | surface **provenance + "measured vs indicative"** prominently |
| **End user / owner** | "what do I do + ROI," plain words | Copilot + Decarbonise/MACC + tour exist | a simpler **guided entry**; hide expert tabs by default |
| **Investor** | crisp story, polish, proof | landing is strong | a **guided demo path**; the in-app sprawl currently dilutes "what is this in 10s" |

---

## 3. Recommended plan (you choose scope)

| # | Change | Effort | Why it sells |
|---|---|---|---|
| **P0-1** | Nav → 4 clusters + clear default home | M | Biggest "this is a product, not a project" jump |
| **P0-2** | Persona/segment-aware first screen (`/dashboard`) | M–L | Each viewer sees *their* value in 10 seconds |
| **P1-3** | Light / report mode for data & report views | M | Unlocks auditor/consultant buyers |
| **P1-4** | Promote methodology/provenance into a visible trust feature | S–M | Converts the skeptical signers |
| **P1-5** | Progressive-disclosure pass on heaviest pages | M | Calms density; faster comprehension |
| **P2-6** | Micro-consistency sweep (accent usage, empty/loading already strong) | S | Final polish |

**Suggested order:** P0-1 → P0-2 → P1-4 → P1-3 → P1-5 → P2-6. P0-1 alone changes the first
impression the most, for the least work.

## 4. What's explicitly NOT broken (don't touch)
Brand tokens, type scale, accessibility, motion, loading/empty/error states, the landing hero, the
auth card. These are assets — the audit builds on them, it doesn't redo them.

---

### Next step
Tell me which rows in §3 to implement (or "all, in order"). For each, I'll do a **page-level deep
dive** (read the real screens), propose the concrete change, then edit the code — one cluster at a
time per our cadence.
