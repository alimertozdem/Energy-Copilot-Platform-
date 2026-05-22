# KPI Formulas & Business Logic — Energy Copilot Platform

## KPI 1: Energy Use Intensity (EUI)

**Definition:** Measures how efficiently a building uses energy per unit of conditioned floor area.

```
EUI = Total Annual Consumption (kWh) / Conditioned Area (m²)
Unit: kWh/m²/year

Climate-Adjusted EUI:
EUI_adj = EUI × (Reference HDD+CDD / Actual HDD+CDD)
```

**Why climate adjustment?** A building in Berlin naturally consumes more heating energy than one in Istanbul. Adjustment allows fair comparison across climates and years.

**HDD/CDD Base temperatures:**
- HDD base: 15°C (heating required below this)
- CDD base: 22°C (cooling required above this)

**Benchmark ranges (Office buildings):**

| Performance | EUI (kWh/m²/year) | Label |
|---|---|---|
| Excellent | < 80 | LEED Platinum equivalent |
| Good | 80–130 | Above sector average |
| Average | 130–200 | Typical commercial building |
| Poor | > 200 | Urgent action required |

*Benchmarks vary by building type. Separate sets for Hotel, Retail, Logistics, Hospital.*

---

## KPI 2: Peak Demand

```
Peak_Demand_kW = MAX(demand_kw) over the period

Demand Reduction (if battery present):
Peak_Shaved_kW = Peak_Without_Battery - Peak_With_Battery

Demand Charge Saving (€):
Saving = Peak_Shaved_kW × demand_charge_rate (€/kW/month)
```

---

## KPI 3: Load Factor

**Definition:** How consistently the building uses energy relative to its peak.

```
Load_Factor = Average_Demand_kW / Peak_Demand_kW
Range: 0 to 1

→ Close to 1.0: Steady, efficient load profile (good)
→ Close to 0.0: Highly peaked load (poor — high demand charges)

Target: > 0.70 for office buildings
```

---

## KPI 4: Base Load

**Definition:** Minimum consumption when building is unoccupied — the "sleep consumption."

```
Base_Load_kW = MIN(demand_kw) during 02:00–04:00 local time

Alert condition:
Base_Load / Peak_Demand > 0.35
→ Equipment not entering standby properly
```

---

## KPI 5: Solar KPIs (active when has_pv = True)

```
Self_Consumption_Rate = self_consumed_kwh / generated_kwh
Target: > 70%
Low value → battery needed, or load scheduling optimization required

Self_Sufficiency_Rate = self_consumed_kwh / total_consumption_kwh
Target: 20–60% (depends on system size and location)

Solar_Yield = generated_kwh / pv_capacity_kwp
Germany: 900–1050 kWh/kWp/year
Turkey: 1300–1600 kWh/kWp/year

Performance_Ratio (PR) = actual_yield / theoretical_yield
theoretical_yield = irradiance_kwh_m2 × pv_capacity_kwp × 0.80
Target PR: > 0.75
Low PR → panel soiling, shading, or inverter fault
```

---

## KPI 6: Battery KPIs (active when has_battery = True)

```
Round_Trip_Efficiency = discharged_kwh / charged_kwh
Target: > 0.90 (LFP lithium-ion)

Cycle_Count_Daily = charged_kwh / battery_capacity_kwh
(Counts full equivalent cycles per day)
Lifetime estimate: total_cycles / guaranteed_cycles

Battery_Utilization = average_soc_used / battery_capacity_kwh
Recommended operating band: 20%–80% SoC
(Protects against degradation)
```

---

## KPI 7: Heat Pump COP (active when has_heat_pump = True)

```
COP_actual = Heat_Energy_Produced_kWh / Electricity_Consumed_kWh

Seasonal COP (SCOP):
SCOP = Total_Season_Heat_kWh / Total_Season_Electricity_kWh

COP_Performance_Ratio = COP_actual / COP_rated
< 0.80 → Maintenance alert (MEDIUM)
< 0.60 → Critical fault alert (HIGH)

Note: COP naturally decreases in cold weather.
Always compare COP at equivalent outdoor temperature bands.
```

---

## KPI 8: Carbon & Cost

```
CO2_Consumption_kg = consumption_kwh × emission_factor_kg_kwh

CO2_Avoided_kg = solar_generated_kwh × emission_factor_kg_kwh
(Solar generation = grid electricity NOT consumed)

CO2_Net_kg = CO2_Consumption_kg - CO2_Avoided_kg

Carbon_Intensity = CO2_Net_kg / conditioned_area_m2
Unit: kg CO₂/m²/year

Grid Emission Factors (static reference):
  Germany 2024: 0.380 kg CO₂/kWh (source: Umweltbundesamt)
  Turkey 2024:  0.442 kg CO₂/kWh (source: TEİAŞ)

Energy_Cost_EUR =
  (grid_import_kwh × energy_price_eur_kwh)
  + (peak_demand_kw × demand_charge_eur_kw_month)
  - (grid_export_kwh × feed_in_tariff_eur_kwh)
```

