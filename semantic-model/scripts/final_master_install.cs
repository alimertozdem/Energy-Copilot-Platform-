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
@"VAR _night = CALCULATE( AVERAGE(gold_kpi_hourly[peak_demand_kw]), gold_kpi_hourly[hour] IN {2,3,4} ) VAR _peak = CALCULATE( MAX(gold_kpi_hourly[peak_demand_kw]), gold_kpi_hourly[hour] IN {9,10,11,12,13,14,15,16,17} ) RETURN DIVIDE( _night, _peak )", "0.0%", F58);

// Selected Grain Label needs the 'Time Grain' field parameter (created in PBI UI).
if (Model.Tables.Any(t => t.Name == "Time Grain")) {
    Upsert("gold_kpi_hourly", "Selected Grain Label",
@"VAR _g = SELECTEDVALUE( 'Time Grain'[Time Grain Order], 1 ) RETURN SWITCH( _g, 0, ""Hourly"", 1, ""Daily"", 2, ""Monthly"", ""Daily"" )", null, F58);
} else {
    Output("NOTE: 'Selected Grain Label' skipped — create the 'Time Grain' field parameter (PBI UI) then re-run this script."); skipped++;
}

// =====================================================================
// v57 — PAGE 6 ESG (EPC area-weighted, CRREM S1+2, EU Taxonomy, CSRD readiness)
// =====================================================================
string F57 = "Page 6 ESG (v57)";
Upsert("silver_epc_ratings", "EPC Score Area-Weighted kWh m2",
@"VAR _num = SUMX( silver_epc_ratings, silver_epc_ratings[epc_score_kwh_m2] * RELATED( silver_building_master[conditioned_area_m2] ) ) VAR _den = SUMX( silver_epc_ratings, RELATED( silver_building_master[conditioned_area_m2] ) ) RETURN DIVIDE( _num, _den )", "0.0", F57);
Upsert("silver_epc_ratings", "EPC Class Area-Weighted",
@"VAR _s = [EPC Score Area-Weighted kWh m2] RETURN SWITCH( TRUE(), ISBLANK(_s), ""—"", _s<=50, ""A"", _s<=100, ""B"", _s<=150, ""C"", _s<=200, ""D"", _s<=250, ""E"", _s<=300, ""F"", ""G"" )", null, F57);
Upsert("gold_ghg_scope", "Carbon Intensity S1S2 kgCO2 m2 yr",
@"VAR _s1s2 = SUMX( gold_ghg_scope, gold_ghg_scope[scope1_total_tco2] + gold_ghg_scope[scope2_location_tco2] ) VAR _area = SUMX( silver_building_master, silver_building_master[conditioned_area_m2] ) RETURN DIVIDE( _s1s2 * 1000, _area )", "0.0", F57);
Upsert("gold_crrem_pathway", "CRREM Pathway 2C kgCO2 m2 yr",
@"AVERAGE( gold_crrem_pathway[pathway_2c_kgco2_m2_yr] )", "0.0", F57);
Upsert("gold_crrem_pathway", "CRREM Stranding Gap S1S2 kgCO2 m2 yr",
@"[Carbon Intensity S1S2 kgCO2 m2 yr] - [CRREM Pathway 2C kgCO2 m2 yr]", "0.0", F57);
Upsert("gold_crrem_pathway", "CRREM Stranding Status",
@"VAR _gap = [CRREM Stranding Gap S1S2 kgCO2 m2 yr] RETURN SWITCH( TRUE(), ISBLANK(_gap), ""No pathway data"", _gap>0, ""STRANDED — above pathway now"", _gap>-2, ""At risk — within 2 kgCO2/m2"", ""On track"" )", null, F57);
Upsert("gold_compliance_results", "EU Taxonomy Carbon Score",
@"AVERAGE( gold_compliance_results[csrd_score] )", "0.0", F57);
Upsert("gold_ghg_scope", "CSRD Disclosure Readiness Pct",
@"VAR _hasS1    = IF( CALCULATE( SUM(gold_ghg_scope[scope1_total_tco2]) ) > 0, 1, 0 ) VAR _hasS2loc = IF( CALCULATE( SUM(gold_ghg_scope[scope2_location_tco2]) ) > 0, 1, 0 ) VAR _hasS2mkt = IF( CALCULATE( SUM(gold_ghg_scope[scope2_market_tco2]) ) > 0, 1, 0 ) VAR _hasS3    = IF( CALCULATE( SUM(gold_ghg_scope[scope3_estimated_tco2]) ) > 0, 1, 0 ) VAR _hasLineage = 1 RETURN DIVIDE( _hasS1 + _hasS2loc + _hasS2mkt + _hasS3 + _hasLineage, 5 )", "0%", F57);

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
@"VAR _faults = [IoT FDD High Today] VAR _cost = [IoT FDD Cost Today EUR] RETURN IF( _faults = 0 && (_cost = 0 || ISBLANK(_cost)), ""All Clear"", FORMAT(_faults, ""0"") & "" faults — Est. €"" & FORMAT(ROUND(_cost,0), ""0"") & "" today"" )", null, F59);
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
@"VAR _p = SELECTEDVALUE(gold_iot_fdd[priority_score]) RETURN SWITCH( TRUE(), ISBLANK(_p), ""--"", _p>=60, ""Urgent"", _p>=35, ""High"", _p>=20, ""Medium"", ""Low"" )", null, F60);
Upsert("gold_iot_fdd", "IoT FDD Priority Color",
@"VAR _p = SELECTEDVALUE(gold_iot_fdd[priority_score]) RETURN SWITCH( TRUE(), ISBLANK(_p), ""#AAAAAA"", _p>=60, ""#FF4136"", _p>=35, ""#FF851B"", _p>=20, ""#FFDC00"", ""#2ECC40"" )", null, F60);
Upsert("gold_iot_fdd", "IoT FDD Row Cost Label",
@"VAR _c = SELECTEDVALUE(gold_iot_fdd[cost_eur_estimate]) RETURN IF( ISBLANK(_c) || _c = 0, ""--"", ""Est. €"" & FORMAT(_c, ""0.00"") )", null, F60);
Upsert("gold_iot_fdd", "IoT FDD Top Diagnosis",
@"VAR _top = TOPN(1, gold_iot_fdd, gold_iot_fdd[priority_score], DESC) RETURN CONCATENATEX( _top, gold_iot_fdd[equipment] & "" — "" & gold_iot_fdd[fault_code] & "" ("" & FORMAT(gold_iot_fdd[confidence], ""0%"") & "")"", "", "" )", null, F60);


