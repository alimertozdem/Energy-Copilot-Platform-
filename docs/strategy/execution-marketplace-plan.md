# EnergyLens — Execution Marketplace (BMAD plan)

> **Status:** PLAN for approval (2026-06-12). Builds on growth-strategy §9.
> **Model decided with Mert:** **hybrid — MVP lead-gen → target take-rate** (commission on the
> realised retrofit between customer and installer).
> **Build gate:** later phase — *after* a commercial reference base + first residential pilots.

---

## 1. The idea — close the insight → action loop

A customer who sees a recommended measure (heat pump, insulation, PV) can, **in-app**, reach vetted
installers, get quotes, and commission the work. Today the platform says **what** to do, **how** to
fund it (BAFA/KfW via `/financing`), and **tracks** it (`/actions`) — it does not connect the owner
to **who** does it. The marketplace is that missing connective layer.

## 2. Business

- **Two sides.** Demand = building owners / Hausverwaltungen with quantified recommendations
  (already produced by the product). Supply = vetted installers/contractors (heat pump, insulation,
  PV, hydraulic balancing) by region.
- **Revenue (hybrid, decided):**
  - **MVP — lead-gen:** a fee per qualified lead/introduction routed to an installer (fixed or small
    %). No money flows through us → **no escrow/legal load**. Validates demand + supply willingness
    to pay.
  - **Target — take-rate:** a % commission on the **realised retrofit project value**. Higher revenue
    and better alignment, but needs quoting + payments/escrow + liability framing.
- **Why a later build phase:** a two-sided market needs vendor onboarding + vetting/trust,
  quoting/bidding, payments/escrow, legal/liability — plus the classic cold-start. Sequencing the
  risk (lead-gen first) is exactly the hybrid path.

## 3. Architecture — the connective layer

```
recommendation engine (WHAT) → [ MARKETPLACE (WHO) ] → /financing (HOW to pay) → /actions (TRACK)
```

Three of the four already exist; the marketplace is the new middle. New surfaces/entities are
**Postgres-only, additive — no Fabric dependency**:

| Entity | Purpose | Phase |
|---|---|---|
| `vendors` | company, regions, measure types, vetting status, rating | 1 |
| `vendor_measures` | vendor ↔ measure-type/capability map (for matching) | 1 |
| `rfqs` | a customer building + measure → routed to matched vendors | 1 |
| `quotes` | vendor response: price, scope, timeline | 2 |
| `projects` | accepted quote → commissioned work → milestones → completion (**where take-rate is captured**) | 3 |

**Reuse:** the recommendation/actions payload (measures + CapEx/subsidy), `/financing` (BAFA/KfW),
`/actions` (status tracking), and the audit log.

## 4. Data & trust (trust *is* the product)

- **Vetting fields:** trade license (Handwerksrolle), insurance, references, BAFA/KfW eligibility
  (energy-efficiency expert / Fachunternehmererklärung).
- **Matching keys:** measure_type × region (DE first) × capacity.
- **Privacy:** a customer's building data is shared with a vendor **only on explicit RFQ consent**.

## 5. Logic

- **Matching:** measure_type × region → ranked vendors (vetting + rating + capacity).
- **Flow:** RFQ → quote → compare → accept → project; commission captured at a project milestone
  (Phase 3).
- **Energy-logic gate UNCHANGED:** the marketplace routes to humans who execute; it invents no
  engineering logic. Recommendations keep stating their assumptions (ties to the calc-transparency
  layer + `residential-retrofit-calculations.md`).

## 6. Phased roadmap (dependency-ordered)

- **Phase 0 — now, zero-infra:** a "Request an installer" affordance on a recommended measure →
  **founder-brokered** intro (manual). Validates demand + supply appetite before any build. Reuses
  `/actions`.
- **Phase 1 — lead-gen MVP:** vendor registry + matching + RFQ (email/notify) + lead fee. One region
  (DE), 2–3 measure types (heat pump, insulation, PV).
- **Phase 2 — managed quotes:** in-app quote submission + compare; a vendor portal-lite.
- **Phase 3 — take-rate:** payments/escrow + commission capture on project milestones + legal/
  liability + contracts.
- **Cold-start:** seed supply via installer/Handwerk partnerships + the EXIST/BSBI network; demand is
  already in-product — **every quantified recommendation is a latent RFQ**.

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Trust / liability | Vetting bar; "EnergyLens introduces, does not warrant the work" framing (Phase 0–1); escrow + contracts only at Phase 3 |
| Chicken-and-egg | Lead-gen (low supply commitment) + manual brokering (Phase 0) |
| Regulatory | Installer licensing (Handwerksrolle), BAFA/KfW Fachunternehmer requirements — captured in vetting |
| Payments/escrow legal | Deferred to Phase 3 (the heaviest piece) |

## 8. Open decisions (product owner)

1. **Commission numbers:** lead fee (€/lead) + eventual take-rate % — set when Phase 1/3 nears.
2. **Vetting bar:** minimum (license + insurance) vs curated (references + BAFA-expert) — trust vs
   supply liquidity.
3. **Geography:** DE first (recommended; matches the residential vertical) — confirm.
4. **Build trigger:** after N commercial references / first residential pilots — confirm the gate.

## 9. Explicitly deferred

- Real build (Phase 1+) until a commercial reference base + residential pilots exist.
- Payments / escrow / legal until Phase 3.
- Non-DE geographies.

_Links: growth-strategy §9 · `residential-retrofit-calculations.md` · `/financing` (BAFA/KfW) · `/actions`._
