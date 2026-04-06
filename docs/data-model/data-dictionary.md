# Data Dictionary — Energy Copilot Platform

## Bronze Layer Tables

### bronze.raw_energy_readings
Raw energy consumption data. Written as-is from source.

| Column | Type | Description |
|---|---|---|
| ingestion_id | STRING | Unique record ID (UUID) |
| building_id | STRING | Building identifier |
| source_system | STRING | BACnet / Modbus / API / CSV |
| sensor_id | STRING | Meter or sensor identifier |
| timestamp_utc | TIMESTAMP | Measurement time (UTC) |
| raw_value | DOUBLE | Raw measurement value |
| raw_unit | STRING | kWh / W / kW / Wh (non-normalized) |
| ingested_at | TIMESTAMP | Time data arrived at platform |
| tier | STRING | Tier1 / Tier2 / Tier3 |

### bronze.raw_solar_generation
Raw PV solar generation data.

| Column | Type | Description |
|---|---|---|
| ingestion_id | STRING | UUID |
| building_id | STRING | |
| timestamp_utc | TIMESTAMP | |
| generated_raw | DOUBLE | Generated energy (raw) |
| exported_raw | DOUBLE | Exported to grid (raw) |
| raw_unit | STRING | |
| inverter_id | STRING | Inverter identifier |
| ingested_at | TIMESTAMP | |

### bronze.raw_battery_status
Raw battery system telemetry.

| Column | Type | Description |
|---|---|---|
| ingestion_id | STRING | UUID |
| building_id | STRING | |
| timestamp_utc | TIMESTAMP | |
| soc_raw | DOUBLE | State of Charge (raw %) |
| charge_power_raw | DOUBLE | Charging power (raw) |
| discharge_power_raw | DOUBLE | Discharging power (raw) |
| battery_id | STRING | Battery unit identifier |
| ingested_at | TIMESTAMP | |

### bronze.raw_weather_data
Raw weather data from external API.

| Column | Type | Description |
|---|---|---|
| ingestion_id | STRING | UUID |
| building_id | STRING | |
| timestamp_utc | TIMESTAMP | |
| temperature_raw | DOUBLE | Outdoor temperature (raw) |
| humidity_raw | DOUBLE | Humidity (raw) |
| solar_irradiance | DOUBLE | Solar irradiance W/m² |
| wind_speed_raw | DOUBLE | Wind speed (raw) |
| source_api | STRING | OpenWeather / DWD / MGM |
| ingested_at | TIMESTAMP | |

### bronze.raw_hvac_data
Raw HVAC system data.

| Column | Type | Description |
|---|---|---|
| ingestion_id | STRING | UUID |
| building_id | STRING | |
| sensor_id | STRING | HVAC unit identifier |
| timestamp_utc | TIMESTAMP | |
| supply_temp_raw | DOUBLE | Supply air temperature |
| return_temp_raw | DOUBLE | Return air temperature |
| power_raw | DOUBLE | Instantaneous power |
| runtime_raw | INTEGER | Runtime in seconds |
| mode_raw | STRING | Heating / Cooling / Standby / Off |
| ingested_at | TIMESTAMP | |

---

## Silver Layer Tables

### silver.building_master
Master reference table for all buildings. Core of the data model.

| Column | Type | Description |
|---|---|---|
| building_id | STRING | Primary key |
| organization_id | STRING | Parent organization |
| building_name | STRING | Display name |
| country_code | STRING | DE / TR |
| city | STRING | |
| climate_zone | STRING | e.g. Cfb (Oceanic), BSk (Semi-arid) |
| gross_floor_area_m2 | DOUBLE | Gross floor area |
| conditioned_area_m2 | DOUBLE | Heated/cooled area |
| year_built | INTEGER | |
| building_type | STRING | Office / Retail / Hotel / Logistics |
| subscription_tier | STRING | Insight / Monitor / Copilot |
| **Technology Profile** | | |
| has_pv | BOOLEAN | PV solar system present |
| pv_capacity_kwp | DOUBLE | Installed PV capacity (kWp) |
| roof_area_m2 | DOUBLE | Available roof area (optional) |
| roof_orientation | STRING | N / S / E / W / SE / SW |
| roof_tilt_deg | DOUBLE | Tilt angle in degrees |
| has_battery | BOOLEAN | Battery storage present |
| battery_capacity_kwh | DOUBLE | Total battery capacity |
| battery_technology | STRING | LFP / NMC |
| battery_strategy | STRING | self_consumption / peak_shaving |
| has_heat_pump | BOOLEAN | Heat pump system present |
| heat_pump_cop_rated | DOUBLE | Design COP value |
| heat_pump_capacity_kw | DOUBLE | Heating/cooling capacity |
| has_hvac_traditional | BOOLEAN | Traditional HVAC present |
| has_ev_charging | BOOLEAN | EV charging stations present |
| has_led_lighting | BOOLEAN | LED lighting system |
| **Building Envelope** | | |
| wall_u_value | DOUBLE | W/m²K — external wall |
| roof_u_value | DOUBLE | W/m²K — roof |
| floor_u_value | DOUBLE | W/m²K — ground floor |
| window_u_value | DOUBLE | W/m²K — windows |
| window_to_wall_ratio | DOUBLE | Window area / wall area (%) |
| air_tightness_ach | DOUBLE | Air changes per hour |
| thermal_mass_level | STRING | LOW / MEDIUM / HIGH |
| insulation_year | INTEGER | Last insulation renovation year |
| has_thermal_bridge | BOOLEAN | Known thermal bridges present |
| energy_certificate | STRING | A+ / A / B / C / D / E / F / G |
| energy_certificate_year | INTEGER | |
| **Regulatory** | | |
| regulatory_profile_id | STRING | FK to regulatory_rules |
| iso50001_certified | BOOLEAN | ISO 50001 energy management certified |
| **Timestamps** | | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### silver.energy_readings_clean
Normalized and quality-checked energy consumption data.

