# Energy Copilot Platform — Semantic Model Setup Guide
## Microsoft Fabric / Power BI Direct Lake

---

## 1. How to Create the Semantic Model (Fabric UI)

1. In Fabric workspace, go to left menu → **New item** → **Semantic model**
2. Name: `EnergycopilotModel`
3. Select **Lakehouse**: `EnergyCopilotLakehouse`
4. Tables will be listed automatically — select only the required ones (see Section 2)
5. **Confirm** → model opens in Direct Lake mode

---

## 2. Tables and Columns to Add

### FACT TABLES (measurement data)

#### `gold_kpi_daily`
| Column | Type | Description |
|--------|------|------------|
| building_id | Text | FK → silver_building_master |
| date | Date | Date (relationship key) |
| year | Integer | |
| month | Integer | |
| total_consumption_kwh | Decimal | Daily total consumption |
| peak_demand_kw | Decimal | Daily peak demand |
| avg_load_factor | Decimal | Average load factor |
| solar_generated_kwh | Decimal | Solar generation |
| solar_self_consumed_kwh | Decimal | Solar self-consumption (on-site) |
| solar_exported_kwh | Decimal | Solar exported to grid |
| avg_solar_pr | Decimal | Solar performance ratio |
| avg_self_sufficiency_rate | Decimal | Energy self-sufficiency rate |
| battery_charged_kwh | Decimal | Battery charged |
| battery_discharged_kwh | Decimal | Battery discharged |
| battery_cycles_day | Decimal | Daily cycle count |
| battery_soc_min_pct | Decimal | Min state of charge |
| battery_soc_max_pct | Decimal | Max state of charge |
| avg_temperature_c | Decimal | Average outdoor temperature |
| hdd_day | Decimal | Heating degree-day |
| cdd_day | Decimal | Cooling degree-day |
| net_grid_consumption_kwh | Decimal | Net grid consumption |
| co2_emissions_kg | Decimal | CO₂ emissions |
| co2_savings_from_solar_kg | Decimal | CO₂ savings from solar |
| eui_kwh_m2 | Decimal | Energy use intensity |
| hdd_normalized_eui | Decimal | Climate-normalized EUI |
| carbon_intensity_kg_m2 | Decimal | Carbon intensity |
| estimated_cost_eur | Decimal | Estimated energy cost |
| estimated_savings_eur | Decimal | Estimated savings from solar |
| floor_area_m2 | Decimal | Floor area (m²) |
| has_pv | Boolean | |
| has_battery | Boolean | |
| has_heat_pump | Boolean | |
| subscription_tier | Text | |

#### `gold_anomaly_log`
| Column | Type | Description |
|--------|------|-------------|
| anomaly_id | Text | PK — SHA-256 hash of building_id\|detected_at\|anomaly_type |
| building_id | Text | FK → silver_building_master |
| anomaly_type | Text | CONSUMPTION_SPIKE, NIGHT_OVERCONSUMPTION, SOLAR_PR_DROP, BATTERY_OVERDISCHARGE, BATTERY_OVERCHARGE, DATA_QUALITY_GAP |
| severity | Text | critical / high / medium / low (lowercase) |
| detected_at | DateTime | Full detection timestamp |
| detected_date | Date | Detection date — cast of detected_at for Date table relationship |
| metric_value | Decimal | Measured value at time of anomaly |
| threshold_value | Decimal | Threshold value that was breached |
| description_en | Text | English description of the anomaly |
| is_resolved | Boolean | Whether the anomaly has been resolved |

> ✅ **Note:** `detected_date` is written as a proper **Date** type by the notebook (cast from `detected_at`). No manual type conversion needed in the Model editor.

#### `gold_consumption_forecast`
| Column | Type | Description |
|--------|------|------------|
| building_id | Text | FK |
| forecast_date | Date | Forecast date |
| predicted_kwh | Decimal | Prophet model forecast |
| lower_bound_kwh | Decimal | 80% lower bound |
| upper_bound_kwh | Decimal | 80% upper bound |
| confidence_pct | Decimal | Confidence interval |
| model_mape_pct | Decimal | Model error rate (MAPE) |
| trained_on_days | Integer | Training day count |
| model_version | Text | |
| forecasted_at | DateTime | |

