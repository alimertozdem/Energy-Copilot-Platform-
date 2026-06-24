# EnergyLens — Founder Operating Plan

> **Status:** DRAFT v1 — for product-owner (Mert) review and markup
> **Date:** 2026-06-18
> **BMAD layer:** Business (sequencing, funding, go-to-market) — precedes any further Architecture/Data work
> **Supersedes:** the implicit "build more, then raise" assumption. Confirms the wedge in
> [`2026-06_growth_strategy.md`](./2026-06_growth_strategy.md) and the COGS model in
> [`unit-economics-pricing-review.md`](./unit-economics-pricing-review.md).

This plan exists because the platform is **code-complete** and the binding constraint is **founder
time + go-to-market + proof on real buildings — not features.** It reorganizes the next ~6 months
around that reality.

---

## 0. The decision that anchors everything

Two founder constraints were surfaced on 2026-06-18:

1. **Income is needed now.**
2. **The platform has zero paying pilots and runs on synthetic data only** (the "reality gap").

These two are solved by the **same move**, and that is the spine of this plan:

> **Earn survival cash by taking energy/ESG freelance engagements, delivered *through* EnergyLens —
> so every paid gig is simultaneously income, a real-building product test, and a reference.**

What this plan explicitly **rejects** (and why):

- **"Raise a pre-seed/angel round now."** A round takes ~3–9 months `[Muhtemel]`, pays the founder
  nothing in the interim, and with no traction prices badly or fails. Investor capital is *growth
  fuel for the company*, not founder income `[Kesin]` — using a round to cover rent is a red flag.
  → Equity moves to the **last** rung of the funding ladder (§8), unlocked by proof, not used to buy it.
- **Carrying rent on the startup's back.** Survival cash must be **decoupled** from startup
  progress so financial pressure never forces a bad startup decision (premature round, over-promised
  pilot). Freelance is the decoupling mechanism.

---

## 1. Strategy in one paragraph

EnergyLens's wedge is the **data-light, hardware-free, estimation-first energy + compliance
intelligence layer for German building portfolios** (Hausverwaltung / housing companies first),
priced on the rising cost of *doing nothing* (EPBD MEPS 2030/2033, rising CO₂ price) plus subsidy
(BAFA/KfW) ROI. For the next ~6 months the founder funds himself with **energy/ESG freelance work
delivered on the platform**, which doubles as live validation on varied real buildings and a growing
reference base. Non-dilutive grant funding (EXIST) is pursued in parallel. An equity raise is
deferred until 1–2 paying references + an EXIST signal exist, at which point the raise narrative
shifts from "pre-revenue idea" to "validated, founder-proven traction."

---

## 2. The freelance-as-engine model — one motion, five outputs

Each freelance engagement, if scoped correctly, produces five things at once:

| Output | How the gig produces it |
|---|---|
| **1. Cash now** | Paid day-rate / fixed-fee engagement — the survival-cash line. |
| **2. Real-building validation** | The app is exercised on a *real* portfolio, closing the reality gap one building type at a time. |
| **3. Reference / case study** | A satisfied client (anonymized) becomes a logo, quote, or before/after artifact. |
| **4. EXIST evidence** | Real client engagement = market-pull proof in the grant application. |
| **5. Investor traction** | "Founder delivered N paid engagements on the product" beats any deck `[Muhtemel]`. |

### 2.1 The one risk that kills this model: the **services trap** `[Muhtemel]`

Consulting revenue is seductive because it pays today. The failure mode: you keep taking bespoke
gigs, the product degrades into a *tool you use to deliver services*, and the SaaS never ships. Many
"product + consulting" founders never escape and end up a 1-person agency.

**Guardrails (non-negotiable):**

- **Productized, not bespoke.** Sell one or two **fixed-scope, fixed-price** offers (§3), not
  open-ended consulting. If a gig needs heavy custom work outside the offer, it is a no (or a
  clearly-priced exception), not a pivot.
- **Every gig must harden the *product*, not a one-off spreadsheet.** Deliverables are generated
  *from* EnergyLens. If you find yourself doing the analysis in Excel and the app on the side, stop.
- **Cap the services share.** Target: as references accumulate, shift effort from "freelance for
  cash" toward "SaaS subscriptions + EXIST stipend." Freelance is the **bridge**, not the
  destination.
- **Reusability clause in every contract** (§5) — without it, output #3 (references) is legally lost.

---

## 3. The freelance offer (positioning) — **OPEN DECISION**

The offer must be (a) liquid on freelance markets, (b) deliverable through EnergyLens, (c)
reference-compounding toward the product's ICP. Recommended:

- **Primary (recommended):** *"EPBD/GEG Readiness & CapEx Prioritisation Screening"* for DE building
  portfolios — portfolio benchmark, CRREM stranding view, ranked retrofit measures with BAFA/KfW
  subsidy-adjusted ROI. **Most product-aligned**; references compound directly onto the Hausverwaltung
  wedge. Indicative: **€2–5k per portfolio engagement** `[Tahmin]`.
