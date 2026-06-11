# EnergyLens — Unit Economics & Pricing Review (2026-06-11)

_Triggered by the founder's question: with IoT + battery "all included", does the capacity cost
blow up the margin? **Short answer: it does — but only under the naive "everything on always-on
Fabric" model. The ① Decouple decision we just made is exactly what keeps the pricing profitable.**
All figures are **illustrative ranges** (region/contract vary) — verify live Azure pricing before
quoting._

## Two facts that anchor the cost model (verified 2026-06-11)

1. **App-owns-data embedding works on ANY F-SKU (F2+).** External customers need **no** Power BI
   license; **F64 is not required** (F64 only matters for *internal free* user-owns-data viewing).
   So our embed model can run on a small, even **pausable**, capacity.
2. **The "€32/mo P1" figure in the docs is wrong.** There is no €32 Fabric SKU. Real pay-go (EUR):
   **F2 ≈ €242 · F4 ≈ €484 · F8 ≈ €967 · F64 ≈ €7,740** per month (24/7); reserved ≈ −40%. €32 is
   only reachable by **pausing** an F2 to ~100 h/month — valid for a trial/demo, **not** production.

## Assumptions (stated)

Shared infra €65/mo (frontend+backend+Postgres) · Event Hubs €11/mo per IoT customer (Decouple) ·
metered Copilot LLM €15/mo per Monitor customer · Stripe 1.5%+€0.25 · F2 paused-to-business-hours
≈ €87/mo · USD→EUR 0.92.

## The headline: Monitor tier (IoT @ €299/mo), Decouple vs. Naive

| Customers | World | Capacity/mo | COGS/mo | **Margin/customer** | Margin % |
|---:|---|---:|---:|---:|---:|
| 1 | **Decouple** | €87 (F2 paused) | €183 | **+€116** | **39%** |
| 1 | Naive (Fabric always-on) | €484 (F4 24/7) | €569 | **−€270** | **−90%** |
| 5 | **Decouple** | €242 | €460 | +€207 | 69% |
| 5 | Naive | €967 (F8) | €1,130 | +€73 | 24% |
| 10 | **Decouple** | €484 | €856 | +€213 | 71% |
| 10 | Naive | €967 | €1,229 | +€176 | 59% |
| 25 | **Decouple** | €967 | €1,800 | +€227 | 76% |
| 25 | Naive | €1,934 (F16) | €2,492 | +€199 | 67% |

**Read this:** under **Naive**, your **first** IoT customer loses ~€270/mo (you're paying for an
always-on Fabric capacity that streams 24/7). Under **Decouple**, customer #1 is already +39%
margin, because real-time runs on cheap Event Hubs and Fabric only does pausable embed + batch.
This is the founder's instinct, quantified — and the reason ① Decouple is *load-bearing for the
business model*, not just an architecture preference.

## The other structural cost: the shared capacity floor

| Basic tier (meter-only @ €99/mo), Decouple | Margin/customer | Margin % |
|---|---:|---:|
| 1 customer | **−€55** | −55% |
| 5 customers | +€36 | 36% |
| 10 customers | +€42 | 43% |
| 25 customers | +€56 | 57% |

The first **€87–242/mo of Fabric capacity is a fixed cost** you must amortise. Below ~5 paying
customers you're underwater on it; past that, margins are healthy. Implication: **get to ~5 paying
customers fast**, or keep early capacity paused/minimal.

## Findings (the "absurd/illogical" spots you asked me to catch)

1. **Pricing is sound — but conditional on ① Decouple.** The €99/€299 points are competitive and
   ~40–75% gross margin *if* IoT real-time stays off always-on Fabric. Put it back on Fabric
   EventStream and Monitor goes underwater until ~3–5 customers.
2. **`€32/mo P1` cost figure is wrong/misleading** (CLAUDE.md Phase 0 + `TRIAL-PERIOD-CHECKLIST.md`).
   Replace with the real F-SKU ladder + the Decouple model. "P1" itself is legacy Premium (~€5k/mo);
   under Fabric it's F64 — don't conflate.
3. **Free / low-N is a capacity drain risk.** If the **Free** tier triggers a Fabric bridge/embed,
   each free user consumes shared capacity. **Free must stay Postgres-only** (Tier-1 baseline KPIs,
   no bridge) so its COGS ≈ €0. _(Action: confirm Free never bridges.)_
4. **Copilot LLM is an unmetered variable cost.** A heavy Monitor user could run up Anthropic spend.
   Meter it (cap or monitor) — currently mock/credits, so latent.
5. **F64 is not needed** — earlier docs implied a premium capacity; app-owns-data runs on F2. Real
   saving vs. a reflexive F64.

## Packaging guardrails (recommended)

- **Free = Postgres-only**, explicitly (no Fabric bridge). Verify in code.
- **Monitor IoT marginal = Event Hubs (Decouple)**, never always-on Fabric EventStream.
- **Meter the Copilot**; consider a fair-use cap on Free/Basic.
- **Battery/solar sim = batch compute** (negligible marginal) — fine to bundle in Monitor.
- **Amortise the capacity floor:** consider **annual billing or a small minimum commit** so the
  first ~€90–250/mo of capacity is covered before you scale.

## Recommendations

1. **Keep the price points** (Free €0 · Basic €99 · Monitor €299 · Enterprise custom · Residential
   €49/building + €3/unit) — they work past ~5 customers.
2. **Correct the cost docs** (CLAUDE.md Phase 0 + TRIAL checklist): real F-SKU ladder + Decouple
   model + "capacity floor to amortise". _(Founder approval needed to edit CLAUDE.md.)_
3. **Capacity scaling path:** F2 paused (pilots) → F4/F8 (growth) → **reserved (−40%)** when steady.
4. **Make ① Decouple explicit in the pricing rationale** so no one accidentally runs IoT on
   always-on Fabric and erases the margin.
5. Re-run `outputs/unit_econ.py` with measured load before any customer quote — these are ranges.

Sources: [Microsoft Fabric pricing](https://azure.microsoft.com/en-us/pricing/details/microsoft-fabric/) ·
[Power BI embedded capacity & SKUs](https://learn.microsoft.com/en-us/power-bi/developer/embedded/embedded-capacity)
