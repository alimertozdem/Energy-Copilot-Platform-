// page8_fixpack_2026_06_21_v2.csx
// Tabular Editor 2 - Advanced Scripting (C# Script tab). NO LINQ. Idempotent.
//
// FOLLOW-UP to page8_fixpack_2026_06_21.csx. The v1 "latest snapshot" anchor used
// _t = MAX(gold_iot_realtime[timestamp]) computed across ALL sensor types, then
// filtered to one sensor_type at that exact timestamp. The sensor streams are NOT
// perfectly time-aligned: the global last timestamp (05 Jun 06:00) belongs to CO2,
// but building_kwh has no row at that exact instant -> the C1 card returned BLANK
// ("-- kW") and the "Latest Day" power chart (same measures) went empty.
//
// FIX: anchor _t to the latest timestamp OF EACH MEASURE'S OWN sensor_type:
//   VAR _t = CALCULATE ( MAX(timestamp), sensor_type = "<type>" )
// This fixes BOTH the card and the trend chart with no PBI rebinding (in the chart's
// hour_bucket context, _t becomes the last 15-min reading of each hour for that type).
// Still LIVE-READY: when streaming is on, _t = the most recent reading = now.
//
// Also sets Zone Comfort Cell Pct format to 0.0 (matrix was showing 58.33333...).
//
// HOW TO RUN: External Tools -> Tabular Editor -> C# Script -> paste -> Run (F5) ->
//   Save -> publish. Then re-screenshot Page 8 (All + B009).

// ---- 1) UPDATE snapshot measures to per-sensor-type latest anchor ----------------
string[] upNames = new string[] {
    "Realtime Building Power kW",
    "V1 HVAC Power kW",
    "Realtime Building Baseline kW",
    "IoT CO2 Live",
    "Realtime PV Power kW",
    "IoT CO2 Peak ppm"
};

string[] upExprs = new string[] {
    // Realtime Building Power kW
    @"VAR _t = CALCULATE ( MAX ( gold_iot_realtime[timestamp] ), gold_iot_realtime[sensor_type] = ""building_kwh"" ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""building_kwh"" )",
    // V1 HVAC Power kW
    @"VAR _t = CALCULATE ( MAX ( gold_iot_realtime[timestamp] ), gold_iot_realtime[sensor_type] = ""hvac_kwh"" ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""hvac_kwh"" )",
    // Realtime Building Baseline kW
    @"VAR _t = CALCULATE ( MAX ( gold_iot_realtime[timestamp] ), gold_iot_realtime[sensor_type] = ""building_kwh"" ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[baseline_value] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""building_kwh"" )",
    // IoT CO2 Live
    @"VAR _t = CALCULATE ( MAX ( gold_iot_realtime[timestamp] ), gold_iot_realtime[sensor_type] = ""CO2"" ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""CO2"" )",
    // Realtime PV Power kW
    @"VAR _t = CALCULATE ( MAX ( gold_iot_realtime[timestamp] ), gold_iot_realtime[sensor_type] = ""pv_ac_power"" ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""pv_ac_power"" )",
    // IoT CO2 Peak ppm
    @"VAR _t = CALCULATE ( MAX ( gold_iot_realtime[timestamp] ), gold_iot_realtime[sensor_type] = ""CO2"" ) RETURN CALCULATE ( MAX ( gold_iot_realtime[reading_value_max] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""CO2"" )"
};

string missing = "";
int upd = 0;
for (int i = 0; i < upNames.Length; i++)
{
    Measure found = null;
    foreach (var t in Model.Tables)
    {
        foreach (var m in t.Measures)
        {
            if (m.Name == upNames[i]) { found = m; }
        }
    }
    if (found != null) { found.Expression = upExprs[i]; upd++; }
    else { missing = missing + upNames[i] + "; "; }
}

// ---- 2) Format fix: Zone Comfort Cell Pct -> 0.0 --------------------------------
int fmt = 0;
foreach (var t in Model.Tables)
{
    foreach (var m in t.Measures)
    {
        if (m.Name == "Zone Comfort Cell Pct") { m.FormatString = "0.0"; fmt++; }
    }
}

Info("Page8 fixpack v2 -- updated: " + upd + "/6, format-set: " + fmt + ". Missing (verify names): " + (missing == "" ? "none" : missing));
