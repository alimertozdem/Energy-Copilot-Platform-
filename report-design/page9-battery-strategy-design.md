# PAGE 9: Battery Dispatch Strategies & Financial Simulation
**Status:** Design Phase | **Target:** DAX v46-v52 | **Deadline:** 2026-05-18

---

## 📋 OVERVIEW

**Purpose:** Battery storage optimization (SoC management, dispatch strategy comparison, ROI simulation)

**Scope:** Three dispatch strategies:
1. **Self-Consumption** — charge from PV, discharge evening peak
2. **Peak-Shaving** — discharge during grid peak hours (reduce demand charge)
3. **Time-of-Use** — charge during off-peak, discharge during peak (day-ahead market)

**Target Users:**
- Energy Managers (strategy selection)
- Financial stakeholders (ROI calculation)
- Facility Managers (daily SoC monitoring)

---

## 🗂️ DATA MODEL (Fabric Gold Layer)

### Table 1: `gold_battery_dispatch` (30-day actual + simulated)

```
Column Name              | Type      | Source        | Description
─────────────────────────┼───────────┼───────────────┼──────────────────────
date                    | date      | calculated    | daily aggregate
building_id             | string    | static        | FK: silver_building_master
battery_id              | string    | static        | unique battery identifier
strategy                | string    | config        | Self-Consumption / Peak-Shaving / TOU
strategy_priority       | int       | config        | 1=primary, 2=secondary
soc_start_percent       | float     | calculated    | State of Charge @ 00:00
soc_end_percent         | float     | calculated    | State of Charge @ 23:59
soc_target_percent      | float     | config        | desired SoC (e.g., 50% evening)
charge_kwh              | float     | measured      | total energy charged (grid+PV)
discharge_kwh           | float     | measured      | total energy discharged
grid_charge_kwh         | float     | measured      | grid input (kWh)
pv_charge_kwh           | float     | measured      | PV input (kWh)
charging_efficiency     | float     | config        | 90-95% typical
discharging_efficiency  | float     | config        | 90-95% typical
round_trip_efficiency   | float     | calculated    | charge_eff × discharge_eff
cycle_count             | float     | measured      | battery cycle depth
cycle_depth_percent     | float     | calculated    | avg depth per cycle
cost_avoided_eur        | float     | calculated    | savings from avoided peak charges
revenue_from_market_eur | float     | calculated    | grid services revenue (if applicable)
co2_avoided_kg          | float     | calculated    | emissions avoided
health_score_percent    | float     | calculated    | battery degradation estimate
```

### Table 2: `gold_battery_simulation` (scenario modeling)

```
Column Name              | Type      | Source        | Description
─────────────────────────┼───────────┼───────────────┼──────────────────────
scenario_id             | string    | static        | e.g., "100kWh_LFP_SC"
building_id             | string    | static        | FK
scenario_name           | string    | static        | "100kWh LFP + Self-Consumption"
battery_type            | string    | config        | LFP / NCA / Lead-acid
battery_capacity_kwh    | float     | config        | installed capacity (kWh)
battery_power_kw        | float     | config        | max charge/discharge rate
battery_cost_eur        | float     | config        | capex
battery_lifespan_years  | int       | config        | expected life (e.g., 10 years)
strategy_primary        | string    | config        | dispatch strategy
pv_capacity_kwp        | float     | config        | if adding PV
annual_savings_eur      | float     | calculated    | year 1 savings
annual_co2_avoided_kg   | float     | calculated    | CO2 reduction
payback_years           | float     | calculated    | years to ROI
npv_10yr_eur            | float     | calculated    | net present value
irr_percent             | float     | calculated    | internal rate of return
comparison_score        | float     | calculated    | ranking metric (0-100)
```

### Table 3: `gold_battery_daily_summary` (KPI aggregates)

```
Column Name              | Type      | Source        | Description
─────────────────────────┼───────────┼───────────────┼──────────────────────
date                    | date      | calculated    | daily
building_id             | string    | static        | FK
strategy                | string    | static        | active strategy
total_cycles_cumulative | float     | aggregated    | cumulative cycle count
total_cost_avoided_eur  | float     | aggregated    | YTD savings
total_co2_avoided_kg    | float     | aggregated    | YTD emissions reduction
avg_soc_percent         | float     | aggregated    | mean SoC across day
efficiency_percent      | float     | calculated    | round trip eff
battery_health_percent  | float     | calculated    | estimated remaining capacity
```

---

## 🧮 DAX MEASURES (v46-v52)

