// =====================================================================
// EnergyLens — CONSOLIDATED MEASURE LOADER (v57 + v58 + v59 + v60)
// Run ONCE in Tabular Editor 2 (C# Script tab → F5), then Model → Refresh.
// =====================================================================
// Adds every NEW measure the production-ready report needs, into its correct
// home table, idempotently (create-or-update). Built against the LIVE schema
// from probe_model_full_state, with these schema-driven adaptations:
//   - CSRD Disclosure Readiness: uses scope2_market_tco2 / scope3_estimated_tco2
//     (the planned scope2_method / scope3_disclosure_grade columns DO NOT exist).
//   - IoT Zone Setpoint Compliance: uses gold_iot_realtime[in_setpoint_pct]
//     (the old boolean [in_setpoint] column does not exist in the new 11b output).
//   - CRREM Pathway 2C: defined here (it was referenced by v57 but never created).
// Pre-req: Gate B done (gold_iot_fdd, gold_iot_daily_summary added; gold_kpi_hourly
//   related to Date[Date]). 'Time Grain' field parameter (PBI UI) optional — the
//   one measure that needs it is skipped gracefully if absent.
// =====================================================================

int created = 0, updated = 0, skipped = 0;

System.Action<string,string,string,string,string> Upsert = (table, name, expr, fmt, folder) => {
    if (!Model.Tables.Any(t => t.Name == table)) {
        Output("SKIP (missing table '" + table + "'): " + name); skipped++; return;
    }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name);
    if (m == null) { m = Model.Tables[table].AddMeasure(name, expr); created++; }
    else { m.Expression = expr; updated++; }
    if (fmt != null) m.FormatString = fmt;
    if (folder != null) m.DisplayFolder = folder;
};

