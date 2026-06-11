# EnergyLens — Residential Retrofit: Calculation Method & Worked Example

> **Status:** APPROVED (energy-domain gate, Mert — 2026-06-11). Backs growth-strategy §4.3.
> **Principle:** every figure is **indicative** (range/estimate), states its assumptions, and
> cites a source — computed the way German energy advisors (*Energieberater*) actually compute it.
> This document is the **single source** the in-app "how is this calculated?" tooltips cite.

## 1. Representative building (stated assumption)

| Property | Value |
|---|---|
| Units / storeys / heated area | 35 · 6 · **2,450 m²** (~70 m²/unit) |
| Vintage / heating / EPC | ~1970s, unrenovated · central **gas** · EPC ~E/F |
| Baseline space-heating | **150 kWh/m²/yr** (retrofit candidate; cf. Heizspiegel 2025 MFH gas avg **114**) |
| Annual heating energy | 2,450 × 150 = **367,500 kWh/yr** (~368 MWh) |
| Gas price | **0.11 €/kWh** (2026 working price) → **~€40,400/yr** |
| CO₂ | 0.201 kg/kWh (gas) → **73.9 t/yr**; @ nEHS €55/t = **€4,065/yr** (→ ~€11k/yr @ €149/t, 2030) |

## 2. Method — how each number is produced

- **Operational** (balancing, curve, controls): empirical savings % from field studies (ITG Dresden
  meta-study 7–11%; co2online up to 15%).
- **Fabric** (insulation, windows): simplified transmission method —
  `fuel kWh/yr = ΔU × A × Gt × 24 ÷ 1000 ÷ η`
  where ΔU = U_before − U_after [W/m²K], A = element area [m²], **Gt = Gradtagzahl 3,500 Kd**
  (German reference 20/15), η = condensing-gas seasonal efficiency **0.90**.
- **Heat pump**: fuel switch — `electricity kWh = heat demand ÷ JAZ`; cost vs gas; CO₂ via grid factor.
- **€ saving** = kWh × gas price. **CO₂ saving** = kWh × 0.201. **Payback** = net CapEx (after
  subsidy) ÷ (annual € energy + CO₂ cost @ €55/t).

### U-value assumptions (unrenovated 1970s → GEG-compliant)
| Element | U before | U after | Area (this building) |
|---|---:|---:|---:|
| Façade (opaque) | 1.2 | 0.22 | 1,180 m² |
| Top-floor ceiling | 0.8 | 0.20 | 410 m² |
| Basement ceiling | 1.0 | 0.30 | 410 m² |
| Windows | 2.7 | 0.95 | 310 m² |

## 3. Worked example (per measure)

| Tier · Measure | Saving basis | kWh/yr | €/yr | t CO₂/yr | Net CapEx (after subsidy) | Payback |
|---|---|---:|---:|---:|---:|---:|
| **T0** Hydraulic balancing + heating curve | ~10% heating (ITG 7–11%) | ~37,000 | ~€4,050 | ~7.4 | ~€16k (−20%) | **~3–4 yr** |
| **T1** Basement-ceiling insulation | ΔU 0.70 · 410 m² | ~27,000 | ~€2,970 | ~5.4 | ~€16k (−20%) | **~5 yr** |
| **T1** Top-floor-ceiling insulation | ΔU 0.60 · 410 m² | ~23,000 | ~€2,530 | ~4.6 | ~€13k (−20%) | **~5–6 yr** |
| **T2** Façade (WDVS) | ΔU 0.98 · 1,180 m² | ~108,000 | ~€11,900 | ~21.7 | ~€151k (−20%) | **~11–13 yr** |
| **T2** Windows (triple glazing) | ΔU 1.75 · 310 m² | ~51,000 | ~€5,600 | ~10.3 | ~€110k (−20%) | **~17–19 yr** |
| **T2** Air-source heat pump | fuel switch · JAZ 3.0 | elec ~97,000 | ~€11,200\* | ~29.6 | ~€165k (−≈53%) | **~13 yr\*** |

\* Heat pump is a **fuel switch, not a % saving**: € figure uses today's gas/elec + a heat-pump
tariff (0.25 €/kWh). Its real lever is **CO₂ + regulation** — once ETS2 lifts the buildings-carbon
price toward ~€149/t (2030), payback shortens sharply. Electricity grid 363 g/kWh (2024, falling).

## 4. Honesty notes (must be surfaced to the customer)

1. **Savings are not additive** — each measure lowers the consumption the next one acts on. A full
   package realistically reaches **~50–65% heating reduction**, not the arithmetic sum of the rows.
2. **Subsidy transforms payback** — envelope measures −20% (BAFA BEG + iSFP bonus); the heat pump is
   the biggest lever (KfW 30–70%). Always show gross **and** net-of-subsidy.
3. **The cost of doing nothing rises** — 73.9 t/yr × €55 = €4,065/yr carbon cost today, ~€11k/yr at
   €149/t. Every payback shortens as the carbon price climbs.
4. **All figures are screening-grade** — a building-specific audit (consumption history, real areas,
   U-values, hydraulics) replaces these ranges before any commitment.

## 5. Subsidies (Germany, 2026)

- **Envelope** (insulation, windows): BAFA *BEG Einzelmaßnahme* ~15% + 5% iSFP bonus = **up to 20%**.
- **Heating / heat pump**: **KfW** (program 458, not BAFA since 2024): 30% base + 20% speed bonus +
  5% efficiency + 30% income, **capped at 70%**; eligible cost per dwelling **€30k (1st WE) / €15k
  (2nd–6th) / €8k (7th+)**, max €21k subsidy per WE.

## 6. Sources

- [Heizspiegel 2025 — co2online / Deutscher Mieterbund](https://mieterbund.de/aktuelles/meldungen/heizspiegel-fuer-deutschland-2025/)
- [German gas price 2025–26 (~11 ct/kWh)](https://checkalle.de/gas-prices-2026/)
- [Hydraulic balancing 7–11% — co2online / ITG Dresden](https://www.co2online.de/energie-sparen/heizenergie-sparen/hydraulischer-abgleich/)
- [Heat-pump subsidy 2026 (up to 70%, €30k/WE) — Finanztip / KfW](https://www.finanztip.de/waermepumpe/foerderung/)
- [CO₂ grid factor 363 g/kWh 2024 — Umweltbundesamt](https://www.umweltbundesamt.de/themen/co2-emissionen-pro-kilowattstunde-strom-2024)
- [Insulation costs 2025–26 (WDVS/roof/basement)](https://gruenes.haus/haus-daemmen-daemmung-kosten/)
- [Heat-pump Altbau cost & JAZ — 42watt](https://42watt.de/magazin/warmepumpe-im-altbau)
- [Window replacement cost 2025 — 42watt](https://42watt.de/magazin/was-kostet-ein-fenster-mit-einbau)
- [Gradtagzahl / heating degree days — Energie-Lexikon](https://www.energie-lexikon.info/heizgradtage.html)