### KPI Cards (C1-C4)

**C1: Annual Savings (€)**
```dax
-- v46_C1_Annual_Savings_EUR
SUMX(
    FILTER(gold_battery_dispatch, gold_battery_dispatch[building_id] = SELECTEDVALUE(silver_building_master[building_id])),
    gold_battery_dispatch[cost_avoided_eur]
) * 365 / COUNTDISTINCT(gold_battery_dispatch[date])

-- Annual projection from 30-day observed data
```

**C2: Payback Period (years)**
```dax
-- v46_C2_Payback_Years
VAR SelectedScenario = SELECTEDVALUE(gold_battery_simulation[scenario_id])
VAR AnnualSavings = [v46_C1_Annual_Savings_EUR]
VAR BatteryCost = CALCULATE(
    VALUES(gold_battery_simulation[battery_cost_eur]),
    gold_battery_simulation[scenario_id] = SelectedScenario
)
RETURN DIVIDE(BatteryCost, AnnualSavings, BLANK())
```

**C3: CO₂ Avoided (tCO₂/year)**
```dax
-- v46_C3_CO2_Avoided_tCO2
VAR AnnualCO2 = SUMX(
    FILTER(gold_battery_dispatch, 
        gold_battery_dispatch[building_id] = SELECTEDVALUE(silver_building_master[building_id])
    ),
    gold_battery_dispatch[co2_avoided_kg]
) * 365 / COUNTDISTINCT(gold_battery_dispatch[date])

RETURN AnnualCO2 / 1000  -- convert kg to tCO2
```

**C4: Battery Efficiency (round-trip %)**
```dax
-- v46_C4_Round_Trip_Efficiency
AVERAGEX(
    gold_battery_dispatch,
    gold_battery_dispatch[round_trip_efficiency] * 100
)
```

### Visuals (V1-V5)

**V1: 30-day SoC Trend (Area Chart)**
```dax
-- v46_V1_SoC_Trend
-- X-axis: date, Y-axis: soc_end_percent
-- Color by strategy: SC (green), PS (orange), TOU (blue)
-- Stacked area showing multiple strategies if comparing

Data: gold_battery_dispatch[soc_end_percent]
Axis: gold_battery_dispatch[date]
Legend: gold_battery_dispatch[strategy]
```

**V2: Daily Charge/Discharge (Stacked Bar)**
```dax
-- v46_V2_Charge_Discharge
-- X-axis: date
-- Y1 (blue): charge_kwh, Y2 (red): discharge_kwh
-- Stacked bar showing flow direction

Data: [Charge] = gold_battery_dispatch[charge_kwh]
      [Discharge] = gold_battery_dispatch[discharge_kwh]
Format: Stacked column, value labels
```

**V3: Scenario Comparison Table**
```
Columns:
  scenario_name | battery_capacity_kwh | battery_cost_eur | annual_savings_eur | payback_years | co2_avoided_kg | comparison_score

Sorting: comparison_score DESC

Example:
100kWh LFP + TOU     | 100         | €15,000  | €2,100 | 7.1   | 2,500 | 92
100kWh LFP + SC      | 100         | €15,000  | €1,800 | 8.3   | 2,100 | 88
50kWh NCA + PS       | 50          | €8,000   | €1,200 | 6.7   | 1,400 | 76
```

**V4: ROI Gauge (Annual Savings Target)**
```dax
-- v46_V4_ROI_Target_Gauge
VAR ActualSavings = [v46_C1_Annual_Savings_EUR]
VAR TargetSavings = 2000  -- e.g., €2,000/year target
RETURN DIVIDE(ActualSavings, TargetSavings, BLANK()) * 100

-- Gauge: 0-150%, target = 100%
```

**V5: Cost vs Payback Scatter**
```dax
-- v46_V5_Cost_vs_Payback
-- X-axis: battery_cost_eur (size)
-- Y-axis: payback_years
-- Color: comparison_score (green = high, red = low)
-- Bubble size: capacity_kwh

Rows: gold_battery_simulation[scenario_id]
X: gold_battery_simulation[battery_cost_eur]
Y: gold_battery_simulation[payback_years]
Size: gold_battery_simulation[battery_capacity_kwh]
Color: gold_battery_simulation[comparison_score]
```

---

## 🎨 LAYOUT (Power BI Canvas)

