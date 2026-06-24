# Sample Client Report — Portfolio EPBD / Carbon Screening (narrative)

> **Status:** DRAFT v1 — the client-facing narrative for the freelance sample, grounded in the three
> Power BI exports (portfolio + Frankfurt Klinikum + Berlin). Numbers are from the current report;
> **savings figures are flagged indicative pending the "savings ≤ bill" cap fix** (see Internal QA).
> **Illustrative example on sample data** — not a real client. Pairs with the dashboard package.
> Companion to [`2026-06-18_listing-copy-and-report-narrative.md`](./2026-06-18_listing-copy-and-report-narrative.md).

---

## Executive summary

This screening assesses a **9-building mixed commercial portfolio** (office, retail, hotel,
healthcare, logistics, education) against EU compliance trajectories and rising carbon cost — using
only existing meter/bill and building data, **no new hardware**.

- **Three assets are already "stranded"** against the CRREM 1.5–2 °C decarbonisation pathway — their
  carbon intensity is above the line **today**, so their compliance and asset-value risk is live, not future.
- The **worst asset** (a Frankfurt healthcare facility) runs at **~2.6× its CRREM pathway** and
  carries a **~€79k/yr carbon levy** that rises as the German CO₂ price climbs toward ETS2.
- The **best asset** (a Berlin office, EPC B) is **on track** — confirming the method distinguishes
  genuine risk from well-managed stock, not a blanket alarm.
- A prioritised retrofit + operations plan is provided, ranked by abatement cost (€/tCO₂) and
  payback, with **BAFA/KfW subsidy** eligibility flagged where it reshapes the business case.
- All figures are **indicative / screening-grade** with assumptions stated — a decision-support
  basis, not a certified audit.

---

## 1. Portfolio screening — which buildings, in what order

Buildings ranked by CRREM status and carbon intensity vs pathway (kgCO₂/m²/yr):

| Asset (type) | EPC | Carbon intensity | CRREM pathway | Status |
|---|---|---:|---:|---|
| Healthcare, Frankfurt | C | 239 | 92 | **Stranded** (≈2.6×) |
| Retail, Istanbul | E | 151 | 44 | **Stranded** |
| Hotel, Vienna | C | 85 | 72 | **Stranded** |
| Logistics, Hamburg | A | 55 | 58 | On track |
| Education, Amsterdam | D | 50 | 55 | On track |
| Office, Berlin | B | 25 | 42 | On track |
| … (3 more) | | | | On track |

**Read:** capital should go to the three stranded assets first. The screening turns "we have a
portfolio and rising obligations" into a ranked, defensible **capital-allocation order**.

*(One atypical data-centre asset is excluded from this view — its energy-use intensity is an order
of magnitude above any habitable building and would distort the benchmark.)*

---

## 2. Stranded-asset drill-down — Frankfurt healthcare facility

- **Profile:** Healthcare, Frankfurt (DE), EPC **C**, EUI **~535 kWh/m²/yr**, **~1.5 GWh/yr** total.
- **Compliance risk:** carbon intensity **239 vs 92** kgCO₂/m²/yr CRREM pathway → **stranded now**,
  widening as the pathway tightens. **Carbon levy ≈ €79k/yr** today, rising with the CO₂ price.
- **Operational faults detected** (no extra sensors — from existing data): supply-air-temperature
  faults on two air-handling units, and **after-hours HVAC** running outside occupancy — classic,
  low-cost first wins.
- **Where the energy goes:** HVAC dominates (~48% of load) — so HVAC scheduling, controls and
  heat-recovery are the highest-leverage levers for this asset.
- **Recommended measures** (ranked; absolute € **indicative — being finalised**, see note):
  optimise building-management/controls, HVAC scheduling, peak-demand management, fabric/insulation
  where the heat-loss map is worst, and a mandatory energy audit (GEG/EnEfG obligation for a site
  this size). Several qualify for **BAFA/KfW** support, which materially shortens payback.

---

## 3. Well-managed contrast — Berlin office

- **Profile:** Office, Berlin (DE), EPC **B**, EUI **~74 kWh/m²/yr**.
- **Status:** carbon intensity **25 vs 42** pathway → **on track**; comfortably below stranding.
- **Why it's in the report:** it shows the screening *validates* good assets rather than crying wolf
  — the credibility check a portfolio owner needs. Action here is **monitoring + protect-the-rating**,
  not capital.

---

## 4. Recommended actions & financing

1. **Operations first (weeks, low/no capex):** fix the AHU faults and after-hours HVAC on the
   stranded healthcare asset — fastest payback, no procurement.
2. **Controls & demand (this year):** building-management optimisation, HVAC scheduling, peak-demand
   management across the stranded assets.
3. **Fabric & systems (capital, subsidy-backed):** insulation / envelope and HVAC plant where the
   heat-loss and CRREM gap are largest — **screen for BAFA/KfW** before committing; grants of 30%+
   routinely turn a "no" into a "yes".
4. **Track:** re-run the screening after each measure; watch the stranding year move out.

*Absolute annual-saving and payback figures are being finalised (see Internal QA) — measures are
ranked by abatement cost and payback; the order above is robust to the final numbers.*

---

## 5. Assumptions & method

Screening-grade, decision-support — **not** a certified Energieausweis / iSFP. Built from
meter/bill + building data; gaps filled by an estimation model with stated ranges. Carbon intensity
compared to CRREM 1.5–2 °C pathways; carbon cost on the German national CO₂ price trajectory toward
ETS2. ESRS-E1-aligned presentation (not a CSRD compliance statement). Every figure is indicative and
should be confirmed before capital commitment.

---

## Internal QA notes — NOT for client (for Mert + the report-finalisation thread)

- **Savings > bill (must fix before any client use):** Klinikum measure savings as exported sum to
  ~€1.36M (Optimise Bldg Mgmt €438,778 · Battery €329,084 · Peak €329,084 · HVAC €263,267) vs a
  ~€300k/yr total energy bill (1.5 GWh × ~€0.20). Cap savings ≤ bill (the known cap issue) — the
  finalisation thread owns this; narrative uses indicative/ranked framing meanwhile.
- **Data-centre outlier:** exclude from the portfolio benchmark view (EUI ~1,655 distorts charts).
- **Carbon levy rate — verify:** €79,268/yr vs ~Scope-1 2,615 tCO₂ ⇒ ~€30/t, below the 2026 German
  nEHS corridor (~€55–65/t). Confirm the levy rate/scope basis.
- **Page-1 "Goal: … (+/-100%)"** target labels read oddly — report-polish (other thread).
- **Building id note:** Berlin office = "Berliner Bürogebäude Alpha"; code (`demo_data.py`) calls it
  **B001**. If the live report shows it as 02, reconcile the id mapping (minor, non-blocking).