// =====================================================================
// PAGE 10 (SOLAR) + GATE-D FIXES — master add-on (2026-06-03)
// Appended to the v57-v60 consolidation so this ONE file installs everything.
// =====================================================================
string F10 = "Solar - Realtime & Opportunity";
Upsert("gold_iot_realtime", "Realtime PV Power kW",
@"CALCULATE( AVERAGE( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[sensor_type] = ""pv_ac_power"" )", "#,##0.0", F10);
Upsert("gold_iot_realtime", "Peak PV Power kW",
@"CALCULATE( MAX( gold_iot_realtime[reading_value_max] ), gold_iot_realtime[sensor_type] = ""pv_ac_power"" )", "#,##0.0", F10);
Upsert("gold_iot_fdd", "PV Underperformance Count",
@"CALCULATE( COUNTROWS( gold_iot_fdd ), gold_iot_fdd[fault_code] = ""PV_UNDERPERFORMANCE"" )", "#,##0", F10);
Upsert("gold_iot_fdd", "PV Loss EUR",
@"CALCULATE( SUM( gold_iot_fdd[cost_eur_estimate] ), gold_iot_fdd[fault_code] = ""PV_UNDERPERFORMANCE"" )", "#,##0", F10);
Upsert("silver_building_master", "Solar Capacity kWp",
@"SUM( silver_building_master[pv_capacity_kwp] )", "#,##0", F10);
Upsert("gold_recommendations", "INSTALL_SOLAR Opportunities",
@"CALCULATE( COUNTROWS( gold_recommendations ), gold_recommendations[action_type] = ""INSTALL_SOLAR"" )", "#,##0", F10);
Upsert("gold_kpi_daily", "Avg Solar Specific Yield kWh kWp",
@"AVERAGEX( VALUES( gold_kpi_daily[building_id] ), DIVIDE( CALCULATE( SUM( gold_kpi_daily[solar_generated_kwh] ) ), CALCULATE( MAX( gold_kpi_daily[pv_capacity_kwp] ) ) ) )", "#,##0.0", F10);

// Fix -- climate-adjusted EUI (old 'Avg HDD Normalized EUI' referenced the renamed column)
string FE = "Energy KPIs";
Upsert("gold_kpi_daily", "Avg HDD Normalized EUI", @"AVERAGE( gold_kpi_daily[climate_adjusted_eui] )", "#,##0.00", FE);
Upsert("gold_kpi_daily", "Avg Climate-Adjusted EUI", @"AVERAGE( gold_kpi_daily[climate_adjusted_eui] )", "#,##0.00", FE);