#### `gold_recommendations`
| Column | Type | Description |
|--------|------|------------|
| building_id | Text | FK |
| building_name | Text | |
| rank | Integer | Priority rank (1=most important) |
| action_type | Text | INSTALL_HEAT_PUMP, ADD_SOLAR... |
| priority_label | Text | Critical / High / Medium / Low |
| priority_score | Decimal | 0-100 |
| compliance_driver | Text | |
| annual_saving_eur | Decimal | Annual savings (€) |
| co2_saving_kg | Decimal | Annual CO₂ reduction (kg) |
| capex_eur | Decimal | Investment cost |
| net_capex_eur | Decimal | Cost after subsidies |
| grant_eur | Decimal | Grant/incentive amount |
| payback_years | Decimal | Payback period (years) |
| npv_eur | Decimal | Net present value |
| title_en | Text | |
| description_en | Text | |
| assessed_at | DateTime | |

#### `gold_occupancy_profile`
| Column | Type | Description |
|--------|------|------------|
| building_id | Text | FK |
| day_of_week | Integer | 0=Mon … 6=Sun |
| hour_of_day | Integer | 0-23 |
| occupancy_probability | Decimal | 0.0–1.0 |
| profile_source | Text | calibrated / base_only |
| calibration_weeks | Integer | |
| confidence_score | Decimal | 0.0–1.0 |

### DIMENSION TABLE

#### `silver_building_master`
| Column | Type | Description |
|--------|------|------------|
| building_id | Text | PK |
| building_name | Text | Display building name |
| building_type | Text | office / retail / hotel... |
| country_code | Text | DE / TR / AT... |
| conditioned_area_m2 | Decimal | |
| subscription_tier | Text | basic / premium / enterprise |
| has_pv | Boolean | |
| has_battery | Boolean | |
| has_heat_pump | Boolean | |
| pv_capacity_kwp | Decimal | |
| battery_capacity_kwh | Decimal | |
| heat_pump_cop_rated | Decimal | |

### CALCULATED TABLE (create with DAX)

#### `Date` — Time Dimension
In Model editor → **New table** → paste the DAX below:

```dax
Date =
VAR _start = DATE(2024, 1, 1)
VAR _end   = DATE(2027, 12, 31)
RETURN
ADDCOLUMNS(
    CALENDAR(_start, _end),
    "Year",        YEAR([Date]),
    "Month",       MONTH([Date]),
    "MonthName",   FORMAT([Date], "MMMM", "en-US"),
    "MonthShort",  FORMAT([Date], "MMM",  "en-US"),
    "Quarter",     "Q" & QUARTER([Date]),
    "WeekNumber",  WEEKNUM([Date], 2),
    "DayOfWeek",   WEEKDAY([Date], 2),
    "DayName",     FORMAT([Date], "dddd", "en-US"),
    "IsWeekend",   IF(WEEKDAY([Date], 2) >= 6, TRUE, FALSE),
    "YearMonth",   FORMAT([Date], "YYYY-MM"),
    "YearQuarter", YEAR([Date]) & " Q" & QUARTER([Date])
)
```

---

## 3. Relationships

In Model editor → **Manage relationships** → create the following relationships:

| From (Many) | To (One) | Column | Type | Direction |
|-------------|----------|-------|-----|-----|
| gold_kpi_daily[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |
| gold_kpi_daily[date] | Date[Date] | date | Many→One | Single |
| gold_anomaly_log[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |
| gold_anomaly_log[detected_date] | Date[Date] | Date | Many→One | Single |
| gold_consumption_forecast[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |
| gold_consumption_forecast[forecast_date] | Date[Date] | date | Many→One | Single |
| gold_recommendations[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |
| gold_occupancy_profile[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |

> **Note:** `detected_date` is already written as a Date type by the notebook — no manual type conversion required before creating this relationship.

---

## 4. Column Hiding (Optional but Recommended)

Hide technical columns that don't need to appear in reports:
- All `_id` columns across all tables (except building_id — needed for filtering)
- `processed_at`, `detected_at`, `forecasted_at`, `assessed_at`, `computed_at`
- `model_version`, `profile_source`, `calibration_weeks`
- `floor_area_m2` in gold_kpi_daily (use the one from silver_building_master instead)

To hide: right-click a column → **Hide in report view**

---

## 5. Next Steps

After saving the model:
1. Add the measures from `02_dax_measures.dax`
2. Define RLS roles using `03_rls_definition.md`
3. Connect to this model via **Live Connection** in Power BI Desktop → proceed to report design