| Column | Type | Description |
|---|---|---|
| reading_id | STRING | UUID |
| building_id | STRING | |
| sensor_id | STRING | |
| timestamp_utc | TIMESTAMP | |
| timestamp_local | TIMESTAMP | Local time (per country) |
| consumption_kwh | DOUBLE | Normalized to kWh |
| demand_kw | DOUBLE | Instantaneous demand (kW) |
| data_quality_flag | STRING | OK / INTERPOLATED / MISSING / ANOMALY |
| interpolated | BOOLEAN | Was missing data filled in? |
| source_system | STRING | |

### silver.solar_generation_clean

| Column | Type | Description |
|---|---|---|
| building_id | STRING | |
| timestamp_utc | TIMESTAMP | |
| timestamp_local | TIMESTAMP | |
| generated_kwh | DOUBLE | Total generation |
| exported_kwh | DOUBLE | Exported to grid |
| self_consumed_kwh | DOUBLE | generated - exported |
| irradiance_wm2 | DOUBLE | Concurrent solar irradiance |
| data_quality_flag | STRING | |

### silver.battery_status_clean

| Column | Type | Description |
|---|---|---|
| building_id | STRING | |
| timestamp_utc | TIMESTAMP | |
| soc_pct | DOUBLE | State of Charge (0–100%) |
| charge_kw | DOUBLE | Charging power (positive) |
| discharge_kw | DOUBLE | Discharging power |
| net_power_kw | DOUBLE | charge - discharge |
| cycle_count | DOUBLE | Cumulative cycle count |
| active_strategy | STRING | self_consumption / peak_shaving |

### silver.weather_clean

| Column | Type | Description |
|---|---|---|
| building_id | STRING | |
| timestamp_utc | TIMESTAMP | |
| temperature_c | DOUBLE | Celsius |
| humidity_pct | DOUBLE | |
| solar_irradiance | DOUBLE | W/m² |
| wind_speed_ms | DOUBLE | m/s |
| heating_degree_day | DOUBLE | HDD (base 15°C) |
| cooling_degree_day | DOUBLE | CDD (base 22°C) |

### silver.grid_emission_factors
Static reference table. Updated annually.

| Column | Type | Description |
|---|---|---|
| country_code | STRING | DE / TR / ... |
| year | INTEGER | |
| emission_factor | DOUBLE | kg CO₂/kWh |
| source | STRING | IEA / UBA / TEIAS |
| last_updated | DATE | |

**Initial values:**
- Germany 2024: 0.380 kg CO₂/kWh (source: Umweltbundesamt)
- Turkey 2024: 0.442 kg CO₂/kWh (source: TEİAŞ)

### silver.electricity_tariffs

| Column | Type | Description |
|---|---|---|
| tariff_id | STRING | |
| country_code | STRING | |
| tariff_name | STRING | |
| time_of_use | BOOLEAN | Hourly pricing available |
| peak_price_eur_kwh | DOUBLE | Peak hour price |
| offpeak_price_eur_kwh | DOUBLE | Off-peak price |
| demand_charge_eur_kw | DOUBLE | Capacity charge €/kW/month |
| feed_in_tariff_eur_kwh | DOUBLE | Grid export price |
| valid_from | DATE | |
| valid_to | DATE | |

### silver.incentive_programs