// =====================================================================
// v58 — HOURLY / TIME-GRAIN (home: gold_kpi_hourly)
// =====================================================================
string F58 = "Time Series (v58)";
Upsert("gold_kpi_hourly", "TS Consumption kWh",              @"SUM( gold_kpi_hourly[total_consumption_kwh] )", "#,##0", F58);
Upsert("gold_kpi_hourly", "TS Avg Demand kW",               @"AVERAGE( gold_kpi_hourly[peak_demand_kw] )", "#,##0.0", F58);
Upsert("gold_kpi_hourly", "TS Peak Demand kW",              @"MAX( gold_kpi_hourly[peak_demand_kw] )", "#,##0.0", F58);
Upsert("gold_kpi_hourly", "TS Solar Generated kWh",         @"SUM( gold_kpi_hourly[solar_generated_kwh] )", "#,##0", F58);
Upsert("gold_kpi_hourly", "TS Solar Self-Consumed kWh",     @"SUM( gold_kpi_hourly[solar_self_consumed_kwh] )", "#,##0", F58);
Upsert("gold_kpi_hourly", "TS Net Grid kWh",                @"SUM( gold_kpi_hourly[net_grid_consumption_kwh] )", "#,##0", F58);
Upsert("gold_kpi_hourly", "TS CO2 kg",                      @"SUM( gold_kpi_hourly[co2_emissions_kg] )", "#,##0", F58);
Upsert("gold_kpi_hourly", "TS Avg Temperature C",           @"AVERAGE( gold_kpi_hourly[avg_temperature_c] )", "#,##0.0", F58);
Upsert("gold_kpi_hourly", "TS Battery SoC Pct",             @"AVERAGE( gold_kpi_hourly[battery_soc_avg_pct] )", "#,##0", F58);
Upsert("gold_kpi_hourly", "Profile Avg Demand by Hour kW",      @"AVERAGE( gold_kpi_hourly[peak_demand_kw] )", "#,##0.0", F58);
Upsert("gold_kpi_hourly", "Profile Avg Consumption by Hour kWh",@"AVERAGE( gold_kpi_hourly[total_consumption_kwh] )", "#,##0.0", F58);
Upsert("gold_kpi_hourly", "Profile Avg Solar by Hour kWh",      @"AVERAGE( gold_kpi_hourly[solar_generated_kwh] )", "#,##0.0", F58);
Upsert("gold_kpi_hourly", "Base Load Ratio Pct",
@"VAR _night = CALCULATE( AVERAGE(gold_kpi_hourly[peak_demand_kw]), gold_kpi_hourly[hour] IN {2,3,4} )
VAR _peak = CALCULATE( MAX(gold_kpi_hourly[peak_demand_kw]), gold_kpi_hourly[hour] IN {9,10,11,12,13,14,15,16,17} )
RETURN DIVIDE( _night, _peak )", "0.0%", F58);

// Selected Grain Label needs the 'Time Grain' field parameter (created in PBI UI).
if (Model.Tables.Any(t => t.Name == "Time Grain")) {
    Upsert("gold_kpi_hourly", "Selected Grain Label",
@"VAR _g = SELECTEDVALUE( 'Time Grain'[Time Grain Order], 1 )
RETURN SWITCH( _g, 0, ""Hourly"", 1, ""Daily"", 2, ""Monthly"", ""Daily"" )", null, F58);
} else {
    Output("NOTE: 'Selected Grain Label' skipped — create the 'Time Grain' field parameter (PBI UI) then re-run this script."); skipped++;
}

// =====================================================================
// v57 — PAGE 6 ESG (EPC area-weighted, CRREM S1+2, EU Taxonomy, CSRD readiness)
// =====================================================================
string F57 = "Page 6 ESG (v57)";
Upsert("silver_epc_ratings", "EPC Score Area-Weighted kWh m2",
@"VAR _num = SUMX( silver_epc_ratings, silver_epc_ratings[epc_score_kwh_m2] * RELATED( silver_building_master[conditioned_area_m2] ) )
VAR _den = SUMX( silver_epc_ratings, RELATED( silver_building_master[conditioned_area_m2] ) )
RETURN DIVIDE( _num, _den )", "0.0", F57);
Upsert("silver_epc_ratings", "EPC Class Area-Weighted",
@"VAR _s = [EPC Score Area-Weighted kWh m2]
RETURN SWITCH( TRUE(), ISBLANK(_s), ""—"", _s<=50, ""A"", _s<=100, ""B"", _s<=150, ""C"", _s<=200, ""D"", _s<=250, ""E"", _s<=300, ""F"", ""G"" )", null, F57);
Upsert("gold_ghg_scope", "Carbon Intensity S1S2 kgCO2 m2 yr",
@"VAR _s1s2 = SUMX( gold_ghg_scope, gold_ghg_scope[scope1_total_tco2] + gold_ghg_scope[scope2_location_tco2] )
VAR _area = SUMX( silver_building_master, silver_building_master[conditioned_area_m2] )
RETURN DIVIDE( _s1s2 * 1000, _area )", "0.0", F57);
Upsert("gold_crrem_pathway", "CRREM Pathway 2C kgCO2 m2 yr",
@"AVERAGE( gold_crrem_pathway[pathway_2c_kgco2_m2_yr] )", "0.0", F57);
Upsert("gold_crrem_pathway", "CRREM Stranding Gap S1S2 kgCO2 m2 yr",
@"[Carbon Intensity S1S2 kgCO2 m2 yr] - [CRREM Pathway 2C kgCO2 m2 yr]", "0.0", F57);
Upsert("gold_crrem_pathway", "CRREM Stranding Status",
@"VAR _gap = [CRREM Stranding Gap S1S2 kgCO2 m2 yr]
RETURN SWITCH( TRUE(), ISBLANK(_gap), ""No pathway data"", _gap>0, ""STRANDED — above pathway now"", _gap>-2, ""At risk — within 2 kgCO2/m2"", ""On track"" )", null, F57);
Upsert("gold_compliance_results", "EU Taxonomy Carbon Score",
@"AVERAGE( gold_compliance_results[csrd_score] )", "0.0", F57);
Upsert("gold_ghg_scope", "CSRD Disclosure Readiness Pct",
@"VAR _hasS1    = IF( CALCULATE( SUM(gold_ghg_scope[scope1_total_tco2]) ) > 0, 1, 0 )
VAR _hasS2loc = IF( CALCULATE( SUM(gold_ghg_scope[scope2_location_tco2]) ) > 0, 1, 0 )
VAR _hasS2mkt = IF( CALCULATE( SUM(gold_ghg_scope[scope2_market_tco2]) ) > 0, 1, 0 )
VAR _hasS3    = IF( CALCULATE( SUM(gold_ghg_scope[scope3_estimated_tco2]) ) > 0, 1, 0 )
VAR _hasLineage = 1
RETURN DIVIDE( _hasS1 + _hasS2loc + _hasS2mkt + _hasS3 + _hasLineage, 5 )", "0%", F57);

// =====================================================================
// v59 — PAGE 8 IoT FDD + setpoint compliance (homes: gold_iot_fdd, gold_iot_realtime)
// =====================================================================
string F59 = "IoT FDD (v59)";
Upsert("gold_iot_fdd", "IoT FDD Findings Today",
@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[event_date] = TODAY() )", "#,##0", F59);
Upsert("gold_iot_fdd", "IoT FDD High Today",
@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[severity] = ""High"", gold_iot_fdd[event_date] = TODAY() )", "#,##0", F59);
Upsert("gold_iot_fdd", "IoT FDD Cost Today EUR",
@"CALCULATE( SUM(gold_iot_fdd[cost_eur_estimate]), gold_iot_fdd[event_date] = TODAY() )", "#,##0.00", F59);
Upsert("gold_iot_fdd", "IoT FDD Count by Rule", @"COUNTROWS( gold_iot_fdd )", "#,##0", F59);
Upsert("gold_iot_fdd", "IoT FDD Severity Sort",
@"SWITCH( MAX(gold_iot_fdd[severity]), ""High"", 3, ""Medium"", 2, ""Low"", 1, 0 )", "0", F59);
Upsert("gold_iot_fdd", "IoT FDD Cost Label",
@"VAR _c = SUM(gold_iot_fdd[cost_eur_estimate]) RETURN IF( ISBLANK(_c), ""--"", ""Est. €"" & FORMAT(_c, ""0.00"") )", null, F59);
Upsert("gold_iot_fdd", "IoT C4 Label v59",
@"VAR _faults = [IoT FDD High Today] VAR _cost = [IoT FDD Cost Today EUR]
RETURN IF( _faults = 0 && (_cost = 0 || ISBLANK(_cost)), ""All Clear"", FORMAT(_faults, ""0"") & "" faults — Est. €"" & FORMAT(ROUND(_cost,0), ""0"") & "" today"" )", null, F59);
Upsert("gold_iot_fdd", "IoT C4 Color v59",
@"VAR _f = [IoT FDD High Today] RETURN SWITCH( TRUE(), ISBLANK(_f) || _f = 0, ""#2ECC40"", _f <= 2, ""#FF851B"", ""#FF4136"" )", null, F59);
Upsert("gold_iot_realtime", "IoT Zone Setpoint Compliance Pct",
@"CALCULATE( AVERAGE(gold_iot_realtime[in_setpoint_pct]), gold_iot_realtime[sensor_type] IN {""HVAC_temp"", ""humidity"", ""CO2""} )", "0.0", F59);
Upsert("gold_iot_realtime", "IoT Zone Compliance Display",
@"VAR _p = [IoT Zone Setpoint Compliance Pct] RETURN IF( ISBLANK(_p), ""-- %"", FORMAT(ROUND(_p,0), ""0"") & ""% in setpoint (EN 16798)"" )", null, F59);
Upsert("gold_iot_realtime", "IoT Zone Compliance Color",
@"VAR _p = [IoT Zone Setpoint Compliance Pct] RETURN SWITCH( TRUE(), ISBLANK(_p), ""#AAAAAA"", _p>=90, ""#2ECC40"", _p>=75, ""#FF851B"", ""#FF4136"" )", null, F59);
Upsert("gold_iot_fdd", "IoT Total Cost Today EUR",
@"[IoT FDD Cost Today EUR] + CALCULATE( SUM(gold_iot_realtime[cost_eur_window]), gold_iot_realtime[event_date] = TODAY() )", "#,##0.00", F59);

// =====================================================================
// v60 — PAGE 8 IoT FDD priority / confidence / energy-impact (home: gold_iot_fdd)
// =====================================================================
string F60 = "IoT Priority (v60)";
Upsert("gold_iot_fdd", "IoT FDD Diagnoses Today",
@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[event_date] = TODAY() )", "#,##0", F60);
Upsert("gold_iot_fdd", "IoT FDD Max Priority", @"MAXX( gold_iot_fdd, gold_iot_fdd[priority_score] )", "0", F60);
Upsert("gold_iot_fdd", "IoT FDD Avg Confidence", @"AVERAGE( gold_iot_fdd[confidence] )", "0.00", F60);
Upsert("gold_iot_fdd", "IoT FDD Avg Confidence Pct",
@"VAR _c = [IoT FDD Avg Confidence] RETURN IF( ISBLANK(_c), ""--"", FORMAT(_c, ""0%"") )", null, F60);
Upsert("gold_iot_fdd", "IoT FDD Energy Impact kWh Today",
@"CALCULATE( SUM(gold_iot_fdd[energy_impact_kwh]), gold_iot_fdd[event_date] = TODAY() )", "#,##0.0", F60);
Upsert("gold_iot_fdd", "IoT FDD Row Confidence",
@"VAR _c = SELECTEDVALUE(gold_iot_fdd[confidence]) RETURN IF( ISBLANK(_c), ""--"", FORMAT(_c, ""0%"") )", null, F60);
Upsert("gold_iot_fdd", "IoT FDD Priority Band",
@"VAR _p = SELECTEDVALUE(gold_iot_fdd[priority_score])
RETURN SWITCH( TRUE(), ISBLANK(_p), ""--"", _p>=60, ""Urgent"", _p>=35, ""High"", _p>=20, ""Medium"", ""Low"" )", null, F60);
Upsert("gold_iot_fdd", "IoT FDD Priority Color",
@"VAR _p = SELECTEDVALUE(gold_iot_fdd[priority_score])
RETURN SWITCH( TRUE(), ISBLANK(_p), ""#AAAAAA"", _p>=60, ""#FF4136"", _p>=35, ""#FF851B"", _p>=20, ""#FFDC00"", ""#2ECC40"" )", null, F60);
Upsert("gold_iot_fdd", "IoT FDD Row Cost Label",
@"VAR _c = SELECTEDVALUE(gold_iot_fdd[cost_eur_estimate]) RETURN IF( ISBLANK(_c) || _c = 0, ""--"", ""Est. €"" & FORMAT(_c, ""0.00"") )", null, F60);
Upsert("gold_iot_fdd", "IoT FDD Top Diagnosis",
@"VAR _top = TOPN(1, gold_iot_fdd, gold_iot_fdd[priority_score], DESC)
RETURN CONCATENATEX( _top, gold_iot_fdd[equipment] & "" — "" & gold_iot_fdd[fault_code] & "" ("" & FORMAT(gold_iot_fdd[confidence], ""0%"") & "")"", "", "" )", null, F60);

// =====================================================================
Output("=====================================================");
Output("CONSOLIDATION DONE — created: " + created + " | updated: " + updated + " | skipped: " + skipped);
Output("Next: File → Save (Ctrl+S) to push to the model, then Power BI → Refresh / Recalculate.");
Output("=====================================================");
