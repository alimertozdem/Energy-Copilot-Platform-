# EnergyLens — Pilot Acquisition Plan (2026-06-14)

_Goal: land the **first real pilot(s)** → produce the first real-data **case study**, the single
artifact that flips "feature-complete" into "sellable." This **builds on** existing assets, it does
not replace them: `docs/c4-outreach/`, `docs/startups-application/06_gtm_strategy.md`,
`docs/startups-application/BSBI_PILOT_MAILS.md`, `docs/mentor-meeting/EnergyLens_Pilot_Data_Request`.
Inbound + status tracked in the already-live `/pilot` form → `/admin` queue._

---

## 0. The one objective

Not "many customers." **One real building's data, end-to-end, with a named reference.** Everything
below serves that. **Success =** (a) 1–2 pilots live on real data, (b) one named case study +
testimonial, (c) one willingness-to-pay signal. Until this exists, the product is "built" but not
yet "sold."

## 1. The pilot offer (identical for every target)

- **Free, time-boxed:** 6–8 weeks, 1–3 buildings.
- **Zero hardware, zero risk:** they send **bills / meter exports only** — the no-hardware wedge.
  Data stays in the Microsoft cloud, row-level isolated (RLS).
- **They get:** a live dashboard + an end-of-pilot report = EPBD/MEPS risk + prioritized retrofit
  ROI + subsidy (BAFA/KfW) capture, per building.
- **You get:** real (messy) data, a **named case study + testimonial**, and a pricing conversation.
- **Framing guardrail:** "no cost, fully managed by me, no commitment" — free must not read as
  low-quality. All figures shown as **indicative ranges** (honesty layer).

## 2. Three tracks — run in parallel

### Track 1 — Warm leads already loaded (START THIS WEEK)
Templates exist; the work is to **send**, not to write.

1. **BSBI campus pilot** — fastest path to the first case study. Send the **supervisor** mail, then
   the **facility manager** mail (`BSBI_PILOT_MAILS.md` — sequencing already specified). Academic
   "M.Sc. capstone" framing makes it low-risk for them.
2. **C4 / Boris Peter** — warm (professor intro pending). Note: C4 is embodied-carbon / structural,
   **not** the wedge ICP → treat as a **credibility conversation + possible channel partner**
   (consultants who could resell), not a Hausverwaltung pilot. Use `c4-outreach/01_intro_email.md`;
   fill **[Professor name]** + **[phone]**. _This week: confirm the intro with Dr. Chelabi._

### Track 2 — The wedge campaign (where "sellable" gets proven): small-mid DE Hausverwaltung
New ICP, predates the old GTM doc. This is the commercial proof.

- **Who:** firms managing ~200–3,000 units, mixed residential/commercial, **no in-house energy
  manager**, exposed to EPBD/MEPS + rising CO₂ cost, with a real capital-allocation decision.
- **Where to find them:**
  - **Associations / directories:** VDIV (Verband der Immobilienverwalter), GdW member housing
    companies & cooperatives, BVI — member lists + events.
  - **LinkedIn:** titles _Geschäftsführer · Leiter Technik · Nachhaltigkeit · Bestandsmanagement_ at
    Hausverwaltung / Wohnungsunternehmen.
  - **Communities:** Berlin PropTech & Energy meetups; EXIST/HWR network once admitted.
- **Cadence:** **5–8 researched, personalized touches/week** (not spray). Hook = a compliance
  deadline + subsidy money currently on the table.

### Track 3 — Enabler: EXIST / HWR incubator
Admission → warm intros into DE real-estate/proptech + credibility. Progress the **HWR Incubator
application + Chelabi mentor letter** in parallel (both drafted — see `exist_strategy`).

## 3. NEW asset — DE Hausverwaltung cold email (the missing template)

> German lands far better with this ICP. Draft below; have a native speaker sanity-check before bulk
> send. English fallback follows.

**Subject:** Welche Gebäude zuerst sanieren? — kostenfreier EPBD-Schnellcheck (ohne Hardware)

```
Sehr geehrte/r Frau/Herr [Name],

als Verwalter von rund [X] Einheiten stehen Sie vor der EPBD/MEPS-Pflicht und steigenden
CO₂-Kosten — bei begrenztem Budget. Die entscheidende Frage ist: welche Gebäude zuerst, mit
welcher Maßnahme, und welche Förderung (BAFA/KfW) rechnet sich wann?

Ich habe EnergyLens gebaut — eine Softwareschicht, die genau das beantwortet. Ohne neue
Sensoren: Sie senden nur vorhandene Verbrauchs- bzw. Abrechnungsdaten, wir liefern eine
priorisierte Sanierungs- und Förder-Roadmap je Gebäude.

Ich biete einen kostenfreien 6–8-Wochen-Pilot für 1–3 Ihrer Gebäude an — unverbindlich,
vollständig von mir betreut. Im Gegenzug bitte ich nur um Ihr Feedback und, bei guten
Ergebnissen, eine Referenz.

Hätten Sie 20 Minuten für ein kurzes Gespräch? Live-Demo (ohne Login):
https://energy-copilot-platform.vercel.app/demo

Mit freundlichen Grüßen,
Ali Mert Özdemir
Energy Engineer · M.Sc. Energy Management, BSBI Berlin
alimertozdem@gmail.com · linkedin.com/in/alimertozdemir96
```

**English fallback (subject):** Which buildings to renovate first? — free EPBD screening, no hardware
_(same body, translated; use only if the contact prefers English.)_

## 4. Pipeline math (solo-realistic)

- **Warm (Track 1):** ~5 touches → 2–3 conversations → **1 pilot** (BSBI most likely).
- **Wedge (Track 2):** ~40 targeted touches over 6–8 weeks → ~6–8 replies → 2–3 calls → **1 pilot**.
- **Targets:** 1 pilot signed in **~4 weeks** (warm), 1 commercial pilot in **~8 weeks**.

## 5. Weekly cadence (≈90 min/day is enough)

- **Mon:** research + queue 10 wedge targets.
- **Tue/Wed AM (09:00–11:00):** send (highest academic/business engagement window).
- **Thu:** follow-ups (one gentle nudge at 7–10 days).
- **Fri:** log replies in `/admin`, book calls, iterate subject lines on reply-rate.

## 6. Track & measure (use what's already built)

- **Inbound:** `/pilot` public form → `/admin` pilot queue (live).
- **Outbound:** a simple sheet (target · channel · date · status · next step) — I can generate it.
- **KPIs:** touches, reply %, calls booked, pilots signed → review every Friday.

## 7. Honesty guardrails (non-negotiable)

- Indicative ranges, never promises — "screening-level," "estimated."
- "ESRS-E1-aligned reporting support," never "CSRD-compliant."
- GDPR: their data, RLS-isolated, deleted on request. Say so up front — it lowers the barrier.

## 8. What I (Claude) can do now / once connectors are live

- **Now:** draft + personalize every email, build the target-tracking sheet, prep the end-of-pilot
  report template, and tighten the one-pager/demo talking points.
- **Once GitHub connector is live:** keep the repo demo-ready (release tags, clean README) so a
  prospect who looks technical sees a credible project.
- _(No CRM connector exists yet — if outreach scales, that's the next connector to consider.)_

---

### Immediate next actions (this week)
1. Send the **BSBI supervisor** mail (Tue/Wed AM) → then facility-manager mail per the sequence.
2. Confirm the **C4 intro** with Dr. Chelabi; fill + queue the C4 email.
3. Tell me to **generate the wedge target sheet** + localize the German template — then we start
   Track 2's first 10 targets.