---

## Anomaly Detection Rules

### A1 — Consumption Spike
```
Trigger:
  consumption_kwh(t) > rolling_avg(last 30 days, same hour, same day type) × 1.5
  AND outdoor_temp_change < 5°C (weather not the cause)

Severity: MEDIUM
Probable causes: Equipment fault, setpoint drift, unauthorized use
```

### A2 — High Base Load (After-Hours Waste)
```
Trigger:
  base_load_kw > peak_demand_kw × 0.35
  AND time between 01:00–05:00 local

Severity: LOW → MEDIUM
Probable causes: Servers, lighting, HVAC not shutting down
```

### A3 — COP Degradation
```
Trigger:
  COP_actual < COP_rated × 0.80
  AND outdoor_temp > design_temp - 3°C
  (low COP is not weather-related)

Severity: HIGH
Probable causes: Filter fouling, refrigerant leak, delayed maintenance
```

### A4 — Solar Underperformance
```
Trigger:
  PR_actual < 0.70
  AND irradiance > 400 W/m² (sufficient sunlight available)

Severity: MEDIUM
Probable causes: Panel soiling, shading, inverter fault
```

### A5 — Battery Anomaly
```
Condition A: round_trip_efficiency < 0.85
  Severity: MEDIUM — Cell degradation or temperature effect

Condition B: SoC stays at 95%+ continuously (self_consumption mode)
  Severity: LOW — Capacity oversized or load scheduling needed

Condition C: SoC drops below 10% repeatedly
  Severity: HIGH — Over-discharge risk, battery life at risk
```

### A6 — Weekend/Holiday Overconsumption
```
Trigger:
  consumption(weekend/holiday) > avg_weekday_consumption × 0.60

Severity: MEDIUM
Probable causes: HVAC not switching to holiday mode, standby loads
```

### A7 — Insulation Performance Degradation
```
Trigger:
  climate_adjusted_EUI increased > 15% vs prior year
  AND weather comparable
  AND HVAC system unchanged

Severity: MEDIUM
Probable causes: Insulation deterioration, increased air infiltration
Action: Recommend Blower Door Test
```

---

## Battery Dispatch Logic

### Strategy A: Self-Consumption Mode

Runs every 15 minutes (Tier 2-3):

```
net_load = consumption(t) - solar_generation(t)

IF net_load < 0 (solar surplus):
  IF SoC < 90%: charge battery
  ELSE: export to grid

IF net_load > 0 (consumption > solar):
  IF SoC > 15%: discharge battery
  ELSE: import from grid

Optimization target: maximize self_consumption_rate
```

### Strategy B: Peak Shaving Mode

Runs every 15 minutes (Tier 2-3):

```
peak_threshold = defined by operator
(Default suggestion: 90th percentile of last 12 months demand)

IF demand(t) > peak_threshold:
  discharge_power = demand(t) - peak_threshold
  IF SoC > 15%: discharge battery
  ELSE: alert (insufficient capacity)

IF demand(t) < peak_threshold × 0.50:
  "charge opportunity" period
  IF SoC < 80%: charge from grid or solar
  Preference: charge during off-peak tariff hours

Optimization target: minimize peak_demand_kw → reduce demand charges
```

---

## HVAC Optimization Rules

### H1 — Early Start Optimization (Optimal Start)

```
Optimal start time = occupancy_start - preheat_time

Simplified preheat calculation (Phase 1):
  preheat_minutes = (target_temp - current_indoor_temp) × 6

Example: Current 14°C, target 20°C → 6°C diff → 36 min pre-start

Alert: HVAC starting > 90 min before occupancy with no pre-heat justification
→ Energy waste from over-conditioning
```

### H2 — Setpoint Optimization

```
Winter heating target: 20°C (EN 16798-1 standard)
Summer cooling target: 24°C

Each 1°C above heating setpoint → ~6% excess energy
Each 1°C below cooling setpoint → ~6% excess energy

Alert: setpoint outside target ± 1°C → recommendation generated
```

### H3 — Holiday/Unoccupied Mode

```
Setback targets:
  Winter unoccupied: 16°C (frost protection)
  Summer unoccupied: 28°C

Detection: compare occupancy_schedule with actual HVAC setpoints
Alert: HVAC maintaining comfort temperature during unoccupied hours
```

