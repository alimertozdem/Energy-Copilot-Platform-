// =====================================================================
// EnergyLens — PAGE 8 (Real-Time IoT) — FINAL CONSOLIDATED INSTALL
// Tabular Editor 2 → C# Script tab. PREFER: File → Open (the folder icon)
//   and pick this file from disk, then F5. (Pasting long lines can truncate
//   them → "CS1513 } expected". Open-from-disk avoids that.)
// After F5: Ctrl+S → Power BI Desktop → Refresh.
// ---------------------------------------------------------------------
// WHAT THIS DOES (idempotent — safe to re-run):
//   1. SWEEP: deletes every orphan measure left on the removed tables
//      (iot_hot_readings, iot_anomaly_alerts, gold_battery_hourly_profile)
//      and on any 0-column table → clears all "Missing_References" errors
//      (e.g. the C1_Building_kW_Color error in your screenshot). Then it
//      tries to drop those dead tables from the model.
//   2. INSTALL: create-or-update the FINAL Page 8 measure set on the LIVE
//      tables, verified against semantic-model/_probe_output.txt:
//        - gold_iot_realtime  (C1 power, C2 compliance, C3 CO2, V1 series)
//        - gold_iot_fdd       (C4 faults, FDD cards, V5 table helpers)
//        - gold_iot_daily_summary (V2 uptime)
//   sensor_type literals confirmed from notebooks/iot/11b_iot_processing.py:
//     building_kwh, hvac_kwh, HVAC_temp, humidity, CO2.
// =====================================================================

int created = 0, updated = 0, swept = 0;
string F = "IoT (Page 8)";

// create-or-update one measure (single-line DAX, paste-safe)
System.Action<string,string,string,string> U = (tbl, nm, ex, fmt) => {
    if (!Model.Tables.Any(t => t.Name == tbl)) { Output("SKIP (no table '" + tbl + "'): " + nm); return; }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == nm);
    if (m == null) { m = Model.Tables[tbl].AddMeasure(nm, ex); created++; }
    else { m.Expression = ex; updated++; }
    if (fmt != null) m.FormatString = fmt;
    m.DisplayFolder = F;
};

// ── STEP 1 — SWEEP ORPHANS (clears Missing_References) ───────────────
foreach (var deadTbl in new string[]{ "iot_hot_readings", "iot_anomaly_alerts", "gold_battery_hourly_profile" }) {
    var t = Model.Tables.FirstOrDefault(x => x.Name == deadTbl);
    if (t == null) { Output("clean (table absent): " + deadTbl); continue; }
    foreach (var m in t.Measures.ToList()) { Output("swept: " + deadTbl + "." + m.Name); m.Delete(); swept++; }
    try { t.Delete(); Output("dropped dead table: " + deadTbl); }
    catch (System.Exception e) { Output("kept table (measures swept): " + deadTbl + " — remove it via Power BI model view if it lingers"); }
}
// catch-all: any measure stranded on a 0-column (broken) table
foreach (var m in Model.AllMeasures.ToList()) {
    if (m.Table != null && m.Table.Columns.Count == 0) { Output("swept orphan: " + m.Table.Name + "." + m.Name); m.Delete(); swept++; }
}

// ── STEP 2 — INSTALL FINAL PAGE 8 MEASURES ───────────────────────────

// --- C1: Real-Time Building Power (kW) vs baseline ------------------
U("gold_iot_realtime","Realtime Building Power kW",@"CALCULATE( AVERAGE(gold_iot_realtime[reading_value_avg]), gold_iot_realtime[sensor_type]=""building_kwh"" )","#,##0.0");
U("gold_iot_realtime","Realtime Building Baseline kW",@"CALCULATE( AVERAGE(gold_iot_realtime[baseline_value]), gold_iot_realtime[sensor_type]=""building_kwh"" )","#,##0.0");
U("gold_iot_realtime","C1 Building Power Display",@"VAR p=[Realtime Building Power kW] RETURN IF( ISBLANK(p), ""-- kW"", FORMAT(p,""#,##0.0"") & "" kW"" )",null);
U("gold_iot_realtime","C1 Building Power Color",@"VAR p=[Realtime Building Power kW] VAR b=[Realtime Building Baseline kW] RETURN SWITCH( TRUE(), ISBLANK(p),""#AAAAAA"", b>0 && p>b*1.2,""#FF4136"", b>0 && p>b*1.05,""#FF851B"", ""#2ECC40"" )",null);

// --- C2: Zone Comfort Compliance % (EN 16798) ----------------------
U("gold_iot_realtime","IoT Zone Setpoint Compliance Pct",@"CALCULATE( AVERAGE(gold_iot_realtime[in_setpoint_pct]), gold_iot_realtime[sensor_type] IN {""HVAC_temp"",""humidity"",""CO2""} )","0.0");
U("gold_iot_realtime","IoT Zone Compliance Display",@"VAR p=[IoT Zone Setpoint Compliance Pct] RETURN IF( ISBLANK(p), ""-- %"", FORMAT(ROUND(p,0),""0"") & ""% in setpoint (EN 16798)"" )",null);
U("gold_iot_realtime","IoT Zone Compliance Color",@"VAR p=[IoT Zone Setpoint Compliance Pct] RETURN SWITCH( TRUE(), ISBLANK(p),""#AAAAAA"", p>=90,""#2ECC40"", p>=75,""#FF851B"", ""#FF4136"" )",null);

