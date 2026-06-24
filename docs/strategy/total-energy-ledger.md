# EnergyLens — Total Final Energy Ledger (Path A)

> **Status:** DESIGN — pending energy-review sign-off (Mert, Energieberater). 2026-06-19.
> **Extends:** [`residential-retrofit-calculations.md`](./residential-retrofit-calculations.md) — reuses the
> approved German degree-day method (`fuel kWh = ΔU·A·Gt·24÷1000÷η`) for the commercial portfolio.
> **Principle:** every figure is indicative (range/estimate), states its assumptions, cites a basis.
> All numbers below are validated against the live Supabase mirror (`mv_*`, project `vuiqfaklvlbushkiapnp`) on 2026-06-19.

---

## 1. Decision & why

The embedded report shows physically impossible numbers (recommended annual savings of **102–212 %**
of the annual energy bill on 7/10 buildings; non-office EUI 2–3× sector benchmarks; heat-pump payback
**529 years**). Root-cause analysis traced **four separate symptoms to one cause**: the model keeps an
**electricity-only** cost and EUI ledger, while consumption and most savings measures include **heating**.

**Decision (Mert, 2026-06-19): Path A — fix the root.** Build a true *total final energy* ledger
(electricity + fuel) so heating savings are scored against the right denominator and EUI is benchmarked
on the standard total-energy basis. Path B (mechanical DAX/output caps) was rejected as lipstick.

## 2. Root cause (current state, verified)

| Symptom | Mechanism | Evidence |
|---|---|---|
| Savings > bill | 13 measures each credit % of the **electricity** bill; heating measures (CHP, heat recovery, BMS) save mostly on **gas** → inflated % | CHP = **75 %** of bill; sum uncapped |
| HP payback 529 yr | HP shifts load gas→electricity; on an electricity-only ledger it looks like a **loss** | `INSTALL_HEAT_PUMP` saving ≈ 0 %, payback 529 yr |
| EUI 2–3× benchmark | Generator folds gas heating into **electricity** via `heat_mult` (06_..., `generate_sample_data.py` L481), inconsistently | Healthcare elec-EUI 566 vs 90–200 band |
| "No gas data" | GHG engine derives gas as a **flat 25 % of electricity** (`09_ghg_scope_engine.py` L470), not physics | `gas_fuel_kwh = elec × 0.25 ÷ 0.85` |

**Implication:** there is no independent fuel series. A credible total-energy ledger requires (a) a real
degree-day **heating-demand model**, and (b) **de-inflating electricity** (removing the `heat_mult` fudge)
so heating is counted once, in the correct carrier.

## 3. Target — energy carriers

```
total_final_energy_kwh = electricity_clean_kwh        (meters: base + lighting + equipment + electric-HVAC)
                       + gas_fuel_kwh                  (gas-heated buildings: space heat + DHW ÷ η_boiler)
                       + district_heat_kwh             (district-heated buildings, e.g. B004)
                       + diesel_kwh                    (standby generators; minor)
```
- `electric-HVAC` = cooling (chiller/AC) + **electric heating** (heat pump / resistive), the only heating
  that legitimately appears on the electricity meter.
- Gas/district/diesel = separate carriers, each with its own tariff and emission factor.

## 4. Heating-demand model (degree-day, screening-grade)

Reuses the residential method, generalised to any envelope:

```
H_spec  = U_eff · C_env  +  0.34 · (n50 ÷ 20) · h            [W/m²K per conditioned m²]
q_heat  = H_spec · Gt · 24 ÷ 1000                            [kWh/m²·yr, space-heat demand]
space_heat_kwh = q_heat · conditioned_area_m2
```