- **Secondary / upsell:** *ESRS-E1 / VSME-light energy & emissions reporting* (post-Omnibus). Larger
  market, recurring potential. Use the approved legal language ("ESRS-E1-aligned", **not**
  "CSRD-compliant"). Indicative: **€3–8k** `[Tahmin]`.
- **Off the table:** pure Microsoft Fabric / data-engineering gigs. They pay, but they do **not** go
  "through" EnergyLens, so they yield zero product validation or reference — they're just a job. Only
  take them as pure emergency cash, knowing they don't advance the startup.

> **Decision needed from you (domain + market expert):** which is the primary freelance offer — the
> EPBD retrofit-screening line, the ESRS/VSME reporting line, or both with one as headline? This
> determines which references you accumulate.

**Delivery format:** a branded PDF/report + a short walkthrough, generated from the platform, every
number carrying its "indicative / assumptions" tooltip (the calc-transparency layer already built).
**Channels:** freelance.de, Malt, Upwork (ESG/energy), plus direct outreach to the C4 lead and
Hausverwaltungen.

---

## 4. The validation loop — gig → product → reference

```
  Freelance gig (real portfolio)
        │  ingest real bills/EPC/meter data  → closes the reality gap on THIS building type
        ▼
  Run EnergyLens on it (founder QA's every output, §5)
        │  note what broke / what assumptions held → minimal, targeted product fixes only
        ▼
  Deliver paid report  →  cash (#1)
        │  contract reuse clause → anonymized case study (#3)
        ▼
  Reference + real-data proof  →  EXIST evidence (#4) + raise narrative (#5)
```

**Building-type focus reconciliation:** take whatever building types the freelance market pays for
(income first), **but** track which align with the Hausverwaltung / commercial wedge. A residential
portfolio or retail-chain reference is worth more *strategically* than a one-off exotic building —
weight outreach accordingly. Income variety is fine; **reference variety should converge** on one ICP.

---

## 5. Delivery & energy-logic guardrails (defensibility + legal)

A paid deliverable raises the bar above an internal demo. Per the project's own energy rules:

- **App output = draft, never gospel.** The platform was trained on synthetic data; on a *new real
  building* its first output is a hypothesis. **Manually sanity-check every figure** before it reaches
  a paying client. The freelance gig is also your QA harness — but only if you treat output as draft.
- **Ranges + stated assumptions, always.** No exact single-point claims on savings/ROI. Indicative /
  screening framing protects both the client decision and you. (This is already house style — enforce
  it under a paid contract.)
- **Liability framing.** Deliverables are *decision-support screening*, not stamped engineering /
  *Energieberater* certification (unless you hold/partner that qualification). Say so in the report.
- **IP & reuse clause in every contract** `[Kesin importance]`: you retain the right to (a) reuse
  anonymized/aggregated results as a reference and case study, and (b) keep product learnings. Without
  this clause, output #3 is legally unusable. Standard, but must be explicit.

---

## 6. 90-day plan

| Weeks | Focus | Concrete output |
|---|---|---|
| **1–2** | Package the offer (§3). One-page service description + fixed price + sample (anonymized) report. Pick primary offer. | A sellable offer + a portfolio profile on freelance.de / Malt / Upwork. |
| **2–6** | Outbound + close first gig. Work the C4 lead and a shortlist of 15–20 DE Hausverwaltungen / ESG contacts. | **1 paid engagement** signed (cash + first real portfolio). |
| **3–8** | Deliver gig #1 *through the platform*; run the validation loop (§4); fix only pilot-blockers. | Paid report delivered; reality-gap closed on 1 building type; case study #1. |
| **4–10** | EXIST application package in parallel: HWR Incubator host, Dr. Chelabi mentor letter, solo budget (~€45k, verify at application) `[Tahmin]`. | EXIST submission ready / submitted. |
| **8–12** | Gig #2; begin converting a freelance client to a recurring SaaS subscription (Basic/Residential). | 2nd reference; **first recurring MRR** attempt. |

**Milestone that ends "income-now" mode:** ~€X/month of combined freelance + first MRR that covers
your runway (you set €X). Until then, freelance volume is the priority lever.

---

## 7. Weekly operating split (solo, freelance-primary)

Indicative, adjust to live gig load:

- **~50% — Freelance delivery + sales** (the cash engine; also the validation loop).
- **~20% — Product hardening**, but *only* fixes surfaced by real gigs. No new modules/segments.
- **~20% — EXIST + funding prep.**
- **~10% — Outbound for the next gig / SaaS conversion.**