| Column | Type | Description |
|---|---|---|
| program_id | STRING | |
| country_code | STRING | |
| program_name | STRING | KfW 261 / BAFA Wärmepumpe / YEKA |
| technology | STRING | heat_pump / pv / battery / efficiency / insulation |
| incentive_type | STRING | grant / loan / tax_credit / feed_in_tariff |
| max_amount_eur | DOUBLE | |
| eligibility_notes | TEXT | |
| application_url | STRING | |
| valid_from | DATE | |
| valid_to | DATE | |

### silver.regulatory_rules

| Column | Type | Description |
|---|---|---|
| rule_id | STRING | |
| country_code | STRING | |
| regulation_name | STRING | EnEfG / GEG / EPBD / BEP-TR |
| rule_type | STRING | mandatory / target / reporting |
| threshold | STRING | Applicability condition |
| requirement | TEXT | What must be done |
| deadline | DATE | Compliance deadline |
| penalty_notes | TEXT | |

---

## Gold Layer Tables

### gold.kpi_hourly
Hourly KPI aggregations. Primary table for Tier 2-3.

| Column | Type | Description |
|---|---|---|
| building_id | STRING | |
| hour_utc | TIMESTAMP | Hour start (UTC) |
| consumption_kwh | DOUBLE | |
| demand_kw | DOUBLE | Peak demand in hour |
| solar_generated_kwh | DOUBLE | Null if no PV |
| self_consumed_kwh | DOUBLE | |
| grid_import_kwh | DOUBLE | |
| grid_export_kwh | DOUBLE | |
| battery_soc_avg_pct | DOUBLE | Null if no battery |
| battery_charged_kwh | DOUBLE | |
| battery_discharged_kwh | DOUBLE | |
| cop_actual | DOUBLE | Null if no heat pump |
| temperature_c | DOUBLE | Outdoor temp |
| energy_cost_eur | DOUBLE | |

### gold.kpi_daily
Daily KPI summary. Primary table for Tier 1.

| Column | Type | Description |
|---|---|---|
| building_id | STRING | |
| date | DATE | |
| **Core KPIs** | | |
| eui_kwh_m2 | DOUBLE | Energy Use Intensity |
| peak_demand_kw | DOUBLE | Daily peak demand |
| load_factor_pct | DOUBLE | avg/peak ratio |
| base_load_kw | DOUBLE | Overnight minimum load |
| **Solar KPIs** | | |
| solar_generated_kwh | DOUBLE | |
| self_consumption_rate | DOUBLE | % of generation used on-site |
| self_sufficiency_rate | DOUBLE | % of consumption from solar |
| grid_export_kwh | DOUBLE | |
| solar_performance_ratio | DOUBLE | PR (actual/theoretical) |
| **Battery KPIs** | | |
| peak_shaved_kw | DOUBLE | Demand reduction achieved |
| battery_cycles | DOUBLE | Daily cycle count |
| arbitrage_saving_eur | DOUBLE | |
| round_trip_efficiency | DOUBLE | |
| **Heat Pump KPIs** | | |
| cop_actual | DOUBLE | |
| cop_rated | DOUBLE | |
| cop_performance_ratio | DOUBLE | actual/rated |
| **Cost & Carbon** | | |
| energy_cost_eur | DOUBLE | |
| demand_charge_eur | DOUBLE | |
| total_cost_eur | DOUBLE | |
| co2_consumption_kg | DOUBLE | |
| co2_avoided_kg | DOUBLE | Via solar generation |
| co2_net_kg | DOUBLE | |
| **Climate** | | |
| hdd | DOUBLE | Heating Degree Days |
| cdd | DOUBLE | Cooling Degree Days |
| climate_adjusted_eui | DOUBLE | |

### gold.kpi_monthly
Monthly aggregations for ESG reporting and billing analysis.

### gold.anomaly_log

| Column | Type | Description |
|---|---|---|
| anomaly_id | STRING | |
| building_id | STRING | |
| detected_at | TIMESTAMP | |
| anomaly_type | STRING | consumption_spike / cop_drop / solar_underperformance / base_load_high / battery_anomaly / holiday_overconsumption |
| severity | STRING | LOW / MEDIUM / HIGH / CRITICAL |
| affected_system | STRING | HVAC / PV / Battery / Meter / Envelope |
| description_tr | TEXT | Turkish explanation |
| description_de | TEXT | German explanation |
| description_en | TEXT | English explanation |
| probable_cause | TEXT | |
| recommended_action | TEXT | |
| estimated_loss_eur | DOUBLE | If unaddressed |
| acknowledged | BOOLEAN | |
| resolved | BOOLEAN | |

### gold.sustainability_metrics

