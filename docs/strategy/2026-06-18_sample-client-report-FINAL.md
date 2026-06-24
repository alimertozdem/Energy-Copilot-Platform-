# Sample Client Report — Portfolio EPBD / Carbon Screening (FINAL narrative)

> **Status:** FINAL v1 — supersedes the draft
> [`2026-06-18_sample-client-report-narrative.md`](./2026-06-18_sample-client-report-narrative.md).
> Numbers from the **final** report export (3). **Correction vs the draft:** the earlier
> "savings > bill" flag was based on a misread bill (~€300k); the asset's actual energy spend is
> **~€1.5M/yr** (≈7 GWh), so no single measure exceeds the bill. Remaining caveats are milder (see
> Internal QA). **Illustrative example on sample data** — not a real client.

---

## Executive summary

A **9-building mixed commercial portfolio** assessed against EU compliance trajectories and rising
carbon cost — from existing meter/bill data, **no new hardware**.

- **Three assets are already "stranded"** vs the CRREM pathway — risk is live today, not future.
- The **worst asset** (Frankfurt healthcare facility) runs at **3.6× the peer energy benchmark** and
  **~2.5× its CRREM carbon pathway**, on **~€1.5M/yr** energy spend with a rising CO₂ levy.
- The **best asset** (Berlin office, EPC B) is **on track** — the method separates real risk from
  well-run stock.
- A prioritised operations + retrofit plan follows, ranked by payback and abatement cost, with
  **BAFA/KfW** flagged where it reshapes the case.
- Screening-grade, **ESRS-E1-aligned**, assumptions stated — decision support, not a certified audit.

---

## 1. Portfolio screening — order of priority

| Asset (type) | EPC | Carbon intensity | CRREM pathway | Status |
|---|---|---:|---:|---|
| Healthcare, Frankfurt | C | 232 | 92 | **Stranded** (~2.5×) |
| Retail, Istanbul | E | 151 | 44 | **Stranded** |
| Hotel, Vienna | C | 85 | 72 | **Stranded** |
| Logistics, Hamburg | A | 55 | 58 | On track |
| Education, Amsterdam | D | 50 | 55 | On track |
| Office, Berlin | B | 25 | 42 | On track |
| … (3 more) | | | | On track |

Capital goes to the three stranded assets first. *(An atypical data-centre asset is excluded — its
EUI is an order of magnitude above any habitable building and distorts the benchmark.)*

---

## 2. Stranded-asset drill-down — Frankfurt healthcare facility

- **Profile:** Healthcare, Frankfurt (DE), EPC **C**, EUI **~544 kWh/m²/yr — 363% of the peer
  benchmark**, **~7 GWh/yr**, **~€1.5M/yr** energy spend.
- **Compliance risk:** carbon intensity **232 vs 92** CRREM pathway → **stranded now**; a rising CO₂
  levy on top. An open **HIGH_CARBON_INTENSITY** flag.
- **Operational faults (from existing data, no new sensors):** supply-air-temperature faults on two
  AHUs + **after-hours HVAC** outside occupancy — low/no-capex first wins.
- **Energy split:** HVAC ~40% of load → controls, scheduling and heat-recovery are the top levers.
- **Recommended measures (ranked, not additive):** building-management/controls optimisation, HVAC
  scheduling, peak-demand management, battery, and a mandatory energy audit (GEG/EnEfG obligation at
  this size). Several qualify for **BAFA/KfW**. *Absolute savings & payback are indicative and under
  sanity-review (see Internal QA) — the **ranking and direction** are robust; the headline message is
  "this asset is non-compliant and over-spending, here is the fix order."*

---

## 3. Well-managed contrast — Berlin office

Office, Berlin (DE), EPC **B**, EUI ~74; carbon **25 vs 42** → **on track**. In the report to show
the screening *validates* good assets — credibility, not blanket alarm. Action = monitoring +
protect-the-rating.

---

## 4. Recommended actions & financing

1. **Operations first (weeks, ~no capex):** fix AHU faults + after-hours HVAC on the stranded asset.
2. **Controls & demand (this year):** BMS optimisation, HVAC scheduling, peak-demand management.
3. **Fabric & systems (capital, subsidy-backed):** envelope/plant where heat-loss + CRREM gap are
   largest — **screen BAFA/KfW first**; 30%+ grants change the answer.
4. **Track:** re-run after each measure; watch the stranding year move out.

---

## 5. Assumptions & method

Screening / decision-support — **not** a certified Energieausweis / iSFP. Built from meter/bill +
building data; gaps filled by an estimation model with stated ranges. Carbon vs CRREM 1.5–2 °C;
carbon cost on the German trajectory toward ETS2. ESRS-E1-aligned presentation (not a CSRD
statement). Confirm figures before capital commitment.

---

## Internal QA notes — NOT for client (for Mert + report-finalisation thread)

- **CORRECTION:** the draft's "savings > bill" was wrong — based on a misread ~€300k bill. Actual
  spend ≈ **€1.5M/yr** (≈7 GWh × ~€0.22). No single measure exceeds the bill.
- **Real remaining flags (milder):**
  1. **Sub-year paybacks implausible** — e.g. battery saving €329,084/yr at 0.3-yr payback ⇒ ~€99k
     capex; a battery that cheap can't save that much. Re-check the payback/CAPEX model.
  2. **Duplicate figure** — Battery and Peak-Demand both show **€329,084** → likely a formula
     artifact; verify they're distinct.
  3. **Don't sum measures** — €438,778 + €329,084 + €329,084 + €263,267 ≈ €1.36M (91% of the bill) is
     double-counting; measures overlap. Present ranked, not summed.
- **Carbon levy** dropped to **€23,346** (was €79,268) — on Scope-1 ~2,615 t that is ~€9/t, **below**
  the 2026 nEHS corridor (~€55–65/t). Verify the levy rate/scope basis.
- **Data-centre outlier** still excluded from the benchmark view.
- **Other exports:** only Klinikum was re-exported as final — if the **portfolio** and **Berlin**
  views were also revised, send them; otherwise their stable numbers (CRREM statuses, Berlin
  on-track) carry over unchanged.