```
┌────────────────────────────────────────────────────────────────────┐
│ 🟢 PAGE 9: Battery Dispatch Strategies & Financial Simulation     │
└────────────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│      C1         │  │      C2         │  │      C3         │  │      C4         │
│ Annual Savings  │  │ Payback Period  │  │ CO₂ Avoided     │  │  Efficiency     │
│  €2,100/yr      │  │    7.1 years    │  │  2.5 tCO₂/yr    │  │    92%          │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ V1: 30-day State of Charge (SoC) Trend                               │
│ [Area chart: Self-Consumption (green) vs Peak-Shaving (orange)]      │
│ Peak SoC: 95%, Trough SoC: 10%, Avg: 55%                             │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────┐  ┌─────────────────────────────────────┐
│ V2: Daily Charge/Discharge (kWh)        │  │ V4: Annual Savings ROI Gauge        │
│ [Stacked bar: blue=charge, red=disch]   │  │ [Gauge: 0%-150%, current 105%]      │
│ Avg charge: 45kWh, Avg disch: 42kWh    │  │ Target: €2,000 → Actual: €2,100     │
└─────────────────────────────────────────┘  └─────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ V3: Strategy Comparison (Scenario Analysis)                                   │
├──────────────────────┬────────┬────────┬──────────┬──────────┬──────────┬────┤
│ Scenario Name        │ kWh    │ Cost € │ Savings €│Payback yr│CO₂ tCO₂ │ ⭐ │
├──────────────────────┼────────┼────────┼──────────┼──────────┼──────────┼────┤
│100kWh LFP + TOU      │ 100    │15,000  │ 2,100    │ 7.1      │ 2.5     │ 92 │
│100kWh LFP + SC       │ 100    │15,000  │ 1,800    │ 8.3      │ 2.1     │ 88 │
│50kWh NCA + PS        │ 50     │ 8,000  │ 1,200    │ 6.7      │ 1.4     │ 76 │
└──────────────────────┴────────┴────────┴──────────┴──────────┴──────────┴────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ V5: Cost vs Payback Period (Bubble: size=capacity, color=score)             │
│                                                                               │
│  Payback (yr)                                                                │
│       15 │                                                                   │
│       10 │              ● 50kWh                                              │
│        7 │        ● 100kWh SC                                                │
│        5 │      ● 100kWh TOU                                                 │
│        0 └────────┴────────────┴──────────┴──────────┴──────────            │
│            €0   €5,000    €10,000   €15,000   €20,000   Cost              │
│                                                                               │
│          ✅ Better (high score)            ⚠️ Lower score (red/yellow)     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 DATA GENERATION (Trial Period)

**File:** `sample-data/battery_simulator.py`

```python
# Generate battery dispatch data for 6 buildings
# Assumptions:
#   - 100kWh LFP battery (3 scenario variants: 50kWh, 100kWh, 150kWh)
#   - 3 dispatch strategies (SC, PS, TOU)
#   - 30-day simulation (2026-04-20 to 2026-05-19)
#   - Building-specific PV capacity (5-50 kWp)
#   - Grid pricing profiles (DE/TR)

# Outputs:
#   1. gold_battery_dispatch (30 days × 6 buildings × 3 strategies = 540 rows)
#   2. gold_battery_simulation (3 scenarios × 6 buildings = 18 rows)
#   3. gold_battery_daily_summary (30 days × 6 buildings = 180 rows)
```

**Realistic Assumptions:**

| Metric | Min | Typical | Max |
|---|---|---|---|
| **Daily Charge (kWh)** | 20 | 40 | 80 |
| **Daily Discharge (kWh)** | 15 | 35 | 70 |
| **SoC Range (%)** | 10-95 | 20-85 | 5-100 |
| **Round-trip Efficiency** | 81% | 86% | 90% |
| **Daily Cycles** | 0.2 | 0.4 | 0.8 |
| **Annual Savings (€)** | €800 | €1,500 | €2,500 |
| **Payback Period** | 5yr | 7yr | 10yr |

---

## 🔧 PIPELINE CHANGES (Fabric Notebook)

### New Notebook: `12_battery_dispatch_and_simulation.py`

```
INPUT:  gold_kpi_daily (building consumption, solar generation)
        gold_battery_sensor_readings (SoC, charge/discharge rates)
        gold_building_master (building metadata)

PROCESS:
1. Load 30-day consumption + solar data
2. For each building, simulate 3 dispatch strategies:
   a) Self-Consumption:
      - Charge when PV > consumption
      - Discharge when consumption > PV (evening peak)
      - Target SoC: 50% (reserve for next day)
   
   b) Peak-Shaving:
      - Discharge during grid peak hours (17:00-21:00)
      - Charge during off-peak (23:00-06:00)
      - Target SoC: 80% (ready for peak discharge)
   
   c) Time-of-Use:
      - Charge during cheapest hours (off-peak)
      - Discharge during expensive hours (peak)
      - Target SoC: dynamic (based on price forecast)

