// =====================================================================
// EnergyLens — PAGE 8 · replace "Sensor Uptime matrix" with
//   (A) Zone Comfort heatmap  +  (B) compact Sensor Health strip
// TE2 → C# Script → (File → Open this file) → F5 → Ctrl+S → PBI Refresh.
// ---------------------------------------------------------------------
// WHY: the old matrix was a date×sensor grid of "uptime", but
//   - the IoT tables are a rolling window (always ~2-3 days) → date axis is wrong;
//   - sensor_uptime_pct in 11b is round(avg(reading_quality)) → it's DATA QUALITY,
//     not true device uptime. So we stop calling it "uptime".
//
// (A) Zone Comfort heatmap (home: gold_iot_realtime)
//     matrix rows = sensor_location, cols = sensor_type (filter to HVAC_temp/
//     humidity/CO2), value = % of readings within setpoint → muted gradient.
//     Answers "which zone is uncomfortable", and it deepens C2.
// (B) Sensor Health strip (homes: gold_iot_daily_summary / gold_iot_realtime)
//     3 small cards: Data Quality %, Active Sensors, Anomaly Rate % (latest day).
//     Honest data-trust indicator, tiny footprint.
// =====================================================================

int n = 0;
string F = "IoT (Page 8)";
System.Action<string,string,string,string> U = (tbl, nm, ex, fmt) => {
    if (!Model.Tables.Any(t => t.Name == tbl)) { Output("SKIP (no table '" + tbl + "'): " + nm); return; }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == nm);
    if (m == null) m = Model.Tables[tbl].AddMeasure(nm, ex); else m.Expression = ex;
    if (fmt != null) m.FormatString = fmt;
    m.DisplayFolder = F; n++; Output("ok: " + nm);
};

// (A) Zone Comfort heatmap — cell = avg % of readings in setpoint for that
//     location × sensor_type (matrix context supplies both). Color via gradient.
U("gold_iot_realtime","Zone Comfort Cell Pct",@"AVERAGE( gold_iot_realtime[in_setpoint_pct] )","0.0");

// (B) Sensor Health strip — latest day, honest labels.
U("gold_iot_daily_summary","Data Quality Pct",@"VAR d=MAX(gold_iot_daily_summary[event_date]) RETURN CALCULATE( AVERAGE(gold_iot_daily_summary[sensor_uptime_pct]), gold_iot_daily_summary[event_date]=d )","0.0");
U("gold_iot_daily_summary","Sensor Anomaly Rate Pct",@"VAR d=MAX(gold_iot_daily_summary[event_date]) RETURN CALCULATE( AVERAGE(gold_iot_daily_summary[anomaly_rate_pct]), gold_iot_daily_summary[event_date]=d )","0.0");
U("gold_iot_realtime","Active Sensor Locations",@"DISTINCTCOUNT( gold_iot_realtime[sensor_location] )","#,##0");

// Optional display helpers (if you want text + color on the strip cards)
U("gold_iot_daily_summary","Data Quality Display",@"VAR q=[Data Quality Pct] RETURN IF( ISBLANK(q), ""--"", FORMAT(q,""0.0"") & ""% data quality"" )",null);
U("gold_iot_daily_summary","Data Quality Color",@"VAR q=[Data Quality Pct] RETURN SWITCH( TRUE(), ISBLANK(q),""#AAAAAA"", q>=95,""#2ECC40"", q>=85,""#FF851B"", ""#FF4136"" )",null);

Output("=====================================================");
Output("SENSOR HEALTH / ZONE COMFORT — measures ready: " + n);
Output("Ctrl+S -> Refresh. Rebind the old matrix per the guide §7 (updated).");
Output("=====================================================");