| Symbol | Meaning | Value / source | Assumption tag |
|---|---|---|---|
| `U_eff` | area-weighted envelope U | `0.40·U_wall + 0.25·U_win + 0.20·U_roof + 0.15·U_floor` | [Tahmin] element-area weights |
| `C_env` | envelope-to-floor (form factor) | **1.5** (commercial mid-rise; residential worked ex. ≈ 0.94) | [Tahmin] tune per geometry |
| `n50÷20` | n50 blower-door → natural infiltration | `air_tightness_ach` field reads as **n50** (B008 = 8.5); /20 standard | [Muhtemel] confirm field semantics |
| `h` | room height | **3.2 m** | [Tahmin] |
| `Gt` | Gradtagzahl (20/15 basis) | `annual_HDD(base15) × 1.5` — converts the in-model HDD to German 20/15 | [Tahmin] φ=1.5, calibrate |
| `η_boiler` | gas seasonal efficiency | **0.90** (condensing; matches residential doc) | [Kesin] DEFRA/residential |
| DHW | hot-water add (kWh/m²·yr) | Hotel 35 · Healthcare 30 · Lab 25 · Retail 12 · Educ 10 · Office 8 · Logistics 5 · DC 2 | [Tahmin] type table |

**Carrier assignment:** gas-heated → `(q_heat+DHW)÷η_boiler` as `gas_fuel_kwh`; heat-pump → `(q_heat+DHW)÷COP`
as `electric_heat_kwh` (stays on electricity meter); district → `(q_heat+DHW)` as `district_heat_kwh`.

## 5. Clean electricity (de-inflation)

The generator currently multiplies electric demand by `heat_eff = 1+(15−T)·0.015·heat_mult` for **all**
buildings, including gas-heated ones — physically wrong (a gas boiler does not raise the electric meter).
Fix at source (regenerate, approved): apply the heating temperature response **only** to electric-HVAC
(heat pump / AC / chiller). For gas/district buildings, heating leaves the electricity series entirely and
reappears in the fuel carrier. Net effect: gas-heated buildings' electricity EUI drops into the electricity
band; their heating shows in gas; total = both.

## 6. New gold columns, cost & tariffs

`gold_kpi_daily` (and monthly) gain, alongside the **retained** electricity columns:

| Column | Definition |
|---|---|
| `electric_heat_kwh`, `gas_fuel_kwh`, `district_heat_kwh`, `diesel_kwh` | per carrier (model) |
| `total_final_energy_kwh` | sum of carriers |
| `total_eui_kwh_m2` | `total_final_energy_kwh ÷ gross_floor_area` (annualised) |
| `gas_cost_eur`, `district_cost_eur` | carrier_kwh × tariff |
| `total_energy_cost_eur` | `estimated_cost_eur (elec) + gas_cost + district_cost + diesel_cost` |

**Tariffs (provisional, new `ref_fuel_tariffs`):** gas DE 0.11 / AT 0.10 / NL 0.12 / TR 0.05 €/kWh;
district ≈ 0.12 €/kWh; diesel ≈ 0.18 €/kWh-equiv. [Muhtemel — verify before Logic step.]
Electricity unchanged (`ref_electricity_tariffs`).

## 7. Total-energy EUI benchmarks (provisional — to verify)

Gauge gains a **total-energy** band per type (keeps electricity band as secondary). Provisional, **pending
verification against CIBSE TM46 / DIN V 18599** at the benchmark step:

| Type | Total-energy EUI band (kWh/m²·yr) |
|---|---|
| Office 200–280 · Hotel 300–400 · Healthcare 400–550 · Education 150–230 · Retail 200–350 · Logistics 50–120 · Lab 400–700 · Data_Center 1500–2500 |

A modern all-electric heat-pump office legitimately sits **below** the gas-era "typical" (e.g. B001 ≈ 87) —
the gauge should read that as *excellent*, not broken.

## 8. Recommendation engine (B1) under total-energy

Once `total_energy_cost_eur` exists:
1. **Cost base → total.** CHP/heat-recovery/BMS/HP %-of-cost recompute against the full bill (CHP 75 %→~22 %;
   HP payback becomes finite as avoided-gas is credited).
2. **Per-measure realistic bands** (% of total energy cost): LED 2–5 · HVAC sched 5–15 · BMS 5–10 ·
   insulation 10–20 · peak 3–8 · sub-metering ≈ 0 (enabler, no direct kWh) · CHP ≤ 22 · battery 3–8 · PFC ≤ 4.
