# Stated Assumptions — Energy Copilot Platform

All assumptions are explicitly stated here. Any change to these assumptions
must be reflected in the relevant KPI formula or simulation logic.

---

## Data Assumptions

| Assumption | Value | Rationale |
|---|---|---|
| Minimum data resolution (Tier 1) | Hourly | Sufficient for daily KPI calculation |
| Minimum data resolution (Tier 2-3) | 15-minute | Required for battery dispatch and HVAC optimization |
| Weather data source | OpenWeatherMap (global) / DWD (Germany) / MGM (Turkey) | Free API, sufficient accuracy for building energy |
| HDD base temperature | 15°C | EN ISO 15927-6 standard |
| CDD base temperature | 22°C | Common European standard |
| Missing data interpolation limit | Maximum 2 consecutive hours | Beyond this, marked as MISSING, not interpolated |

---

## Grid Emission Factors

| Country | Factor | Year | Source |
|---|---|---|---|
| Germany | 0.380 kg CO₂/kWh | 2024 | Umweltbundesamt (UBA) |
| Turkey | 0.442 kg CO₂/kWh | 2024 | TEİAŞ |

*These values should be reviewed and updated annually.*

---

## Solar PV Assumptions

| Assumption | Value | Notes |
|---|---|---|
| Default Performance Ratio (PR) | 0.80 | Industry standard for well-maintained systems |
| Required roof area per kWp | 7 m² | Approximate for standard panels (400W, 1.7m²) |
| Default roof orientation | South (180°) | If not specified by user |
| Default roof tilt | 30° (Germany) / 25° (Turkey) | Optimal annual yield |
| Discount rate for NPV | 5% | Conservative financial assumption |
| NPV calculation period | 10 years | Standard energy project horizon |
| Germany installed cost | 1,000–1,400 €/kWp | 2024 market range, system installed |
| Turkey installed cost | 600–900 USD/kWp | 2024 market range, system installed |
| PV system lifetime | 25 years | Standard panel warranty |

---

## Battery Storage Assumptions

| Assumption | Value | Notes |
|---|---|---|
| Recommended technology | LFP (LiFePO₄) | Best balance of safety, cost, lifetime for commercial |
| Installed cost | 600–900 €/kWh | 2024 European market (system installed) |
| Round-trip efficiency | 0.92 | Typical LFP at room temperature |
| Guaranteed cycle life | 4,000 cycles | LFP standard warranty condition |
| System lifetime | 15 years | Conservative estimate |
| Warranty period | 10 years | Market standard |
| Min SoC (operating) | 15% | Protects battery from deep discharge |
| Max SoC (operating) | 90% | Protects battery from overcharge stress |
| Optimal SoC band | 20%–80% | Extended lifetime recommendation |
| EU ETS carbon price | 60–80 €/ton CO₂ | 2024 range for carbon credit valuation |

---

## Heat Pump Assumptions

| Assumption | Value | Notes |
|---|---|---|
| Default gas boiler efficiency | 0.90 | Modern condensing boiler |
| COP performance threshold | 80% of rated COP | Below this triggers maintenance alert |
| Critical COP threshold | 60% of rated COP | Below this triggers HIGH severity alert |
| Temperature band for COP comparison | ±3°C of design temperature | Fair comparison baseline |

---

## HVAC Optimization Assumptions

| Assumption | Value | Notes |
|---|---|---|
| Heating setpoint target | 20°C | EN 16798-1 standard |
| Cooling setpoint target | 24°C | Common European standard |
| Setpoint tolerance | ±1°C | Before recommendation triggers |
| Energy per degree rule | ~6% per °C | Approximate for commercial HVAC |
| Preheat time factor | 6 min per °C difference | Simplified; varies by building mass |
| Winter setback (unoccupied) | 16°C | Frost protection minimum |
| Summer setback (unoccupied) | 28°C | Energy conservation |

---

## Insulation Assumptions

| Assumption | Value | Notes |
|---|---|---|
| Wall insulation cost (Germany) | 80–120 €/m² | 100mm EPS external wall insulation |
| Roof insulation cost (Germany) | 60–100 €/m² | Mineral wool, accessible roof |
| Triple glazing windows (Germany) | 400–700 €/m² | Including installation |
| GEG min wall U-value | 0.24 W/m²K | Regulatory minimum |
| GEG min roof U-value | 0.20 W/m²K | Regulatory minimum |
| GEG min window U-value | 1.30 W/m²K | Regulatory minimum |

---

## Financial Assumptions

| Assumption | Value | Notes |
|---|---|---|
| Discount rate (NPV) | 5% | Conservative real rate |
| Analysis period | 10 years | Standard for energy projects |
| Germany electricity price | ~0.22 €/kWh | 2024 commercial tariff (medium consumer) |
| Turkey electricity price | ~0.08 €/kWh | 2024 commercial tariff (approximate) |
| Germany gas price | ~0.07 €/kWh | 2024 commercial tariff |
| Germany feed-in tariff (PV) | ~0.08 €/kWh | EEG 2024 small commercial systems |
| EU ETS carbon price | 60–80 €/ton CO₂ | 2024 range |

*All prices are approximate 2024 market values and must be updatable per tenant.*

---

## Regulatory Assumptions

| Assumption | Notes |
|---|---|
| Regulations are static (Phase 1) | Manually reviewed and updated annually |
| EnEfG threshold | 250+ employees — ISO 50001 or energy audit required |
| GEG renewable requirement | 65% renewable for new/replacement heating systems from 2024 |
| CSRD applicability | Companies with >500 employees (Phase 1 threshold) |
| EPBD nZEB target | Near-zero energy for new buildings — primary energy target varies by country |

---

## Benchmarking Assumptions

*Office buildings (primary benchmark set for Phase 1):*

| Class | EUI kWh/m²/year | Source |
|---|---|---|
| Excellent | < 80 | ASHRAE 90.1 / EU Building Stock Observatory |
| Good | 80–130 | |
| Average | 130–200 | |
| Poor | > 200 | |

*Separate benchmark sets for Retail, Hotel, and Logistics to be added in Phase 1 data.*

---

## What This Platform Does NOT Assume

- That sensor data is always accurate (data quality flags handle this)
- That energy prices are fixed (tariff table is per-tenant and updatable)
- That all buildings have all technologies (technology profile gates all relevant modules)
- That roof characteristics are always known (PV simulations note when estimates are used)
- That regulatory compliance is a binary pass/fail (gap analysis provides gradations)
