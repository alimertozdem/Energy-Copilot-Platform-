// page8_fixpack_2026_06_21_v4.csx
// Tabular Editor 2 - Advanced Scripting (C# Script tab). NO LINQ. Idempotent.
//
// IMPORTANT — make the change actually land:
//   In TE: run with F5, THEN press Ctrl+S (Save). F5 only edits the in-memory model
//   ("updated N/N" prints from memory); Ctrl+S commits to the dataset. Then in
//   Power BI Desktop press Home -> Refresh (or reopen) so the live connection reloads
//   the measure definitions. Verify by clicking the measure -> the formula bar must
//   show the event_date / REMOVEFILTERS version below.
//
// Two fixes vs the original measures:
//   (a) latest-DATE anchor (date equality is robust; datetime equality blanked under
//       DirectLake) -> never blank when the latest day has data; live-ready.
//   (b) REMOVEFILTERS(sensor_location) on the building-level cards -> building power /
//       HVAC / baseline / CO2 are building-level KPIs, so a zone (sensor_location)
//       selection in the Zone Comfort matrix must NOT empty them. This is why C1 went
//       "-- kW" while C3 (zonal CO2) still rendered.
//
// Zone Comfort Cell Pct keeps location sensitivity (it IS per-zone) -> NOT touched
// except format 0.0.

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
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""building_kwh"", REMOVEFILTERS ( gold_iot_realtime[sensor_location] ) )",
    // V1 HVAC Power kW
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""hvac_kwh"", REMOVEFILTERS ( gold_iot_realtime[sensor_location] ) )",
    // Realtime Building Baseline kW
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[baseline_value] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""building_kwh"", REMOVEFILTERS ( gold_iot_realtime[sensor_location] ) )",
    // IoT CO2 Live  (building-level air quality)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""CO2"", REMOVEFILTERS ( gold_iot_realtime[sensor_location] ) )",
    // Realtime PV Power kW
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""pv_ac_power"", REMOVEFILTERS ( gold_iot_realtime[sensor_location] ) )",
    // IoT CO2 Peak ppm  (worst zone on the latest day)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( MAX ( gold_iot_realtime[reading_value_max] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] = ""CO2"", REMOVEFILTERS ( gold_iot_realtime[sensor_location] ) )"
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

Info("Page8 fixpack v4 -- updated: " + upd + "/6, format-set: " + fmt + ". Missing: " + (missing == "" ? "none" : missing) + "  >>> NOW PRESS Ctrl+S to commit, then Refresh in PBI Desktop.");
