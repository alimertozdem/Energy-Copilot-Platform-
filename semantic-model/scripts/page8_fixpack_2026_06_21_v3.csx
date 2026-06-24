// page8_fixpack_2026_06_21_v3.csx
// Tabular Editor 2 - Advanced Scripting (C# Script tab). NO LINQ. Idempotent.
//
// SUPERSEDES the snapshot logic in v1/v2. Diagnostic proved the data is clean
// (building_kwh has rows at the global max timestamp 2026-06-05 06:00), yet the
// snapshot measures returned BLANK for building_kwh while CO2 rendered. Root cause:
// DirectLake datetime equality ( timestamp = _t ) is unreliable here.
//
// FIX: anchor to the latest DATE instead of the latest datetime:
//   VAR _d = MAX(gold_iot_realtime[event_date])  -- date equality is robust
//   RETURN CALCULATE ( <agg>, event_date = _d, sensor_type = "<type>" )
// Works in BOTH the card (no hour axis -> latest-day average, never blank) and the
// "Latest Day" trend chart (hour_bucket axis -> each bucket's own date satisfies the
// filter, so the full profile plots). Still LIVE-READY: when streaming is on,
// MAX(event_date) = today, so the cards show today's data automatically.
//
// Also (re)sets Zone Comfort Cell Pct format to 0.0 (matrix showed 58.33333...).
//
// HOW TO RUN: External Tools -> Tabular Editor -> C# Script -> paste -> Run (F5) ->
//   Save -> publish. In PBI Desktop press Refresh. C1 + the "Latest Day" chart fill.

string[] upNames = new string[] {
    "Realtime Building Power kW",
    "V1 HVAC Power kW",
    "Realtime Building Baseline kW",
    "IoT CO2 Live",
    "Realtime PV Power kW",
    "IoT CO2 Peak ppm"
};

string[] upExprs = new string[] {
    // Realtime Building Power kW  (latest day avg)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""building_kwh"" )",
    // V1 HVAC Power kW  (latest day avg)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""hvac_kwh"" )",
    // Realtime Building Baseline kW  (latest day avg)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[baseline_value] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""building_kwh"" )",
    // IoT CO2 Live  (latest day avg)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""CO2"" )",
    // Realtime PV Power kW  (latest day avg)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""pv_ac_power"" )",
    // IoT CO2 Peak ppm  (latest day worst zone)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( MAX ( gold_iot_realtime[reading_value_max] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""CO2"" )"
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

int fmt = 0;
foreach (var t in Model.Tables)
{
    foreach (var m in t.Measures)
    {
        if (m.Name == "Zone Comfort Cell Pct") { m.FormatString = "0.0"; fmt++; }
    }
}

Info("Page8 fixpack v3 -- updated: " + upd + "/6, format-set: " + fmt + ". Missing (verify names): " + (missing == "" ? "none" : missing));
