# EnergyLens — Sample Deliverable Reports (Freelance)

**Purpose:** these PDFs show a prospect the *actual output* of the **ESG / EPBD
decision-support reporting** service (Service #2 in
[`../strategy/2026-06-18_freelance-service-map.md`](../strategy/2026-06-18_freelance-service-map.md)).
Attach to Upwork / Malt / freelancermap listings and to outreach emails so a
prospect can see "this is the report you'd get."

All reports are for one illustrative building (**B001 — a synthetic Berlin
office**), so they share consistent figures across the suite.

## The pack

| File | Report | Standard / use | Audience |
|---|---|---|---|
| `01_GHG-Inventory` | GHG Inventory | GHG Protocol (Scope 1/2/3, dual Scope 2) | Any — carbon baseline |
| `02_ESRS-E1-Climate` | ESRS E-1 Climate | CSRD/ESRS-aligned (E1-1…E1-9) | Corporate / CSRD |
| `03_CRREM-Stranding` | CRREM stranding | Transition-risk vs 1.5°C pathway | Real-estate / EPBD |
| `04_VSME-Basic` | VSME Basic Module | EFRAG Voluntary SME (B1–B11) | SME ESG |
| `05_GRESB-Readiness` | GRESB readiness | 28-indicator performance readiness | Funds / GRESB |
| `06_EnEfG-Audit` | EnEfG audit & plan | German Energy Efficiency Act §8/§9 | DE buildings |

## ⚠️ Honesty / framing — non-negotiable

- Always label as **"illustrative sample — synthetic data, not a real client."**
- Reports say **"ESRS-E1-aligned"**, **"CRREM-aligned (indicative pathways)"**,
  **"reporting support — not audited / assured / a CSRD filing"** — keep that
  language; never claim "certified", "CSRD-compliant", or "official CRREM".
- These are decision-support / screening deliverables, not certified
  Energieausweis / iSFP.

## ⚠️ REFRESH NEEDED — re-export before using

The current files were exported **2026-06-29, BEFORE the latest report fixes
went live**, so several are stale:

| File | Status | What changed (re-export to fix) |
|---|---|---|
| 01 GHG | ✅ current | — |
| 02 ESRS | ✅ current | — |
| 03 CRREM | ⚠️ stale | intensity now annual (~23, not 13.3), caption "trailing 12 months" |
| 04 VSME | ⚠️ stale | Scope 3 label corrected; operational (S1+2) card added |
| 05 GRESB | ⚠️ stale | operational (S1+2) card added |
| 06 EnEfG | ⚠️ stale | thresholds fixed (§9 > 2.77 GWh, §8 EnMS > 7.5 GWh); measure economics realistic (HVAC ~€11k / 4.3 yr, not €36k / 11 yr) |

**Before re-exporting, confirm both are deployed:**
1. **Frontend (Vercel):** the report-fix commits are live (`0150bda` … `fe420b2`).
2. **Backend (Railway/Azure):** the CRREM `co2_365`, dq-reclassify and
   partial-year fields are live. Quick check on B001: CRREM intensity shows
   **~22–23** (not 13.3) and the GHG/ESRS data-quality no longer says
   **"missing gas"**.

Then download each report from the app (Download PDF) and **replace the file of
the same name here**, keeping the `EnergyLens_Sample_0N_*` naming.

## Where this is referenced

- Outreach: [`../strategy/2026-06-18_outreach-kit.md`](../strategy/2026-06-18_outreach-kit.md)
- The curated 1-page overview (different artifact): `EnergyLens_Sample_Report.pdf`
  (built by `scripts/build_sample_report.py`) — use as the cover/teaser; this
  pack is the detailed follow-up.
