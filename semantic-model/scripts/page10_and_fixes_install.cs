// =====================================================================
// EnergyLens — PAGE 10 (SOLAR) + GATE-D FIXES — Tabular Editor 2 installer
// Run in Tabular Editor 2: C# Script tab -> F5, then Model -> Refresh.
// Idempotent create-or-update into the correct home table. Safe to re-run.
// Built against the live probe schema (semantic-model/_probe_output.txt).
//
// Covers:
//   1) Page 10 Solar measures — CORRECTED (silver_building_master, not dim_building)
//   2) Fix 3 — climate-adjusted EUI (old 'Avg HDD Normalized EUI' pointed at the
//      dropped column hdd_normalized_eui -> repointed + clean-named measure added)
//   3) Page 4 — forecast band measures (gold_consumption_forecast had 0 measures)
//   4) Selected Grain Label — only if the 'Time Grain' field parameter exists
//   5) OPTIONAL — 'Date'[Month Year] compact axis label for multi-year trends
//
// PRE-REQ: re-run 03_gold_kpi_engine first so gold_kpi_daily has
//   solar_specific_yield_kwh_kwp; otherwise measure #7 is skipped (not broken).
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

// ---------------------------------------------------------------------
// 1) PAGE 10 — SOLAR. dim_building -> silver_building_master (real model dim).
// ---------------------------------------------------------------------
string F10 = "Solar - Realtime & Opportunity";

Upsert("gold_iot_realtime", "Realtime PV Power kW",
@"CALCULATE( AVERAGE( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[sensor_type] = ""pv_ac_power"" )", "#,##0.0", F10);

Upsert("gold_iot_realtime", "Peak PV Power kW",
@"CALCULATE( MAX( gold_iot_realtime[reading_value_max] ), gold_iot_realtime[sensor_type] = ""pv_ac_power"" )", "#,##0.0", F10);

Upsert("gold_iot_fdd", "PV Underperformance Count",
@"CALCULATE( COUNTROWS( gold_iot_fdd ), gold_iot_fdd[fault_code] = ""PV_UNDERPERFORMANCE"" )", "#,##0", F10);

Upsert("gold_iot_fdd", "PV Loss EUR",
@"CALCULATE( SUM( gold_iot_fdd[cost_eur_estimate] ), gold_iot_fdd[fault_code] = ""PV_UNDERPERFORMANCE"" )", "#,##0", F10);

// Installed nameplate across the filtered portfolio (was SUM(dim_building[...])).
Upsert("silver_building_master", "Solar Capacity kWp",
@"SUM( silver_building_master[pv_capacity_kwp] )", "#,##0", F10);

Upsert("gold_recommendations", "INSTALL_SOLAR Opportunities",
@"CALCULATE( COUNTROWS( gold_recommendations ), gold_recommendations[action_type] = ""INSTALL_SOLAR"" )", "#,##0", F10);

// Specific yield — needs the daily column from the 03 re-run. Guard so we don't
// create a broken measure before the column lands.
if (Model.Tables["gold_kpi_daily"].Columns.Any(c => c.Name == "solar_specific_yield_kwh_kwp")) {
    Upsert("gold_kpi_daily", "Avg Solar Specific Yield kWh kWp",
@"AVERAGEX( FILTER( gold_kpi_daily, NOT ISBLANK( gold_kpi_daily[solar_specific_yield_kwh_kwp] ) ), gold_kpi_daily[solar_specific_yield_kwh_kwp] )", "#,##0.0", F10);
} else {
    Output("SKIP 'Avg Solar Specific Yield kWh kWp' — re-run 03_gold_kpi_engine first (daily column missing)."); skipped++;
}

// ---------------------------------------------------------------------
// 2) FIX 3 — climate-adjusted EUI. Old measure referenced renamed column.
// ---------------------------------------------------------------------
string FE = "Energy KPIs";
Upsert("gold_kpi_daily", "Avg HDD Normalized EUI",
@"AVERAGE( gold_kpi_daily[climate_adjusted_eui] )", "#,##0.0", FE);   // repoint so existing visuals keep working
Upsert("gold_kpi_daily", "Avg Climate-Adjusted EUI",
@"AVERAGE( gold_kpi_daily[climate_adjusted_eui] )", "#,##0.0", FE);   // correctly named

// ---------------------------------------------------------------------
// 3) PAGE 4 — forecast band measures (so you can shade the confidence band).
// ---------------------------------------------------------------------
string F4 = "Forecast (Page 4)";
Upsert("gold_consumption_forecast", "Forecast Predicted kWh",
@"SUM( gold_consumption_forecast[predicted_kwh] )", "#,##0", F4);
Upsert("gold_consumption_forecast", "Forecast Lower Bound kWh",
@"SUM( gold_consumption_forecast[lower_bound_kwh] )", "#,##0", F4);
Upsert("gold_consumption_forecast", "Forecast Upper Bound kWh",
@"SUM( gold_consumption_forecast[upper_bound_kwh] )", "#,##0", F4);

// ---------------------------------------------------------------------
// 4) Selected Grain Label — needs the 'Time Grain' field parameter (PBI UI).
// ---------------------------------------------------------------------
if (Model.Tables.Any(t => t.Name == "Time Grain")) {
    Upsert("gold_kpi_hourly", "Selected Grain Label",
@"VAR _g = SELECTEDVALUE( 'Time Grain'[Time Grain Order], 1 )
RETURN SWITCH( _g, 0, ""Hourly"", 1, ""Daily"", 2, ""Monthly"", ""Daily"" )", null, "Time Series (v58)");
} else {
    Output("NOTE: 'Selected Grain Label' skipped — create the 'Time Grain' field parameter (PBI UI) then re-run."); skipped++;
}

// ---------------------------------------------------------------------
// 5) OPTIONAL — compact 'Month Year' axis label on 'Date' (e.g. "Jan 2024").
//    Use it (or Date[YearMonth]) on multi-year trend axes instead of
//    Date[Date] for a readable monthly curve. Comment out if unwanted.
// ---------------------------------------------------------------------
try {
    var dt = Model.Tables["Date"];
    if (dt != null && !dt.Columns.Any(c => c.Name == "Month Year")) {
        var cc = dt.AddCalculatedColumn("Month Year", @"FORMAT( 'Date'[Date], ""mmm yyyy"" )");
        if (dt.Columns.Any(c => c.Name == "YearMonth"))
            cc.SortByColumn = dt.Columns["YearMonth"];   // "2024-01" sorts chronologically
        Output("Added calculated column 'Date'[Month Year] (sorted by YearMonth).");
    }
} catch (System.Exception ex) { Output("Month Year column skipped: " + ex.Message); }

Output(string.Format("DONE — created {0}, updated {1}, skipped {2}. Now Model -> Refresh.", created, updated, skipped));