3. **Aggregate cap:** Σ measures ≤ **35 %** of total annual cost (deep-retrofit ceiling); scale proportionally
   if exceeded. Recompute `payback_years = net_capex ÷ annual_saving`.

## 9. Validation prototype (live `mv_`, 2026-06-19)

Heating model run against real envelope + HDD. `heat_carrier` = delivered fuel/electric heat after η/COP.
`total_indic` = current(inflated) electricity + gas (illustrative; electricity not yet de-inflated):

| Bldg | Type | gas | hp | elec_now | q_heat | heat_carrier | total_indic | reads as |
|---|---|:--:|:--:|--:|--:|--:|--:|---|
| B009 | Data_Center | – | – | 1870 | 40 | 42 | 1870 | ✓ in band |
| B005 | Healthcare | ✓ | – | 566 | 68 | 109 | 675 | elec needs de-inflation |
| B002 | Retail | ✓ | – | 294 | 127 | 154 | 448 | elec needs de-inflation |
| B004 | Hotel | – | – | 348 | 60 | 95 | 348 | **district** heat, not gas → 3rd carrier |
| B008 | Office | ✓ | – | 77 | **219** | 252 | 329 | ✓ G-rated now reads high (was absurdly low at 77) |
| B006 | Education | – | – | 207 | 98 | 108 | 207 | VRF electric heat (heavily inflated) |
| B003 | Logistics | ✓ | – | 164 | 34 | 43 | 207 | elec needs de-inflation |
| B010 | Lab | – | ✓ | 143 | 47 | 15 | 143 | HP heat already electric |
| B001 | Office | – | ✓ | 87 | 41 | 13 | 87 | ✓ excellent modern office |
| B007 | Office | – | ✓ | 58 | 28 | 7 | 58 | ✓ net-plus |

**Reads:** the heating model is physically coherent (B008 worst, modern buildings lowest). The validation
also proves de-inflation is mandatory — for gas buildings `elec_now` is heat-inflated, so `total_indic`
double-counts until §5 is applied. B004 confirms a **district-heat** carrier is needed (its heating is
currently faked into electricity and shows as no gas).

## 10. Notebook change plan & sequence

| # | Notebook | Change | Runs in |
|---|---|---|---|
| 1 | `sample-data/generate_sample_data.py` + `generators/generate_new_buildings_data.py` | de-inflate electricity (§5): `heat_eff` only on electric-HVAC; emit clean electricity | local (regenerate) |
| 2 | `notebooks/gold/03b_total_energy_ledger.py` (**new**) | degree-day heating model (§4) → carrier kWh + total + total_cost + total_eui; merge into `gold_kpi_daily` | Fabric |
| 3 | `notebooks/gold/09_ghg_scope_engine.py` | replace 25 % proxy with real `gas_fuel_kwh` from §4 | Fabric |
| 4 | `ref_fuel_tariffs` + benchmark/gauge (semantic model) | gas/district tariffs; total-energy bands; verify vs TM46/DIN | Fabric + TE |
| 5 | `notebooks/recommendation/06_recommendation_engine.py` (+ cap stage) | cost base → total; per-measure bands + 35 % cap (B1) | Fabric |
| 6 | `notebooks/anomaly-detection/anomaly_detection.py` | B3: sustained solar underperformance, ~1–3/bldg/month | Fabric |

After each: re-mirror gold → `mv_*`, SQL-verify ranges before advancing.

## 11. Open calibration knobs (energy-review — Mert)

1. `C_env` form factor (1.5) and room height (3.2 m) — per-type or per-building?
2. `φ` HDD-base conversion (1.5) — or recompute HDD at 20/15 in `03`?
3. `n50 ÷ 20` — confirm `air_tightness_ach` is n50 (else divisor changes materially; B008 sensitive).
4. DHW/process table — Healthcare/Lab process loads may warrant more than the DHW add.
5. Electricity bands for intensive types (Healthcare elec realistically 150–300, above the 90–200 brief band).