**STOP list** (until a real gig or pilot demands it): new features, new segments, the 3-pillar
multi-segment build, estimator polish beyond what gig #1 needs. The 2026-06-17 multi-segment scope
stays a **vision/TAM narrative for investors**, not an operating workstream.

---

## 8. Funding ladder — rung by rung

Climb in order. Each rung is unlocked by a **proof milestone**, not by ambition.

| Rung | Source | Unlock milestone | Dilution | Role |
|---|---|---|---|---|
| **1** | **Freelance income** | — (now) | none | Survival cash + validation engine. |
| **2** | **First SaaS MRR** | A freelance client converts to a subscription | none | Proof the product sells, not just the founder. |
| **3** | **EXIST grant** `[Tahmin ~€45k solo]` | Host + mentor + market-pull evidence (from rung 1) | none | Living stipend + coaching; buys focused runway. |
| **4** | **Angel / pre-seed** | 1–2 paying references + EXIST signal + early MRR | dilutive | Growth fuel — hire, capacity, GTM. **Only here.** |

**Why this order beats "raise now":** at rung 4 *after* rungs 1–3, you negotiate from "validated,
de-risked, non-dilutive-funded traction." That typically moves valuation and terms materially
`[Muhtemel]` versus pitching a pre-revenue synthetic-data idea.

---

## 9. What money changes — the raise story (for rung 4)

When you do raise, the honest pitch for *why capital is needed* and *what it unlocks*:

- **Money does NOT buy:** the product (built) or new features (not the constraint).
- **Money buys, in priority order:**
  1. **Founder + first hire full-time** — convert the validation engine into a repeatable sales motion.
  2. **A GTM/commercial co-founder or first salesperson** (see §10).
  3. **"Activate the paid layers" COGS** — Fabric F-SKU (€242+/mo), Event Hubs for IoT real-time
     (the ① Decouple model), Copilot LLM credits. These switch on *per paying customer*, so they're
     scale cost, not upfront burn.
  4. **Credibility data** — licensed EPC/CRREM data, and (Tier-C, only if funded) satellite/3D
     screening. Marginal accuracy gain; the dominant levers stay archetype + bill + HDD + EPC.
- **Layer-activation potential (the TAM slide)** `[Tahmin]` — illustrative, contingent on proof:
  Basic €99 → Monitor €299 (IoT/battery/copilot) → per-building scale → Residential €49+€3/unit →
  multi-segment **white-label** (banks/insurers/REIT funds/Energieberater). Each is a revenue line;
  none is real until validated. Present as vision, never as forecast.

---

## 10. Co-founder stance

Decision was "undecided — discuss." Position:

- A co-founder search pays nothing now and takes 3–6 months `[Muhtemel]` → it is a **parallel track,
  not the thing that saves you**.
- **Reframe the search.** Don't look for "a co-founder"; look for **someone who can put a paying
  customer in front of you within 60 days** — i.e., a commercial partner with a Hausverwaltung /
  Energieberater / ESG-buyer network. If that person exists and is willing, partner. If not, stay
  solo and sell; revisit at rung 4 when you can also offer equity + salary.
- A pure technical co-founder is **low priority** — the build is done; your gap is distribution.

---

## 11. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| **Services trap** — freelance eats the product | High | §2.1 guardrails: productized offers, app-generated deliverables, capped services share. |
| **Income pressure forces bad startup calls** | High | Decouple survival cash (freelance) from startup progress (§0). |
| **App output wrong on a real building** (synthetic-trained) | High | §5: every figure manually QA'd; ranges + assumptions; screening-not-certification framing. |
| **No reference rights** | Medium | IP/reuse clause in every contract (§5). |
| **Scope sprawl** (multi-segment pull) | Medium | §7 STOP list; multi-segment = investor narrative only. |
| **EXIST timing/eligibility shifts** | Medium | Verify current EXIST rules at application; don't bank runway on grant timing. |
| **Solo burnout / bandwidth** | Medium | Weekly split (§7); revisit co-founder at rung 4. |

---

## 12. Open decisions (product owner)

1. **Primary freelance offer (§3):** EPBD retrofit-screening, ESRS/VSME reporting, or both with one
   as headline? *(Determines reference accumulation — your call as domain + market expert.)*
2. **Runway number (§6):** the €X/month that ends "income-now" mode — so the plan has a finish line.
3. **EXIST timing:** start the application package now (parallel) or after gig #1 lands?
4. **Co-founder (§10):** open a *targeted* search (network-bringing commercial partner) now, or defer
   to rung 4?

---

_Sources / dependencies: [`2026-06_growth_strategy.md`](./2026-06_growth_strategy.md) ·
[`unit-economics-pricing-review.md`](./unit-economics-pricing-review.md) ·
[`pricing-model-v2.md`](./pricing-model-v2.md) · EXIST figures per prior research — verify at
application. All ROI/savings/figures herein are indicative ranges, not commitments._