// Page 4 -- forecast band measures (gold_consumption_forecast had 0 measures)
string F4 = "Forecast (Page 4)";
Upsert("gold_consumption_forecast", "Forecast Predicted kWh", @"SUM( gold_consumption_forecast[predicted_kwh] )", "#,##0", F4);
Upsert("gold_consumption_forecast", "Forecast Lower Bound kWh", @"SUM( gold_consumption_forecast[lower_bound_kwh] )", "#,##0", F4);
Upsert("gold_consumption_forecast", "Forecast Upper Bound kWh", @"SUM( gold_consumption_forecast[upper_bound_kwh] )", "#,##0", F4);

// Page 9 -- Round Trip Efficiency shows 0.9 (fraction). Display as percent.
if (Model.Tables.Any(t => t.Name == "gold_battery_dispatch")) {
    Upsert("gold_battery_dispatch", "C4 Round Trip Efficiency Pct",
@"AVERAGE( gold_battery_dispatch[round_trip_efficiency] ) * 100", "0.0", null);
}

// Page 3 -- P3 Anomaly Status: old measure used MAX() on Boolean is_resolved -> error.
//   Count-based (no MAX); works per-row (table) and aggregated (card).
if (Model.Tables.Any(t => t.Name == "gold_anomaly_log")) {
    Upsert("gold_anomaly_log", "P3 Anomaly Status",
@"VAR _open = CALCULATE( COUNTROWS( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE() ) VAR _tot = COUNTROWS( gold_anomaly_log ) RETURN SWITCH( TRUE(), _tot = 0, ""--"", _open > 0, ""Open"", ""Resolved"" )", null, null);
}

// =====================================================================
// CLEANUP -- silinmis tablolardaki oksuz olculeri sil + canli tablolara yeniden kur
//   (Missing_References: iot_hot_readings, gold_battery_hourly_profile)
// =====================================================================
System.Action<string> DelAll = (nm) => {
// SWEEP: silinmis tablolardaki TUM olculeri sil (isim tek tek degil) -> tum Missing_References temizlenir
foreach (var orphanTbl in new string[]{"iot_hot_readings","gold_battery_hourly_profile"}) {
    var ot = Model.Tables.FirstOrDefault(x => x.Name == orphanTbl);
    if (ot != null) {
        foreach (var m in ot.Measures.ToList()) { Output("swept: "+orphanTbl+"."+m.Name); m.Delete(); }
        try { ot.Delete(); Output("dropped orphan table: "+orphanTbl); } catch (System.Exception e) { Output("kept table (measures swept): "+orphanTbl); }
    }
}
    foreach(var mm in Model.AllMeasures.Where(x => x.Name == nm).ToList()) { mm.Delete(); Output("deleted: "+nm); }
};

// Page 9 -- V6 (dropped gold_battery_hourly_profile) -> gold_battery_hourly_dispatch
DelAll("V6 Charge Rate"); DelAll("V6 Discharge Rate"); DelAll("V6 SoC Pct"); DelAll("V6 Price Index");
if (Model.Tables.Any(t => t.Name == "gold_battery_hourly_dispatch")) {
    string FV6 = "Battery 24h (V6)";
    Upsert("gold_battery_hourly_dispatch","V6 Charge Rate",@"SUM( gold_battery_hourly_dispatch[charge_kwh] )","#,##0.0",FV6);
    Upsert("gold_battery_hourly_dispatch","V6 Discharge Rate",@"SUM( gold_battery_hourly_dispatch[discharge_kwh] )","#,##0.0",FV6);
    Upsert("gold_battery_hourly_dispatch","V6 SoC Pct",@"AVERAGE( gold_battery_hourly_dispatch[soc_percent] )","0.0",FV6);
    Upsert("gold_battery_hourly_dispatch","V6 Price Index",@"AVERAGE( gold_battery_hourly_dispatch[grid_price_index] )","0.00",FV6);
}

// Page 7/8 -- V2 uptime + IoT CO2 (dropped iot_hot_readings) -> gold_iot_daily_summary / gold_iot_realtime
DelAll("V2_Sensor_Uptime_Pct"); DelAll("V2_Uptime_Color_Index"); DelAll("IoT_CO2_Live");
if (Model.Tables.Any(t => t.Name == "gold_iot_daily_summary")) {
    string FV2 = "IoT Uptime (V2)";
    Upsert("gold_iot_daily_summary","V2 Sensor Uptime Pct",@"AVERAGE( gold_iot_daily_summary[sensor_uptime_pct] )","0.0",FV2);
    Upsert("gold_iot_daily_summary","V2 Uptime Color Index",@"VAR u=[V2 Sensor Uptime Pct] RETURN SWITCH(TRUE(), ISBLANK(u),""#AAAAAA"", u>=95,""#2ECC40"", u>=85,""#FF851B"", ""#FF4136"")",null,FV2);
}
if (Model.Tables.Any(t => t.Name == "gold_iot_realtime")) {
    Upsert("gold_iot_realtime","IoT CO2 Live",@"CALCULATE( AVERAGE(gold_iot_realtime[reading_value_avg]), gold_iot_realtime[sensor_type]=""CO2"" )","#,##0","IoT (v59)");
}