---

## Simulation Engine

### Add PV Solar

```
Inputs: pv_capacity_kwp (user input or auto-suggested from roof_area_m2)
Auto-suggestion: max_kwp = roof_area_m2 / 7 (1 kWp ≈ 7 m²)

Step 1: Estimate generation
  hourly_generation = pv_capacity_kwp × irradiance_kwh_m2 × 0.80 (PR)

Step 2: Self-consumption calculation
  self_consumed = MIN(hourly_generation, hourly_consumption)
  exported = hourly_generation - self_consumed

Step 3: Financial calculation
  annual_saving = (self_consumed × energy_price) + (exported × feed_in_tariff)

Step 4: CO2 calculation
  co2_avoided = hourly_generation × emission_factor

Step 5: Investment return
  investment = pv_capacity_kwp × installed_cost_per_kwp
  payback_years = investment / annual_saving
  npv = NPV(discount_rate=0.05, cashflows=10 years)
  irr = IRR(cashflows)

Default cost assumptions:
  Germany 2024: 1,000–1,400 €/kWp (displayed as range)
  Turkey 2024:  600–900 USD/kWp
```

### Add Battery Storage

```
Inputs: battery_capacity_kwh, battery_strategy
Default technology recommendation: LFP

Technology specs (LFP, 2024 market):
  cost_per_kwh: 600–900 €/kWh (system installed)
  cycle_life: 4,000 cycles
  warranty: 10 years
  round_trip_efficiency: 0.92
  operating_temp: -10°C to 45°C
  fire_safety: IEC 62619 compliant

Dispatch simulation: apply strategy logic to 12 months historical data
Financial output: peak_charge_saving + arbitrage_saving vs investment
```

### Switch to Heat Pump

```
Inputs: heat_pump_capacity_kw, cop_rated

Current heating cost (gas boiler assumption):
  existing_cost = heating_energy_kwh / boiler_efficiency × gas_price_eur_kwh

Heat pump cost:
  hp_electricity = heating_energy_kwh / cop_rated
  hp_cost = hp_electricity × electricity_price_eur_kwh

Saving = existing_cost - hp_cost
CO2_reduction = existing_co2 - (hp_electricity × emission_factor)

Germany GEG compliance note:
  Heat pump automatically satisfies 65% renewable requirement
  → Flag applicable KfW/BAFA incentives
```

### Insulation Upgrade (Wall / Roof / Window)

```
Heat loss reduction:
  Q_saved = ΔU × surface_area × HDD × 24 / 1000
  (ΔU = current_u_value - target_u_value, in W/m²K)

Cost assumptions:
  Wall insulation (100mm EPS): 80–120 €/m² (Germany)
  Roof insulation: 60–100 €/m²
  Triple glazing windows: 400–700 €/m²

KfW BEG: 15–20% grant may apply → auto-match
```

---

## Sustainability Logic

```
Monthly ESG Score (0–100):
  Component 1 (40%): EUI vs sector benchmark
  Component 2 (30%): CO2 intensity vs country average
  Component 3 (20%): Renewable share (solar self-sufficiency)
  Component 4 (10%): Compliance status

Carbon Credit Value:
  carbon_credit_value_eur = co2_avoided_kg / 1000 × eu_ets_price_eur_ton
  (EU ETS carbon price: ~60–80 €/ton CO₂, 2024)
```

---

## Regulatory Compliance Checks

### Germany — EnEfG
```
IF organization.employee_count >= 250:
  → ISO 50001 certification required
  IF building.iso50001_certified == False:
    → Priority: HIGH
    → Action: "ISO 50001 certification required under EnEfG"
    → Match: BAFA energy audit support program
```

### Germany — GEG
```
IF hvac_replacement_year >= 2024:
  → Must use ≥65% renewable energy source
  IF renewable_share < 0.65:
    → Priority: URGENT
    → Action: "GEG §71 compliance required for new heating systems"
    → Recommendation: Switch to heat pump
    → Match: BEG / BAFA Wärmepumpe grant

Wall U-value check:
  IF wall_u_value > 0.24 AND renovation_planned:
    → Action: "GEG minimum insulation standard not met"
    → Match: KfW 261 / BEG
```

### EU — EPBD
```
IF building.year_built < 2010 AND renovation_planned == False:
  IF climate_adjusted_eui > 150:
    → Action: "Building significantly below nZEB target"
    → Priority: MEDIUM
```

### Turkey — BEP-TR
```
IF energy_certificate IS NULL OR energy_certificate_year < (current_year - 10):
  → Action: "Energy Performance Certificate (EPC) required under BEP-TR"
  → Priority: MEDIUM
```