// --- C3: Indoor Air Quality — CO2 (ppm) ----------------------------
U("gold_iot_realtime","IoT CO2 Live",@"CALCULATE( AVERAGE(gold_iot_realtime[reading_value_avg]), gold_iot_realtime[sensor_type]=""CO2"" )","#,##0");
U("gold_iot_realtime","IoT CO2 Display",@"VAR c=[IoT CO2 Live] RETURN SWITCH( TRUE(), ISBLANK(c),""--"", c<800, ""Good "" & FORMAT(c,""0"") & "" ppm"", c<=1200, ""Fair "" & FORMAT(c,""0"") & "" ppm"", ""Poor "" & FORMAT(c,""0"") & "" ppm"" )",null);
U("gold_iot_realtime","IoT CO2 Color",@"VAR c=[IoT CO2 Live] RETURN SWITCH( TRUE(), ISBLANK(c),""#AAAAAA"", c<800,""#2ECC40"", c<=1200,""#FF851B"", ""#FF4136"" )",null);

// --- C4: Active High Faults + Estimated € cost ---------------------
U("gold_iot_fdd","IoT FDD High Today",@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[severity]=""High"", gold_iot_fdd[event_date]=TODAY() )","#,##0");
U("gold_iot_fdd","IoT FDD Cost Today EUR",@"CALCULATE( SUM(gold_iot_fdd[cost_eur_estimate]), gold_iot_fdd[event_date]=TODAY() )","#,##0.00");
U("gold_iot_fdd","IoT C4 Label v59",@"VAR f=[IoT FDD High Today] VAR c=[IoT FDD Cost Today EUR] RETURN IF( f=0 && (c=0 || ISBLANK(c)), ""All Clear"", FORMAT(f,""0"") & "" faults - Est. EUR "" & FORMAT(ROUND(c,0),""0"") & "" today"" )",null);
U("gold_iot_fdd","IoT C4 Color v59",@"VAR f=[IoT FDD High Today] RETURN SWITCH( TRUE(), ISBLANK(f) || f=0,""#2ECC40"", f<=2,""#FF851B"", ""#FF4136"" )",null);

// --- FDD top-line summary cards ------------------------------------
U("gold_iot_fdd","IoT FDD Diagnoses Today",@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[event_date]=TODAY() )","#,##0");
U("gold_iot_fdd","IoT FDD Max Priority",@"MAXX( gold_iot_fdd, gold_iot_fdd[priority_score] )","0");
U("gold_iot_fdd","IoT FDD Avg Confidence",@"AVERAGE( gold_iot_fdd[confidence] )","0.00");
U("gold_iot_fdd","IoT FDD Avg Confidence Pct",@"VAR c=[IoT FDD Avg Confidence] RETURN IF( ISBLANK(c), ""--"", FORMAT(c,""0%"") )",null);
U("gold_iot_fdd","IoT FDD Energy Impact kWh Today",@"CALCULATE( SUM(gold_iot_fdd[energy_impact_kwh]), gold_iot_fdd[event_date]=TODAY() )","#,##0.0");

// --- V5 "FDD Findings" table — row-level helpers (sort by priority_score DESC) ---
U("gold_iot_fdd","IoT FDD Priority Band",@"VAR p=SELECTEDVALUE(gold_iot_fdd[priority_score]) RETURN SWITCH( TRUE(), ISBLANK(p),""--"", p>=60,""Urgent"", p>=35,""High"", p>=20,""Medium"", ""Low"" )",null);
U("gold_iot_fdd","IoT FDD Priority Color",@"VAR p=SELECTEDVALUE(gold_iot_fdd[priority_score]) RETURN SWITCH( TRUE(), ISBLANK(p),""#AAAAAA"", p>=60,""#FF4136"", p>=35,""#FF851B"", p>=20,""#FFDC00"", ""#2ECC40"" )",null);
U("gold_iot_fdd","IoT FDD Row Confidence",@"VAR c=SELECTEDVALUE(gold_iot_fdd[confidence]) RETURN IF( ISBLANK(c), ""--"", FORMAT(c,""0%"") )",null);
U("gold_iot_fdd","IoT FDD Row Cost Label",@"VAR c=SELECTEDVALUE(gold_iot_fdd[cost_eur_estimate]) RETURN IF( ISBLANK(c) || c=0, ""--"", ""Est. EUR "" & FORMAT(c,""0.00"") )",null);

// --- V1 "Building & HVAC Power — Last 24h" trend series ------------
//     X-axis = gold_iot_realtime[hour_bucket]; series below + Realtime Building Power kW + Realtime Building Baseline kW
U("gold_iot_realtime","V1 HVAC Power kW",@"CALCULATE( AVERAGE(gold_iot_realtime[reading_value_avg]), gold_iot_realtime[sensor_type]=""hvac_kwh"" )","#,##0.0");

// --- V2 Sensor Uptime matrix --------------------------------------
U("gold_iot_daily_summary","V2 Sensor Uptime Pct",@"AVERAGE( gold_iot_daily_summary[sensor_uptime_pct] )","0.0");
U("gold_iot_daily_summary","V2 Uptime Color Index",@"VAR u=[V2 Sensor Uptime Pct] RETURN SWITCH( TRUE(), ISBLANK(u),""#AAAAAA"", u>=95,""#2ECC40"", u>=85,""#FF851B"", ""#FF4136"" )",null);

Output("=====================================================");
Output("PAGE 8 FINAL INSTALL DONE — swept: " + swept + " | created: " + created + " | updated: " + updated);
Output("All Page 8 measures now live under display folder: '" + F + "'.");
Output("Ctrl+S -> Power BI Refresh -> then rebind visuals per page8-FINAL-rebind-guide.md");
Output("=====================================================");