| Column | Type | Description |
|---|---|---|
| building_id | STRING | |
| period_month | DATE | |
| co2_consumption_kg | DOUBLE | |
| co2_avoided_kg | DOUBLE | Via solar |
| co2_net_kg | DOUBLE | |
| co2_vs_baseline_pct | DOUBLE | vs prior year |
| carbon_credit_value_eur | DOUBLE | |
| esg_score | DOUBLE | 0–100 platform score |
| leed_gap_analysis | TEXT | |
| csrd_ready | BOOLEAN | |

### gold.compliance_status

| Column | Type | Description |
|---|---|---|
| building_id | STRING | |
| rule_id | STRING | FK to silver.regulatory_rules |
| checked_at | DATE | |
| compliant | BOOLEAN | |
| gap_description_tr | TEXT | |
| gap_description_de | TEXT | |
| action_required | TEXT | |
| deadline | DATE | |
| priority | STRING | LOW / MEDIUM / HIGH / URGENT |

### gold.incentive_matches

| Column | Type | Description |
|---|---|---|
| building_id | STRING | |
| program_id | STRING | FK to silver.incentive_programs |
| matched_at | DATE | |
| match_reason | TEXT | Why building qualifies |
| estimated_benefit_eur | DOUBLE | |
| action_required | TEXT | |
| application_url | STRING | |
| status | STRING | NEW / SEEN / APPLIED / EXPIRED |

### gold.recommendations

| Column | Type | Description |
|---|---|---|
| recommendation_id | STRING | |
| building_id | STRING | |
| generated_at | TIMESTAMP | |
| recommendation_type | STRING | quick_win / medium_term / strategic |
| affected_system | STRING | HVAC / PV / Battery / Envelope / Behavior |
| title_tr | TEXT | |
| title_de | TEXT | |
| title_en | TEXT | |
| description_tr | TEXT | |
| estimated_saving_eur_year | DOUBLE | |
| estimated_saving_kwh_year | DOUBLE | |
| co2_reduction_kg_year | DOUBLE | |
| implementation_effort | STRING | LOW / MEDIUM / HIGH |
| payback_years | DOUBLE | |
| applicable_incentives | STRING | Comma-separated program IDs |
| priority_score | DOUBLE | (saving × urgency) / effort |

### gold.simulation_add_pv

| Column | Type | Description |
|---|---|---|
| simulation_id | STRING | |
| building_id | STRING | |
| created_at | TIMESTAMP | |
| pv_capacity_kwp | DOUBLE | Simulated PV size |
| roof_area_used_m2 | DOUBLE | |
| annual_generation_kwh | DOUBLE | |
| self_consumed_kwh | DOUBLE | |
| grid_export_kwh | DOUBLE | |
| annual_saving_eur | DOUBLE | |
| co2_reduction_kg_year | DOUBLE | |
| investment_cost_eur | DOUBLE | |
| simple_payback_years | DOUBLE | |
| npv_eur | DOUBLE | 10-year NPV |
| irr_pct | DOUBLE | Internal Rate of Return |
| applicable_incentives | STRING | |
| assumptions_note | TEXT | e.g. "Roof area estimated" |

### gold.simulation_add_battery

| Column | Type | Description |
|---|---|---|
| simulation_id | STRING | |
| building_id | STRING | |
| created_at | TIMESTAMP | |
| battery_capacity_kwh | DOUBLE | |
| recommended_technology | STRING | LFP |
| battery_strategy | STRING | self_consumption / peak_shaving |
| peak_shaved_kw | DOUBLE | |
| self_consumption_gain_pct | DOUBLE | |
| annual_saving_eur | DOUBLE | |
| co2_reduction_kg_year | DOUBLE | |
| investment_cost_eur | DOUBLE | |
| system_lifetime_years | INTEGER | |
| warranty_years | INTEGER | |
| simple_payback_years | DOUBLE | |
| npv_eur | DOUBLE | |
| applicable_incentives | STRING | |

### gold.simulation_switch_hvac
### gold.simulation_add_insulation
### gold.simulation_window_upgrade
### gold.simulation_battery_strategy
*(Same structure pattern as above — details in business-logic documentation)*

### gold.data_health_log

| Column | Type | Description |
|---|---|---|
| building_id | STRING | |
| checked_at | TIMESTAMP | |
| data_freshness_ok | BOOLEAN | Last data within expected window |
| last_reading_at | TIMESTAMP | |
| quality_rate_pct | DOUBLE | % of OK records |
| missing_rate_pct | DOUBLE | |
| dead_sensor_detected | BOOLEAN | Same value for >2 hours |
| overall_health | STRING | HEALTHY / WARNING / CRITICAL |