3. Calculate KPIs:
   - soc_start/end, charge_kwh, discharge_kwh
   - round_trip_efficiency, cost_avoided_eur, co2_avoided_kg
   - payback_years, NPV_10yr, IRR

4. Generate 3 scenarios per building:
   - 50kWh NCA (cheaper, shorter lifespan)
   - 100kWh LFP (balanced, 10yr lifespan)
   - 150kWh LFP (premium, max capacity)

OUTPUT: gold_battery_dispatch
        gold_battery_simulation
        gold_battery_daily_summary
```

---

## 💰 ENERGY LOGIC & FINANCIAL MODEL

### Dispatch Strategy Details

**Self-Consumption (Best for PV + building loads):**
```
Morning (06:00-12:00):   PV surplus → Battery charge (95% efficiency)
Afternoon (12:00-17:00): PV + Battery discharge as needed
Evening (17:00-23:00):   Grid consumption, Battery discharge peak
Night (23:00-06:00):     Battery recharge (if deficit), charge cost: €0.12/kWh

Cost avoided: PV self-consumption premium (€0.15-0.20/kWh vs grid export)
Annual savings: ~€1,500-2,000 (100kWh battery)
```

**Peak-Shaving (Best for demand charge reduction):**
```
Charge window (23:00-06:00): Grid charge @ off-peak rate (€0.05/kWh)
Peak shaving (17:00-21:00):  Discharge 100% → reduce peak demand
Demand charge: €5-15/kWh/month (typical commercial)

Cost avoided: Demand charge reduction ~€200-300/month
Annual savings: €2,400-3,600
```

**Time-of-Use (Best for market-reactive strategy):**
```
Requires: 24h price forecast OR dynamic pricing (AEMO/EPEX)
Charge: lowest price hours (typically 23:00-06:00, early morning)
Discharge: highest price hours (peak 17:00-21:00)

Assumption: EU market, average spread €0.15-0.25/kWh
Annual savings: €2,500-3,500
Note: Requires 1-day forecast accuracy (Phase 2)
```

---

## ✅ VALIDATION CHECKLIST

- [ ] gold_battery_dispatch: 30 days × 6 buildings × 3 strategies = 540+ rows
- [ ] SoC range realistically 10-95% (not 0-100%)
- [ ] Charge/discharge daily variation ±30% (not flat)
- [ ] Round-trip efficiency 81-90% range
- [ ] Annual savings €800-2500 realistic per strategy
- [ ] Payback period 5-10 years reasonable
- [ ] 3 scenarios per building defined
- [ ] Comparison score ranking logical (cost vs payback tradeoff)
- [ ] V1 area chart shows strategy differences visually
- [ ] V3 table sortable by payback, cost, score
- [ ] V5 scatter clearly separates best (top-right) vs worst scenarios
- [ ] Financial metrics (NPV, IRR) calculated correctly

---

## 🚀 ROLLOUT TIMELINE

| Task | Duration | Owner |
|---|---|---|
| Data model + financial assumptions finalize | 3h | Mert (approval) |
| Battery simulator script (3 strategies) | 4h | Claude (code) |
| Notebook 12 (Fabric) | 2h | Claude (code) |
| DAX measures (v46-v52) | 4h | Claude (code) |
| Power BI UI binding | 2h | Claude (UI) |
| Scenario comparison validation | 2h | Mert (QA) |
| **TOTAL** | **~17h** | |

**Target completion:** 2026-05-18 (by day 12 of trial)

---

## 📝 NOTES FOR ENERGY DOMAIN EXPERT

- **COP vs SCOP:** Battery "efficiency" ≠ HVAC COP. Round-trip efficiency is energy input/output ratio.
- **Dispatch strategy constraints:** Real-world battery controllers have safety limits (min SoC 10%, max SoC 95%). Simulator must respect these.
- **Cost assumptions:** German grid (2024): off-peak €0.05/kWh, peak €0.20/kWh. Turkish grid: 20-30% cheaper. Use building location for accuracy.
- **Lifespan modeling:** LFP batteries degrade ~2-3% per 1,000 cycles. Simulator should estimate remaining capacity after 10yr.
- **Phase 2 upgrade:** Real-time dispatch (Eventstream) will enable dynamic strategy selection (currently static).
