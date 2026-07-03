# EnergyLens — Platform Technical Documentation

**How every number in the platform is produced: methods, formulas, assumptions, and sources.**
Version 1.0 · 2026-07-03 · Audited against the live codebase and the live Supabase mirror on this date.
Audience: pilot customers' technical reviewers, Energieberater partners, and future engineering hires.

> **Honesty statement.** The current portfolio (B001–B010, plus residential B011) is a **synthetic
> demonstration dataset** generated to realistic engineering patterns. Every calculation documented
> here runs identically on real data; figures on synthetic buildings are labelled `sample` /
> `estimated` / `data_basis` throughout the product. No real-building performance is claimed.

> **🇹🇷 Özet.** Bu doküman platformdaki her sayının nasıl üretildiğini anlatır: formüller,
> varsayımlar, kaynak dosyalar. Mevcut portföy sentetik demo verisidir ve ürün bunu her yerde
> açıkça etiketler. Her bölümün sonunda bu şekilde kısa Türkçe özet bulunur.

---

## Contents

1. [Platform architecture](#1-platform-architecture)
2. [Platform-wide conventions & reference factors](#2-platform-wide-conventions--reference-factors)
3. [Calculation engines](#3-calculation-engines)
   - 3.1 Fabric data layer (notebooks) · 3.2 Backend service engines · 3.3 Frontend calculation libraries
4. [Web application — module by module](#4-web-application--module-by-module)
5. [Power BI report (10 pages)](#5-power-bi-report)
6. [Access control & security](#6-access-control--security)
7. [Data provenance & the honesty layer](#7-data-provenance--the-honesty-layer)
8. [Audit 2026-07-03 — fixes applied & pilot punch list](#8-audit-2026-07-03)

---

## 1. Platform architecture

EnergyLens is a two-tier product built on one calculation core:

```
                        ┌──────────────────────────────────────────────┐
                        │            MICROSOFT FABRIC (paid tier)      │
  Bills / CSV / PDF ──▶ │  Bronze (raw) → Silver (clean) → Gold (KPI)  │
  IoT (BACnet/Modbus/   │  Spark notebooks 01…30 + Delta Lake          │──▶ Power BI
  MQTT/REST edge agent) │  DirectLake semantic model (329 measures)    │    (embedded)
                        └───────────────┬──────────────────────────────┘
                                        │ notebook 50 (materialize)
                                        ▼
                        ┌──────────────────────────────────────────────┐
                        │        SUPABASE POSTGRES (free tier core)    │
   Web uploads ───────▶ │  mv_* mirror tables + app schema (auth,      │
   (Tier-1 path)        │  buildings, consumption, billing, alerts)    │
                        └───────────────┬──────────────────────────────┘
                                        ▼
                        ┌──────────────────────────────────────────────┐
                        │  FastAPI backend (Azure Container Apps)      │
                        │  gold_read: Postgres-first, Fabric fallback  │
                        │  Next.js frontend (Vercel) + PBI embed       │
                        └──────────────────────────────────────────────┘
```

**Medallion layers (Fabric).** `bronze_*` holds raw, protocol-native ingestion; `silver_*` holds
cleaned, typed entities (`silver_building_master` is the single building dimension); `gold_*` holds
business-ready KPIs (`gold_kpi_daily`, `gold_recommendations`, `gold_ghg_scope`,
`gold_energy_ledger`, `gold_iot_fdd`, `gold_battery_simulation`, residential gold tables, etc.).
Ingestion, transformation and business logic are deliberately separated (one notebook = one
responsibility) so any figure can be traced to one notebook.

**The Postgres mirror.** The production backend (Azure) cannot reach the Fabric SQL endpoint
(port-1433 egress), and a paused Fabric capacity should never take the customer app down. Notebook
`50_materialize` therefore mirrors the gold tables into Supabase as `mv_*` tables.
`app/integrations/gold_read.py` lets every service keep writing T-SQL: it rewrites
`[dbo].[gold_x]` → `mv_x`, `[date]` → `("date"::date)`, `ISNULL`→`COALESCE`, `TOP (n)`→`LIMIT`,
bit-flag `= 0/1` → `= false/true`, and falls back to the original T-SQL against Fabric if Postgres
fails. **One query text, two engines.**

**Two data-entry tiers.** Tier 1: upload-only (CSV / PDF bills) — KPIs computed **in Postgres**
(§3.2.1), no Fabric required; this is the hardware-free wedge. Tier 2/3: edge agent (5 live
protocols) or manual device config streaming into `bronze_iot_readings`, batch-rolled into gold
(§3.1.10, §3.2.9) — Fabric EventStream (Phase B) is built but dormant at €0 until the first paying
IoT customer.

> **🇹🇷 Özet.** Mimari: Fabric (Bronze→Silver→Gold, Spark + DirectLake PBI) hesap çekirdeği;
> notebook 50 gold tabloları Supabase'e `mv_*` olarak aynalar; backend `gold_read` ile önce
> Postgres, olmazsa Fabric okur. Tier-1 (fatura yükleme) hiç Fabric'e dokunmadan Postgres'te KPI
> üretir — donanımsız wedge budur. IoT tarafı edge-agent → bronze → gold batch; streaming hazır ama
> ilk ödeyen müşteriye kadar kapalı (€0).

---

## 2. Platform-wide conventions & reference factors

These rules apply to **every** module; individual engines reference them.

**R1 — Year-indexed, location-based grid emission factors.** CO₂ from electricity always uses the
factor of the building's country **and the data's year** (`ref_grid_emission_factors` in Fabric;
verbatim mirror in `backend/app/services/reference_factors.py`): DE 2022 0.433 / 2023 0.386 /
2024-25 0.363 (UBA); TR 0.442 (TEİAŞ); AT 0.158, NL 0.290, FR 0.052, PL 0.660, EU avg 0.230
kg CO₂/kWh (IEA/EEA). A flat factor would blur "the grid got cleaner" with "the building improved" —
auditors reject that for CSRD/CRREM. Each factor carries `confidence` + `source` into the UI.

**R2 — Electricity tariffs.** Non-household Eurostat blended averages (2025): DE 0.226, AT 0.190,
NL 0.205, TR 0.085 (EPDK), EU 0.190 €/kWh. Used only where an actual metered cost is absent; the
basis is always labelled (`actual` vs `estimated`).

**R3 — The 40-year payback rule.** A simple payback ≥ 40 years exceeds any equipment service life,
so it is **not a real financial payback** — the measure is compliance- or CO₂-driven. Enforced in
four places (defence in depth): notebook 06b nulls it in gold; backend `finance_model.simple_payback`
and `heating_assessment._plausible_pb` return `None`; `reportKit.fmtPayback` and the /actions table
render "—" / "Operational" for anything ≥ 40.

**R4 — Ranges, not fake precision.** Anything forward-looking (retrofit savings, subsidies, carbon
prices, value uplift) is emitted as a **low–high range** with the driver stated (e.g. CapEx ±30%
screening band, demand ±10% measured / ±25% estimated).

**R5 — Basis labels.** Every figure carries its provenance: `measured` / `estimated` /
`sample`·`simulated`·`telemetry` (`data_basis`), `actual` vs `estimated` cost, EPC `anchored` flag,
partial-year (`reporting_months < 12`) warnings on all annual reports.

**R6 — No invented engineering.** Heating physics uses the degree-day method an Energieberater
uses; savings percentages come from cited literature bands (ITG Dresden 7–11% operational, ISO 50001
5–15% BMS, IEA setback benchmarks); anything assumed is marked `[Tahmin]`/"assumption" in code and
tooltip.

> **🇹🇷 Özet.** Tüm platformda ortak kurallar: yıl-endeksli ülke bazlı emisyon faktörleri (R1),
> Eurostat tarifeleri (R2), 40-yıl payback tavanı dört katmanda uygulanır (R3), ileriye dönük her
> sayı aralık olarak verilir (R4), her rakam kaynağını/etiketini taşır (R5), uydurma mühendislik
> yok — literatür bantları ve Gradtag yöntemi (R6).

---

## 3. Calculation engines

### 3.1 Fabric data layer (notebooks)

#### 3.1.1 `03_gold_kpi_engine` — daily KPIs
Produces `gold_kpi_daily` (building × day): `total_consumption_kwh`, `estimated_cost_eur`,
`co2_emissions_kg`, `hdd_day`/`cdd_day`, peak/base load, and the solar block. Key logic:

- **Solar performance ratio (energy basis, IEC 61724).**
  `PR_day = generated_kwh / (kWp × ref_yield)`, where `ref_yield = Σ(hourly avg irradiance W/m²)/1000`
  (peak-sun-hours for that day). Clamped at **`PR_MAX_PLAUSIBLE = 0.95`** (real arrays peak ~0.90;
  higher = sensor/data artefact); days with `ref_yield < 0.5 kWh/m²` (overcast) → **NULL, not a fake
  PR**. Verified live: `MAX(avg_solar_pr) = 0.95`, zero violations.
- Battery round-trip efficiency ≈ discharged/charged (LFP ~0.90–0.95).
- Self-consumption / self-sufficiency per the standard definitions (§KPI 5 of
  `docs/business-logic/kpi-formulas.md`).

#### 3.1.2 `03b_total_energy_ledger` — total final energy (Path A root fix)
The single most important correctness decision in the data layer. The synthetic seed metered only
electricity, so heating-heavy measures compared against an **electricity-only** bill produced
physically impossible results ("savings 102–212% of the bill", heat-pump payback 529 yr, EUI 2–3×
benchmarks). `gold_energy_ledger` (building × year × month) rebuilds the **true total-final-energy
bill**:

```
U_eff   = 0.40·U_wall + 0.25·U_window + 0.20·U_roof + 0.15·U_floor      [W/m²K]
H_spec  = U_eff · C_ENV + 0.34 · (n50 / 20) · room_height               [W/m²K]   C_ENV = 1.5
q_heat  = H_spec · (annual_HDD_base15 · PHI_HDD) · 24 / 1000            [kWh/m²·yr]  PHI_HDD = 1.5
+ DHW by type (Hotel 35 … Office 8 kWh/m²·yr)
```
Space heat is distributed across months by HDD share; DHW evenly (/12). Carrier conversion:
gas = heat / 0.90 (condensing boiler), district = heat delivered, heat-pump/VRF = heat / COP —
**already inside the electricity meter, so NOT re-added** (informational column only).
`total_final_energy = electricity + gas_fuel + district_heat`; costs use `ref_fuel_tariffs`
(fallback DE gas 0.11 €/kWh, district 0.12). PHI_HDD (base-15 HDD → German 20/15 Gradtagzahl) and
C_ENV are the two review knobs, parameterised in CELL 0 and product-owner approved (2026-06-25).

#### 3.1.3 `06_recommendation_engine` + `06b_recommendation_calibration` — the measures catalog
**Stage 1 (06)** generates ~14 measure types per building (LED, HVAC scheduling, BMS, insulation,
CHP, heat pump, solar install, battery, sub-metering, deep retrofit, audit…) with savings, CapEx,
grants, CO₂, payback, NPV (`NPV ≈ saving × 12 − net_capex`, ~20 yr @ 5%), and the
**§9c economic-viability gate** (approved 2026-06-22): an *optional* measure with NPV ≤ 0 is demoted
to `INFORMATIONAL` and can never rank MEDIUM/HIGH; compliance-mandated measures (heat pump,
insulation, deep retrofit, audit) are exempt (they are regulation-driven, not ROI-driven).

**Stage 2 (06b)** re-bases everything on the **total** energy bill (ledger §3.1.2) and enforces
physics: per-measure ceilings as % of total annual cost (LED 5%, scheduling 15%, BMS 10%,
insulation 20%, CHP 22%, PV 25%, deep retrofit 35%…); sub-metering = enabler → saving 0; heat pump
recomputed as a **fuel switch** (avoided gas € − extra electricity € at COP 3.2), and a heat pump
that does **not** cut CO₂ (carbon-heavy grid, e.g. TR) has its saving nulled — it must not be sold
as a decarbonisation win; an aggregate ceiling Σ(measures) ≤ 35% × total cost, **scaled by EPC band**
(A 12% → E/F/G 35% headroom — an A-rated building cannot save a third of its bill); payback ≥ 40 yr
→ NULL (R3); CO₂ scaled proportionally with the € change.

**Run order is load-bearing: 03b → 06 → 06b → 50 (materialize).** 06 overwrites 06b's calibration
whenever it re-runs, so 06b must always run last (this recurred — see §8).

*(Uncommitted work-in-progress on 06, found in this audit: BMS-aware CapEx — re-commissioning
€2.5/m² + €6k base when a BMS exists vs €28/m² new install; kWh/m² saving ceilings for BMS (20)
and scheduling (15) so energy-dense types aren't over-credited; and a multi-year → 12-month
annualisation fix for the consumption base. Compiles clean; needs commit + Fabric run — §8.)*

#### 3.1.4 `09_ghg_scope_engine` — GHG Protocol scopes
`gold_ghg_scope` (building × month): Scope 1 (gas 0.201 kg/kWh HHV-basis BEHG factor, diesel,
refrigerant); Scope 2 **location** (grid factor R1) and **market** (supplier contract factor if on
file, else **AIB residual mix** — per GHG Protocol Scope 2 Guidance the no-instrument fallback is
residual mix, *not* the location average); Scope 3 **category-structured estimate**
(`disclosure_grade = false`): Cat 1 embodied (area × ~700 kgCO₂e/m² / 60 yr amortisation / 12),
plus (live model) Cat 3 fuel-energy, Cat 5 waste, Cat 6 travel, Cat 7 commuting, Cat 13 leased.
**Headline convention (2026-06-29 decision):** operational carbon = **S1 + S2** everywhere;
full Scope-3-inclusive totals appear only in the GHG/ESRS reports, separately and labelled
*estimated*. ⚠️ The live notebook computes 6 Scope-3 categories; the repo copy still has the older
cat1+13 version — mirror pending (§8).

#### 3.1.5 `05_compliance_checker` — regulatory flags
`gold_compliance_results`: GEG §71 heating renewable-compliance, GEG Anlage 7 U-value component
checks (wall ≤ 0.24, roof ≤ 0.20 flat, window ≤ 1.30 W/m²K), EnEfG thresholds, EPBD/MEPS triage
(worst bands: G→2030, F→2033), BEP-TR certificate checks, plus scores per framework.

#### 3.1.6 `10_crrem_pathway_loader` — decarbonisation pathways
Loads *illustrative* 1.5 °C intensity pathways per asset type (2025→2050). **Not the licensed CRREM
dataset** (that requires a CRREM licence agreement — module is built to swap the official points in
one place). UI labels the curves indicative.

#### 3.1.7 `11_hvac_analytics_engine` — HVAC & envelope gold
`gold_hvac_analytics` (280 rows live): rated-vs-actual COP (G1 recalibration), envelope insulation
score anchored so the worst-stock building scores 0 (G2), CO₂ annualisation fix (R1 16.5k→7.1k),
transmission-loss heat badge (G3/R2). Fixed 2026-06-21 during Page-7 finalisation.

#### 3.1.8 `11b/11c IoT processing + FDD` — fault detection & €-quantified alerts
`gold_iot_fdd` (38 rows live): rules over sensor streams (HVAC temp deviation, CO₂ >1500 ppm,
power >120% baseline, PV underperformance…). Cost logic (stated assumption, always shown "Est."):
`cost € = energy_impact_kwh × grid_price` where the energy impact uses the CLAUDE.md waste bands
(2–5 kW per °C HVAC deviation, 1–3 kW extra ventilation on CO₂ spikes, actual excess on power
spikes; DE 0.20 / TR 0.14 €/kWh). Priority = severity weight (High 1.0 / Med 0.6 / Low 0.3) blended
with cost normalised at €50. Verified live 1:1 against the app (portfolio 4 High / €81.14 on
2026-06-01).

#### 3.1.9 `16_gold_battery_simulation_v3_honest` — battery scenarios (Page 9)
The honest rebuild (2026-06-22) after the "anchor × factor" defect: every scenario row carries
`data_basis` ∈ **Measured** (real dispatch history — only B001 self-consumption €3.7k, B003 peak
€69.9k, B005 backup €20.6k exist), **Modeled** (engine-derived; model reproduced measured B003
within ~4%), or **Prospect** (building has no battery — pure what-if). No caps anywhere in the
data (R3 handles display); arbitrage corrected from a 3.3-yr cumulative to annual (€61k). Known
open point: peak/TOU IRRs 40–64% are optimistic-but-not-fabricated (measured B003 = 63%);
a dispatch-spread de-rate pass is a deliberate post-pilot item.

#### 3.1.10 `30_residential_gold` + residential pipeline
Per-unit KPIs (`gold_residential_unit_kpi`): heating+DHW EUI per m² Wohnfläche, climate-adjustment
factor, EPC band per unit, anonymised building benchmark **pre-aggregated into each unit's own row**
(privacy §6). `gold_residential_common_split`: HKVO §7 common-area allocation = **70% consumption /
30% area**. `gold_residential_uvi_monthly`: the monthly consumption statements (UVI) the EED/HKVO
requires. Retrofit math for residential lives in the approved doc
`docs/strategy/residential-retrofit-calculations.md` (ΔU × A × Gt × 24/1000 ÷ η — same family as
§3.2.4).

#### 3.1.11 Forecast & occupancy (Pages 4–5 support)
`07_consumption_forecast` (day-ahead consumption) and `08_occupancy_prediction`
(`gold_occupancy_profile`; OPTIMIZE wrapped non-critical — the post-reset failure noted in earlier
sessions is fixed in the repo copy). Anomaly engine (`anomaly_detection.py`) implements rules A1–A7
(consumption spike ×1.5 vs 30-day same-hour baseline with weather guard, base-load >35% of peak,
COP degradation <0.8×rated with outdoor-temp guard, PR <0.70 with irradiance guard, battery SoC
conditions, weekend overuse >60% of weekday, climate-adjusted EUI +15% YoY) → `gold_anomaly_log`.

> **🇹🇷 Özet.** Veri katmanının kalbi: 03 günlük KPI (PR=enerji-bazlı, 0.95 tavan), 03b toplam
> enerji defteri (Gradtag yöntemi; elektrik-only yanılgısını kökten çözer), 06+06b öneri motoru
> (fizik tavanları, HP=yakıt değişimi, NPV kapısı, EPC-ölçekli %35 toplam tavan; sıra 03b→06→06b
> kritik), 09 GHG (S1+S2 manşet, S3 ayrı ve "estimated"; canlı 6 kategori), 11c IoT arıza+€ etiketi,
> 16 dürüst batarya (Measured/Modeled/Prospect), 30 residential (HKVO 70/30, UVI). CRREM eğrileri
> lisans nedeniyle "illustrative" etiketli.

### 3.2 Backend service engines (FastAPI, Postgres-native)

#### 3.2.1 Baseline KPI engine (`baseline_kpi.py`) — the Tier-1 upload path
Turns uploaded monthly consumption into real KPIs with zero Fabric dependency. ≥12 months →
**trailing-12** window (true annual run-rate); <12 months → monthly-average × 12, flagged
`is_annualized`. EUI = annual kWh / floor area (not weather-corrected — stated). CO₂ per R1;
cost = actual uploaded costs when every window month has one, else kWh × tariff (R2), flagged.
30-day tile figures = annual × 30/365.25 so Fabric and upload paths share semantics.

#### 3.2.2 Provisional baseline estimate (`baseline_estimate.py`)
Before any bill exists: archetype total-final-energy intensity **ranges** by type (Office 120–220,
Retail 180–320, Hotel 220–380, Healthcare 250–450, Logistics 40–110, Residential 100–240
kWh/m²·yr) × area → kWh/cost/CO₂ ranges with real factors (R1/R2). Datacenter deliberately
unmodeled (IT load dominates — no number is better than a wrong one). Superseded the moment
consumption exists.

#### 3.2.3 Estimation engine (`services/estimation/`) — evidence stacking
The free data-estimation core (approved BMAD 2026-06-17): L0 archetype prior → L1 vintage
repositioning within the band → L2 climate scaling of the **heating fraction only**
(`EUI' = EUI × (1−heat_frac + heat_frac × HDD/HDD_ref)`) → L5 German Energieausweis class anchor
(GEG Anlage 10 bands, blended by **inverse-variance**) → L4 partial-bill anchor (1–11 months
annualised by heating-shape month weights; 12+ months = `actual`, confidence high). Area fallback
chain: user → gold → footprint × storeys × 0.8 (`very_low` confidence). Cost/CO₂ use an A8
fuel-split (gas/oil/district heating share at fuel price+EF, remainder electricity) — electricity
proxy only when the heating fuel is unknown. Every output = {low, point, high} + confidence +
method string (e.g. `archetype · vintage · hdd · epc · bill_6m`).

#### 3.2.4 Heating & envelope assessment (`heating_assessment.py`) — the Heating page
Works pre-Fabric (the wedge). Demand: measured total × type heating share (notebook-11 table:
Office .35 … Education .48; Residential .60 stated) or archetype EUI × area, converted to metered
fuel (HP → /JAZ 3.0, else /η 0.90). Fabric measures (roof/wall/window to GEG targets):
**GROSS** transmission saving `ΔU × A_element × 3500 Kd × 24/1000` (the approved residential doc,
kept exactly and reported as `saving_kwh_gross`), then **delivered** = GROSS × gain-utilisation
factor (Office 0.65 … Residential 0.85 — internal/solar gains already cover part of the load), then
capped by the addressable share (68% of thermal demand — ventilation/DHW are not envelope-fixable).
Element areas from archetype ratios (facade 0.48 / roof 0.17 / windows 0.13 of floor area);
"before" U-values default to 1970s stock when unknown (flagged). Heat pump = **fuel switch**
(gas € − elec@JAZ €), not a % saving. The **package** sequences measures cheapest-payback-first on
the *remaining* load (non-additive), clamps at 72% total reduction, and reports CapEx ±30% /
demand-band payback ranges plus a 2030-carbon-price sensitivity. Also derives: CO2KostAufG exposure,
EPC class now/after on the German Endenergie scale **anchored to the registered certificate** when
on file, EPBD MEPS milestone (G/H→2030, F→2033), GEG §71 status, CRREM intensity before/after.

#### 3.2.5 CO2KostAufG allocation (`co2_cost_allocation.py`)
The landlord/tenant split of the heating-fuel CO₂ price. Residential: the **statutory 10-step
model** on kg CO₂ per m² of Wohnfläche (0/100 below 12 kg → 95/5 above 52 kg); non-residential:
flat 50/50 (the NWG step model is not yet in force). Heating-fuel CO₂ only (gas 0.201 kg/kWh BEHG;
electricity and F-gases are outside the levy). Prices: 2026 = €65/t (nEHS corridor cap), ETS2 2028
= €80/t **indicative**. Residential per-unit breakdown = area-pro-rata (labelled an estimate — the
statute splits the tenant part by measured consumption).

#### 3.2.6 Financing engine (`finance_model.py` + `financing.py`)
Pure, deterministic, "support not advice": KfW 458 (30→70%, €30k/unit cap) and BAFA BEG EM
(15→20% with iSFP, €30k/€60k per unit) with residential unit-count estimation (declared, else
area/75 m²); carbon-price **scenarios** (conservative/base/high) anchored 2026 €60 → 2030
80/120/180 → 2050 150/250/350, linearly interpolated, BEHG corridor until ETS2 2028; NPV with 4%
real discount + energy-inflation scenarios (1/3/5%) + carbon value per year; discounted payback;
EPC "green premium" as an indicative 1.0–2.5% value uplift per band, capped 15%.

#### 3.2.7 MACC (`abatement.py`)
Marginal abatement cost per measure over the visible portfolio:
`MAC €/t = (net_capex / lifetime − annual_saving) / annual_tCO₂` — undiscounted by design (stated);
lifetimes from an engineering service-life table (envelope 30, PV 25, HVAC 18, battery/LED 12,
controls 10, operational 5; default 15). Negative MAC = self-financing. Cheapest-first cumulative
CO₂ builds the curve.

#### 3.2.8 ESRS/VSME/GRESB metrics (`esrs_metrics.py` + report routes)
Reads `mv_ghg_scope`/`mv_kpi_daily` for the latest **complete** year (≥12 months; falls back to
latest partial with an explicit `reporting_months` field → PartialYearNotice in every report).
Scope 2 dual-reported (location + market). All-electric buildings flagged `missing_gas` are
reclassified `complete` (no gas to report ≠ missing data). Energy in MWh, GHG intensity per m²,
renewable share from solar self-consumption. Labelled **"ESRS-E1-aligned support"** — never
"CSRD-compliant" (legal-language decision).

#### 3.2.9 Solar detail + telemetry rollup (`solar_detail.py`, `solar_telemetry_rollup.py`)
/solar is **real-first, sample-fallback per building**: buildings with telemetry in the 90-day
window serve from `gold_solar_daily` (loader: generation = counter-delta or power-trapezoid
integration with a 6-h gap guard; IEC PR NULL below 0.05 kWh/m² irradiation and clamped ≤ 1.1 —
deliberately looser than the synthetic gold's 0.95 because a real POA sensor can read PR > 1.0 on
cold clear days; self-consumption = ∫min(PV, load)dt only when a load meter exists —
inverter-only sites get `self_consumption_available = false`, never an estimate, with a coverage %
stating how much of generation is metered for the split). Portfolio PR is **generation-weighted**
(Σ PR×gen / Σ gen; sample PR>1.1 building-days excluded as low-sun artefacts). Specific yield is
annualised **only** over ≥350-day windows. `data_basis` = telemetry / simulated / sample / mixed.

#### 3.2.10 Advisor & anomaly guides (frontend-adjacent)
`buildingAdvisor.ts` (deterministic Layer-1 "AI advisor"): type-aware indicative EUI bands
(healthcare 250–450 … logistics 40–120, office 100–200), over-band €-gap estimate = gap × area ×
country price × 40–80% capture (explicit assumption string), EPC/MEPS insights, heating-system
insights, asset gap-analysis (PV/battery/IoT), all ranked action > watch > info > good, max 6.
Datacenters get a PUE note instead of EUI. The LLM copilot (§4) is wired separately
(`services/copilot/` orchestrator + tools + Anthropic provider with mock fallback).

> **🇹🇷 Özet.** Backend motorları: yükleme yolunda gerçek KPI (trailing-12 / yıllıklaştırılmış
> bayraklı), fatura yokken arketip aralığı, kanıt-istifleyen tahmin motoru (arketip→yaş→iklim→EPC→
> kısmi fatura), ısıtma değerlendirmesi (GROSS iletim × kazanım faktörü, %68 tavan, HP=yakıt
> değişimi, paket sıralaması), CO2KostAufG 10 basamak, KfW/BAFA + karbon senaryolu NPV, MACC,
> ESRS (tam-yıl seçimi + kısmi-yıl uyarısı), solar gerçek-önce (üretim-ağırlıklı PR, tahminsiz
> self-consumption), deterministik danışman. Hepsi aralık + varsayım etiketi taşır.

### 3.3 Frontend calculation libraries
`lib/crrem.ts` — CRREM-style stranding: annual operational intensity (prefers backend trailing-12M
CO₂, falls back to annualised 30-day with caveat) vs illustrative 1.5 °C pathway; first crossing
year = stranding year; milestones 2030/2033/2040/2050. `lib/compliance.ts`, `taxonomy.ts` (EU
Taxonomy screening incl. EPC-validity), `flexibility.ts` (IoT-gated flexibility readiness),
`anomalyGuide.ts` (per-rule explanations), `glossary.ts` (single-source term registry powering
InfoTip tooltips — the planned method/assumptions extension is designed in
`docs/architecture/calc-transparency-plan.md`). `reportKit.tsx` centralises print/PDF report
formatting incl. `fmtPayback` (R3) and `PartialYearNotice`.

> **🇹🇷 Özet.** FE hesap kütüphaneleri: CRREM stranding (trailing-12M CO₂ tercihli), taxonomy/
> flexibility/anomali rehberleri, tek-kaynak glossary ve rapor kiti (payback guard + kısmi-yıl
> uyarısı).

---

## 4. Web application — module by module

All pages are English-UI, dark-theme Next.js (App Router), served from Vercel; every data call goes
through the FastAPI backend with org-scoped visibility (§6). "Source" names the service that owns
the numbers (documented in §3).

| Page | What it shows | Source of the numbers |
|---|---|---|
| `/dashboard` | Org home: KPI tiles, advisor highlights, onboarding nudges | portfolio_metrics + baseline_kpi + advisor |
| `/portfolio` (+ report) | 30-day KPI tiles w/ deltas, per-building table (EUI trailing-12M coverage-aware — fixed in this audit, type-aware EUI bands), solar row | portfolio_metrics §3.2.x, euiBandFor |
| `/buildings` (+ import) | CRUD, bulk CSV import (expected-columns panel), baseline strip | buildings router, baseline_estimate/baseline_kpi |
| `/buildings/[id]` | Building cockpit: KPIs, advisor panel, heating assessment, residential rollup, reports hub | heating_assessment, advisor, residential_manager_metrics |
| `/buildings/[id]/report` + per-building reports (EPC, CO₂, GEG, residential) | Print/PDF documents | reportKit + the §3.2 engines |
| `/actions` (+ report) | Recommendation catalog w/ status workflow, savings/payback/priority | gold_recommendations (06/06b) via actions_data |
| `/alerts` (+ report) | Grouped anomaly queue (distinct open types), severity, est. € | gold_anomaly_log + anomalyGuide |
| `/hvac` | Heating & envelope decision page (measures, package, GEG, EPC path) | heating_assessment |
| `/solar` | Portfolio solar: generation, gen-weighted PR, self-consumption (coverage-aware), yield; building slicer; DataBasisBadge | solar_detail §3.2.9 |
| `/compliance` (+ 8 report routes) | MEPS radar, CRREM stranding, ESRS-E1, VSME, GHG inventory, GRESB, EnEfG, Taxonomy, Flexibility; scorecard hero | esrs_metrics, compliance libs, geg_conformity, co2_cost_allocation |
| `/decarbonisation` (+ report) | MACC curve + measure table | abatement §3.2.7 |
| `/financing` (+ report) | Subsidy matcher, carbon-scenario NPV, green premium | finance_model/financing §3.2.6 |
| `/copilot` | LLM copilot over the user's own buildings (tool-calling) | copilot orchestrator + Anthropic provider |
| `/connections` | Device/agent onboarding (Tier 2/3), test telemetry, VerifyPanel, freshness | ingest router, device_templates |
| `/onboarding` | Self-serve wizard + Data Score | building_readiness / bridge_readiness |
| `/residential`, `/residence` (+ enter, report) | Manager rollup vs resident self-view (UVI, unit KPI, common split) | residential(_manager)_metrics §3.1.10 |
| `/demo` | Public no-login sample tour (own fallback dataset, clearly sample) | demo_data |
| `/pilot`, `/partners`, `/pricing`, `/tour`, `/glossary` | Lead capture → /admin queue; installer marketplace Phase 0; plans; guided tour; term registry | pilot/installer/billing routers |
| `/admin` | Lead queue, org/user admin, audit views | admin router |
| `/settings`, `/login`+auth pages | Org/profile/billing settings; email+OAuth auth, invite, password reset (code-complete; activation pending §8) | settings/auth routers |

**Report generation.** 20 print-grade documents (portfolio, building, actions, alerts, compliance
family, financing, residential family…) share `reportKit` (A4 landscape, brand header, footer,
partial-year notice). Server-side PDF download runs headless Chromium (18 routes live since
fe420b2); every report re-reads its backend endpoint — reports and app can never disagree.

**Billing.** Stripe wiring is code-complete (Free/Basic €99/Monitor €299/Enterprise; Residential
€49/building + €3/unit); activation is founder-run ops, not code.

> **🇹🇷 Özet.** ~30 sayfalık uygulamanın her modülü tek bir backend servisinden beslenir (tablo).
> 20 rapor tek reportKit'ten çıkar ve aynı endpoint'i okuduğu için app ile rapor asla çelişmez;
> PDF'ler sunucu tarafında headless Chromium ile üretilir. Stripe kodu hazır, aktivasyon operasyonel.

---

## 5. Power BI report

**Model.** `EnergyCopilotModel` — DirectLake on the gold Delta tables, 329 measures (live dump
regenerated into `semantic-model/measures_dump.txt`), star-ish schema: every fact keyed to
`silver_building_master[building_id]` and a marked `Date` table (relationship dump alongside).
RLS: DirectLake + fixed-identity (service principal) + CUSTOMDATA-driven roles — the model's data
source uses the SP (SSO off) so embedded customers are isolated (verified: `cp2_embed_rls_live`).
Report-level measures exist that model dumps cannot see (documented gotcha) — the definitive visual
truth is the PBIX, page-finalisation state below.

**Pages (all 10 finalised decision-grade, 2026-06-18 → 06-22 sessions):**

| # | Page | Core content & the measures that matter |
|---|---|---|
| 1 | Portfolio Overview | 5 KPI cards (totals = plain Card+SUM — the AVG-card bug class is closed; EUI card = AVG correctly), portfolio scorecard | 
| 2 | Energy Consumption | consumption trends, time-grain switches, solar overlay |
| 3 | Solar Production | generation, self-consumption, PR (energy-basis from §3.1.1) |
| 4 | Savings & Forecast | recommendation savings (post-06b calibrated), consumption forecast |
| 5 | Occupancy | occupancy heat-map (Day Name), headcount decision support |
| 6 | Sustainability | GHG by scope (real gas Scope 1 — the €166k phantom levy fix), CO₂ trend annualised, compliance scorecard |
| 7 | HVAC | COP rated-vs-actual, envelope insulation score, CO₂ annualised, heat-loss badge |
| 8 | IoT Monitoring | live power/comfort/CO₂ cards, sensor matrix, FDD alert table with Est. € (gold_iot_fdd single-source; C4 card verified €81.14 ↔ app 1:1); freshness = MAX(event_date)+REMOVEFILTERS (DirectLake-safe) |
| 9 | Battery | honest simulation (Measured/Modeled/Prospect via `data_basis`), C2 = installed-battery payback, building_name on rows |
| 10 | Solar Ops | PR distribution (gen-weighted, conditional colour, 0–100 axis), PV underperformance €-loss (target PR 0.80: `lost = gen × (0.80/PR − 1)` at the building's own effective tariff) |

**Open cosmetics (Desktop-only, listed in §8):** Page 6 D2 levy Goal/D4 blank + CO₂ visual rebind;
Page 8 matrix rounding, slicer removal, "Active Zones" rename; Page 9 `data_basis` badge on the
table + B001 umlaut re-run. **Model hygiene:** legacy capped measures (`C2/V3/Scenario Payback ≤25`)
and a flat `Avg Solar PR Pct` remain in the model alongside the corrected report-side versions —
schedule a Tabular-Editor cleanup pass so nothing ever rebinds to a stale measure (§8).

**Embed.** User-owns-data embed in the app (page GUID navigation, FitToPage, persistentFilters,
embed-token caching + circuit breaker). Known performance ceiling is **report design** (186 visuals
/ 20-22 per page / 45 slicers), not storage mode — the paused-capacity warmup and visual-count
reduction are the levers (runbook `docs/runbooks/pbi-perf-diagnosis-2026-06-24.md`).

> **🇹🇷 Özet.** 329 ölçülü DirectLake modeli + 10 sayfanın tamamı karar-kalitesinde kapandı; RLS
> fixed-identity SP + CUSTOMDATA ile müşteri izolasyonu canlı doğrulandı. Kalan işler kozmetik
> (Sayfa 6/8/9) + model temizliği (eski cap'li ölçüler). Performansın sınırı depolama modu değil
> görsel yoğunluğu.

---

## 6. Access control & security

Three confirmed layers: **RLS (data)** — Power BI CUSTOMDATA roles + org-scoped SQL (`building_id
IN (visible set)`) in every backend query; customer data never crosses org boundaries even on the
sample org. **App navigation (module)** — Next.js gates pages on subscription + connected inventory
(no IoT → Page 8 locked; no battery → Page 9 locked). **Subscription (commercial)** — plan gates in
Postgres/FastAPI. Resident privacy is **by construction**: the resident view only ever queries the
resident's own `unit_id`s; the building benchmark is pre-aggregated into each unit's own gold row,
so no cross-unit read exists at any layer. Auth: JWT + OAuth (Microsoft/Google), org invites,
self-service password reset (Resend) code-complete pending activation. Agent ingestion uses scoped
agent tokens.

> **🇹🇷 Özet.** Üç katman: RLS (veri) + uygulama navigasyonu (modül) + abonelik (ticari). Resident
> gizliliği sorgu tasarımıyla garanti (benchmark kendi satırında). Auth: JWT/OAuth + davet +
> şifre sıfırlama (aktivasyon bekliyor).

---

## 7. Data provenance & the honesty layer

The platform's differentiator is that it **states what it knows and how well**: `data_basis`
(telemetry/simulated/sample/mixed) on solar and battery, `Measured/Modeled/Prospect` on battery
scenarios, `measured/estimated` demand bases with band widths (±10% vs ±25%), `actual/estimated`
cost bases, confidence grades on every estimate (`high…very_low`), grid-factor provenance strings,
partial-year notices on all annual reports, "indicative/illustrative" labels on benchmark bands and
CRREM curves, `disclosure_grade=false` on Scope 3, and Datacenter-EUI refusal. The remaining gap to
close with the first pilot: replacing the synthetic seed with a real building's bills — the entire
§3 pipeline is the same; only the labels flip.

> **🇹🇷 Özet.** Her sayı kaynağını, güvenini ve bandını taşır; sentetik veri her yerde etiketli.
> İlk pilot binayla değişecek tek şey etiketler — hesap zinciri aynı.

---

## 8. Audit 2026-07-03

### 8.1 Verified in this audit
Backend engines (§3.2) formula-checked against approved docs; Fabric notebooks (§3.1) checked for
the approved knobs (PHI_HDD 1.5, C_ENV 1.5, PR clamp 0.95, 06b caps, §9c gate, FDD € logic);
live Supabase mirror checked read-only (PR max 0.95 ✓, FDD 38 rows & €81.14 chain ✓, GHG 6-category
live schema ✓, rec aggregate ≤35% ✓); live site up (landing, correct EU 2023/1542 reference);
PBI model dump = fresh live export, 329 measures; report/app single-source confirmed for FDD costs.

### 8.2 Fixed in this audit (applied to the working tree — commit + push pending)
1. **/actions payback display**: operational-measure threshold 50 → **40 yr** (aligns R3; live data
   briefly showed "41.8 yr"). `components/actions/ActionsTable.tsx`
2. **Advisor text**: no longer quotes a payback ≥ 40 yr in the "biggest opportunity" line.
   `lib/insights/buildingAdvisor.ts`
3. **Portfolio EUI** (⚠ energy-logic change — review): building-row EUI now = trailing-12-month
   energy annualised over actual day coverage (`kwh_365 × 365.25/days ÷ area`), 30-day fallback for
   new buildings. Removes the seasonal bias of annualising one month; consistent with co2_365 and
   the EUI benchmark bands. `services/portfolio_metrics.py`
4. **Stale sensitivity note** in heating assessment: hardcoded "~149 €/t" → dynamic base-2030
   carbon price (currently €120/t) + accurate wording. `services/heating_assessment.py`
5. **03b sanity print** now groups by year (a multi-year SUM previously read ~3× annual EUI).
6. **crrem.ts stale docstring** updated (code already used trailing-12M CO₂).
7. Repo hygiene: tracked `AppChrome.tsx.bak` removed from the index; `*.bak` gitignored.
8. **Vercel production build repaired** (broken since 1bbfbe2, 06-29): `PartialYearNotice` was
   imported from `@/lib/crrem` instead of `./reportKit` in the ESRS-E1 and VSME report documents;
   fixed, `tsc --noEmit` clean, deploy `ea0a825` Ready in Production.
9. Ingest/SCADA pass (post-doc audit): telemetry rollup's stale "same cap as 03" comment corrected —
   measured-telemetry PR ceiling 1.1 (POA basis) is deliberate vs the synthetic gold's 0.95.

### 8.3 Punch list — to close before saying "waiting for the first pilot building"
| # | Item | Owner / where |
|---|---|---|
| P1 | **Fabric re-run in order: 03b → 06 → 06b → 50-materialize → PBI Service refresh.** Live `mv_recommendations` is currently post-06/pre-06b (B007 battery 115.2 yr, B003 41.8 yr visible to SQL; app now guards, but the data must be re-calibrated). Commit the uncommitted 06 improvements (BMS-aware CapEx + annualisation + ceilings — compiles clean) first. | Mert (Fabric) |
| P2 | Re-materialize scope: `mv_building_master` has 10 rows vs 14 in `mv_kpi_daily` (B012–B015 orphans); `mv_sync_log` only logs 3 tables. Extend the live 50-materialize TABLES dict + logging. | Mert (Fabric) |
| P3 | Mirror live notebooks into the repo: live 09 GHG (6-category Scope 3) and live 50-materialize (TABLES-dict version) differ from the repo copies; nb16 is mirrored but sits in `_deferred/` with a stale README. | Mert paste → repo |
| P4 | Password-reset activation: Resend account + DNS + `FRONTEND_BASE_URL` + `alembic upgrade head` (head c1d2e3f4a5b6) + deploy. Add rate-limiting follow-up. | Mert (ops) |
| P5 | PBI Desktop cosmetics: Page 6 D2/D4 + CO₂ rebind; Page 8 ×3; Page 9 data_basis badge + umlaut. Then a Tabular-Editor cleanup of stale measures (capped C2/V3/Scenario Payback, flat Avg Solar PR Pct) after confirming page bindings. | Mert (Desktop) |
| P6 | Push this audit's fixes + build check (`npm run build` locally = Vercel parity), then deploy backend (portfolio EUI change) . | Mert (git/ops) |
| P7 | Approve/adjust the two flagged energy-logic changes: portfolio trailing-12M EUI (8.2-3) and the 06 WIP parameters (BMS_SAVING_CEILING 20, HVAC ceiling 15 kWh/m²·yr, RCx €2.5/m²+€6k, install €28/m²). | Mert (energy review) |
| P8 | Post-pilot (explicitly deferred, not blockers): battery dispatch-spread de-rate pass; official CRREM licence swap-in; calc-transparency tooltips build-out; Stripe/billing activation; Fly.io/Azure move decision for Fabric SQL egress. | backlog |

**Bottom line.** With P1–P2 (one Fabric session) and P4–P6 (one ops session) done, the platform is
accurately describable as **"code-complete and audited — waiting for the first pilot building."**

> **🇹🇷 Özet.** Bu denetimde 7 düzeltme uygulandı (en önemlisi: /actions 40-yıl guard'ı ve portföy
> EUI'sinin trailing-12-ay'a geçmesi — ikisi de onayına işaretli). Kalan 6 kalem senin elinde: bir
> Fabric oturumu (03b→06→06b→materialize sırası + mirror), bir ops oturumu (password-reset, push,
> PBI kozmetik). Bunlar bitince "app bitti, ilk pilot binayı bekliyor" cümlesi teknik olarak doğru.

---

*Cross-references: `docs/business-logic/kpi-formulas.md` (KPI/anomaly rule catalog),
`docs/strategy/total-energy-ledger.md` (Path A design), `docs/strategy/residential-retrofit-calculations.md`
(approved retrofit math), `docs/architecture/*` (estimation engine, access model, IoT/FDD, SCADA),
`docs/report-documentation/EnergyLens_Report_Technical_Documentation.docx` (per-visual PBI detail),
`docs/runbooks/*` (operational runbooks).*