// Page 10 -- Avg Solar Specific Yield isim cakismasi -> tekille + yeniden kur
DelAll("Avg Solar Specific Yield kWh kWp");
Upsert("gold_kpi_daily","Avg Solar Specific Yield kWh kWp",@"AVERAGEX( VALUES( gold_kpi_daily[building_id] ), DIVIDE( CALCULATE( SUM( gold_kpi_daily[solar_generated_kwh] ) ), CALCULATE( MAX( gold_kpi_daily[pv_capacity_kwp] ) ) ) )","#,##0.0","Solar - Realtime & Opportunity");

// Page 9 -- RTE kesir/yuzde belirsiz -> ~90'a normalize
if (Model.Tables.Any(t => t.Name == "gold_battery_dispatch")) {
    Upsert("gold_battery_dispatch","C4 Round Trip Efficiency Pct",@"VAR r = AVERAGE( gold_battery_dispatch[round_trip_efficiency] ) RETURN IF( r <= 1.5, r * 100, r )","0.0",null);
}

// Page 6 -- CRREM Pathway hep ayni (83.7) -> bina tipi + referans yil
if (Model.Tables.Any(t => t.Name == "gold_crrem_pathway")) {
    Upsert("gold_crrem_pathway","CRREM Pathway 2C kgCO2 m2 yr",@"VAR bt = SELECTEDVALUE( silver_building_master[building_type] ) RETURN CALCULATE( AVERAGE( gold_crrem_pathway[pathway_2c_kgco2_m2_yr] ), gold_crrem_pathway[building_type] = bt, gold_crrem_pathway[pathway_year] = YEAR( TODAY() ) )","0.0",null);
}

// Page 8 -- C1 Realtime Building Power (sensor_type DOGRULA: varsayim 'building_kwh')
if (Model.Tables.Any(t => t.Name == "gold_iot_realtime")) {
    Upsert("gold_iot_realtime","Realtime Building Power kW",@"CALCULATE( AVERAGE(gold_iot_realtime[reading_value_avg]), gold_iot_realtime[sensor_type]=""building_kwh"" )","#,##0.0","IoT (v59)");
}
// Page 10 -- Feed-in Tariff (ulke lookup, ham sutun yerine olcu)
if (Model.Tables.Any(t => t.Name == "gold_country_regulations") && Model.Tables.Any(t => t.Name == "gold_recommendations")) {
    Upsert("gold_recommendations","Feed-in Tariff EUR kWh",@"LOOKUPVALUE( gold_country_regulations[feed_in_tariff_eur_per_kwh], gold_country_regulations[country_code], SELECTEDVALUE(gold_recommendations[country_code]) )","0.000","Solar - Realtime & Opportunity");
}

// Page 7 -- eski 2 IoT kartinin yerine HVAC-yerel kartlar (gold_hvac_analytics 0-olcu)
if (Model.Tables.Any(t => t.Name == "gold_hvac_analytics")) {
    string FH = "HVAC (Page 7)";
    Upsert("gold_hvac_analytics","HVAC Avg COP",@"AVERAGE( gold_hvac_analytics[cop_actual_avg] )","0.0",FH);
    Upsert("gold_hvac_analytics","HVAC Ventilation Share Pct",@"DIVIDE( SUM(gold_hvac_analytics[ventilation_kwh]), SUM(gold_hvac_analytics[hvac_total_kwh]) )","0.0%",FH);
}

// OPTIONAL -- compact 'Month Year' axis label on 'Date' (e.g. "Jan 2024") for multi-year trends.
try {
    var dt = Model.Tables["Date"];
    if (dt != null && !dt.Columns.Any(c => c.Name == "Month Year")) {
        var cc = dt.AddCalculatedColumn("Month Year", @"FORMAT( 'Date'[Date], ""MMM yyyy"", ""en-US"" )");
        if (dt.Columns.Any(c => c.Name == "YearMonth")) cc.SortByColumn = dt.Columns["YearMonth"];
        Output("Added calculated column 'Date'[Month Year] (sorted by YearMonth).");
    }
} catch (System.Exception ex) { Output("Month Year column skipped: " + ex.Message); }

Output("=====================================================");
Output("MASTER INSTALL DONE -- created: " + created + " | updated: " + updated + " | skipped: " + skipped);
Output("Save (Ctrl+S) -> Power BI Refresh. Re-run 03 first if specific-yield was skipped.");
Output("=====================================================");
