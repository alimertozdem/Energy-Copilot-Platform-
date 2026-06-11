# EnergyLens — Pricing Model v2 (2026-06-11)

_Authoritative pricing spec. Supersedes the flat-tier placeholders on `/pricing` and the
`STRIPE_PRICE_BASIC / MONITOR` setup. Derived from
[`unit-economics-pricing-review.md`](./unit-economics-pricing-review.md) (the COGS model) plus the
2026-06-11 founder pricing review. All amounts are **launch targets** — the authoritative price
always lives in Stripe; this document is the rationale + the SKU map._

---

## 0. The decision that anchors everything: who bears the Fabric capacity?

EnergyLens uses **app-owns-data / ISV embedding**. One Microsoft Fabric capacity (an F-SKU) lives
in **EnergyLens's** tenant (today `rg-energylens`, F4). Every customer's embedded Power BI report
runs on that **single shared capacity**; customers have **no** Fabric account and **no** Power BI
license. The consequences set the whole model:

- The Fabric bill goes **Microsoft → EnergyLens**. The customer never sees it.
- For EnergyLens it is a **COGS** line — a fixed/stepped cost recovered through subscriptions.
- Because the capacity is shared, it is **amortised across the customer base.** Below ~5 paying
  customers the €87–242/mo capacity floor runs underwater; past that, gross margin is **40–75%**
  (unit-economics doc, ① Decouple column).

**Why price scales with capacity (the founder's instinct, made concrete):** the more a customer
consumes — buildings drive data volume, IoT drives streaming + LLM — the more capacity and marginal
cost they create. The model expresses that through a unit the customer understands — **buildings +
modules** — instead of invisible F-SKUs.

**The ① Decouple dependency (load-bearing):** real-time IoT runs on cheap Azure Event Hubs + the
Container App hot store, **not** always-on Fabric. This is what keeps the *first* IoT customer at
**+39% margin** instead of **−90%**. Every price below is valid **only** under ① Decouple — putting
IoT real-time back onto always-on Fabric erases the margin. See
[`../architecture/iot-capacity-decision.md`](../architecture/iot-capacity-decision.md).

---

## 1. The model — four levers

| # | Lever | What it does | Maps to which cost |
|---|---|---|---|
| 1 | **Base subscription (tier)** | Unlocks a module set + N included buildings | Shared capacity floor + infra (~€65/mo) |
| 2 | **Per-building scale** | Each building beyond the included count adds a flat €/mo | Incremental Fabric data/capacity per building |
| 3 | **Modules (features)** | IoT real-time, battery/solar, copilot, compliance | IoT = Event Hubs €11 + LLM €15 ≈ €26/mo · others batch ≈ €0 |
| 4 | **Billing options** | Monthly **or** annual (−15%); white-glove onboarding (Enterprise only) | Annual front-loads the capacity floor |

Per-building (lever 2) is the capacity-scaling mechanism in customer-visible units — exactly how
enterprise BMS vendors (Siemens Desigo, Schneider EcoStruxure) price per building/point.

---

## 2. Tiers & launch prices

| Tier | Monthly | Annual (−15%) | Included buildings | +Extra building / mo | Modules |
|---|---|---|---|---|---|
| **Free / Pilot** | €0 | — | 1 | — | Tier-1 baseline only (Postgres, **no Fabric bridge**) |
| **Basic** | €99 | €1,010 / yr | 3 | +€35 | Deep analytics (Pages 1–7) |
| **Pro / Monitor** | €299 | €3,050 / yr | 5 | +€60 | + IoT real-time · battery & solar ROI · AI copilot · compliance hub |
| **Enterprise** | custom | custom | 10+ | negotiated | + SSO · SLA · white-glove onboarding · larger/dedicated capacity |
| **Residential** | €49 / building + €3 / unit | −15% | — | (per-building by nature) | Hausverwaltung: per-unit heating EUI, HKVO 70/30 split, UVI statements |

Annual math: Basic €99×12 = €1,188 → ×0.85 = **€1,010/yr**. Pro €299×12 = €3,588 → ×0.85 =
**€3,050/yr**. (Prices exclude VAT.)

---

## 3. Example total cost (illustrative)

| Customer | Tier | Buildings | Monthly total | Annual total | Margin note (unit-econ) |
|---|---|---:|---:|---:|---|
| Small office owner | Basic | 3 (incl.) | **€99** | €1,010 | Basic breaks even ~5 customers |
| Mid commercial + IoT | Pro | 5 (incl.) | **€299** | €3,050 | Pro @ 5 cust: +€207/cust (69%) |
| Growing portfolio + IoT | Pro | 8 (5 + 3×€60) | **€479** | €4,886 | per-building covers incremental capacity |
| Hausverwaltung | Residential | 4 bldg · 60 units | **€376** (4×€49 + 60×€3) | −15% if annual | volume → Residential Enterprise |

These show the intended shape: a one-building owner pays little; a portfolio with live IoT pays
proportionally more because it consumes proportionally more capacity.

---

## 4. Free-tier guardrail (margin protection — do not break)

**Free must stay Postgres-only** (Tier-1 baseline KPIs from CSV/bill upload, **no Fabric bridge**)
so its COGS ≈ €0. A Free user that triggered a Fabric bridge would burn shared capacity for €0
revenue — the one configuration that breaks the model (unit-econ finding #3). Free is the
**try-before-buy** surface that also removes any need for an upfront onboarding fee.

---

## 5. What we explicitly did NOT add (and why)

- **No minimum-commit contract.** Annual billing already front-loads 12 months of the capacity
  floor; a separate minimum-commit clause adds sales friction for no extra protection.
- **No upfront onboarding fee on self-serve tiers (Basic/Pro).** It would ask a customer to pay
  before seeing value. The Free/Pilot tier is the de-risking step instead. White-glove onboarding
  stays on **Enterprise**, where it is expected and the deal size carries it.

---

## 6. Implementation plan

### v1 — this session (additive, low-risk)
- **`/pricing` page** → reflect the five tiers, the monthly/annual choice, and the per-building
  line. Honest copy (no feature advertised that checkout can't fulfil).
- **Backend `billing.py`** → add **annual** price IDs + a `period` (monthly|annual) param to
  checkout; the webhook maps both monthly and annual price IDs to the same tier.
- **Stripe (operator)** → create the annual recurring prices; see `BILLING_SETUP.md`.

### v1.1 — next (deferred, needs care)
- **Per-building automation** as a Stripe subscription **quantity** line driven by the org's live
  building count, with proration on add/remove. v1 treats included-building counts as the
  self-serve envelope and handles larger portfolios at contract (founder-run, which early deals
  are anyway).
- **À la carte modules** on Basic (IoT / battery / compliance as individual add-on prices).

### Founder-side (Stripe dashboard, one-time)
Create products/prices and paste IDs into `web-app/backend/.env` — full steps in
[`../../web-app/BILLING_SETUP.md`](../../web-app/BILLING_SETUP.md).

---

_Sources: [`unit-economics-pricing-review.md`](./unit-economics-pricing-review.md) ·
[`iot-capacity-decision.md`](../architecture/iot-capacity-decision.md) ·
[Microsoft Fabric pricing](https://azure.microsoft.com/en-us/pricing/details/microsoft-fabric/) ·
[Power BI embedded capacity & SKUs](https://learn.microsoft.com/en-us/power-bi/developer/embedded/embedded-capacity)_
