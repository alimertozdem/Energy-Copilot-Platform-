// page8_fixpack_2026_06_21.csx
// Tabular Editor 2 - Advanced Scripting (C# Script tab). NO LINQ. Idempotent.
//
// PAGE 8 (IoT) finalization. Two product-owner decisions (2026-06-21):
//   (A) Freshness = "latest snapshot + as-of". The Realtime measures averaged the
//       WHOLE window (data ends 2026-06-05) and were labelled "Real-Time". We anchor
//       them to MAX(timestamp) = the most recent 15-min snapshot. LIVE-READY: the day
//       streaming is switched on, MAX(timestamp)=now and the SAME cards become truly
//       live with zero DAX change. Comfort/zone KPIs anchor to MAX(event_date) (daily).
//   (B) Cost engine = gold_iot_fdd is the SINGLE source of truth (equipment/fault/
//       confidence/power-waste). Daily-summary cost is dropped from the page:
//       'IoT Total Cost Today EUR' -> FDD-only (removes the realtime cost_eur_window
//       term that double-counted a second, disagreeing engine).
//   + CO2 thresholds aligned to the approved standard 800/1500 (was 800/1200).
//   + 'IoT FDD Findings Today' TODAY() -> MAX(event_date) (was blank: data is stale).
//   + 'Active Sensor Locations' -> building-qualified distinct zones (sensor_location
//       names collide across buildings; portfolio undercounted to 14).
//   + new: 'IoT Data As Of' (as-of stamp) and 'IoT CO2 Peak ppm' (averaging hid the
//       portfolio max of ~1669 ppm behind a "Good 746" card).
//
// Columns are verified against notebooks/iot/11b (gold_iot_realtime: timestamp,
// event_date, reading_value_avg, reading_value_max, baseline_value, in_setpoint_pct,
// sensor_type, sensor_location, building_id) and 11c (gold_iot_fdd: event_date,
// cost_eur_estimate, severity).
//
// HOW TO RUN: External Tools -> Tabular Editor -> C# Script -> paste -> Run (F5) ->
//   Save -> publish. Then do the PBI Desktop steps below.
//
// AFTER RUNNING (PBI Desktop, report view — these are NOT measures):
//   1. Place [IoT Data As Of] as a small caption under the 4 KPI cards (e.g. top-right).
//   2. Card titles: "Real-Time Building Power" -> "Building Power (latest)";
//      "Building & HVAC Power - Last 24h" -> "Building & HVAC Power - latest day".
//   3. "Estimated Waste by Equipment(EUR)" title -> add "(Annual Est.)".
//   4. Zone Comfort matrix: the cells are % in setpoint, not raw readings -> set the
//      visual/column subtitle to "% in setpoint" (e.g. header "CO2 %" / "Temp %").
//   5. "Active Sensors" card -> rename title to "Active Zones".
//   6. Date slicer (showing 21.06.2025-30.04.2026, outside the data) does not filter
//      the IoT visuals -> remove it, or bind+default it to the IoT data window.
//   7. (optional) add [IoT CO2 Peak ppm] as a tooltip/second line on the CO2 card.

// ---- 1) UPDATE existing measures (search whole model by name) -------------------
string[] upNames = new string[] {
    "Realtime Building Power kW",
    "V1 HVAC Power kW",
    "Realtime Building Baseline kW",
    "IoT CO2 Live",
    "Realtime PV Power kW",
    "IoT Zone Setpoint Compliance Pct",
    "Zone Comfort Cell Pct",
    "IoT CO2 Display",
    "IoT CO2 Color",
    "IoT FDD Findings Today",
    "IoT Total Cost Today EUR",
    "Active Sensor Locations"
};

string[] upExprs = new string[] {
    // Realtime Building Power kW  (latest snapshot)
    @"VAR _t = MAX ( gold_iot_realtime[timestamp] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""building_kwh"" )",
    // V1 HVAC Power kW  (latest snapshot)
    @"VAR _t = MAX ( gold_iot_realtime[timestamp] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""hvac_kwh"" )",
    // Realtime Building Baseline kW  (latest snapshot)
    @"VAR _t = MAX ( gold_iot_realtime[timestamp] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[baseline_value] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""building_kwh"" )",
    // IoT CO2 Live  (latest snapshot)
    @"VAR _t = MAX ( gold_iot_realtime[timestamp] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""CO2"" )",
    // Realtime PV Power kW  (latest snapshot)
    @"VAR _t = MAX ( gold_iot_realtime[timestamp] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""pv_ac_power"" )",
    // IoT Zone Setpoint Compliance Pct  (latest day, comfort sensors only)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[in_setpoint_pct] ), gold_iot_realtime[event_date] = _d, gold_iot_realtime[sensor_type] IN { ""HVAC_temp"", ""humidity"", ""CO2"" } )",
    // Zone Comfort Cell Pct  (latest day; matrix slices by location/sensor_type)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( AVERAGE ( gold_iot_realtime[in_setpoint_pct] ), gold_iot_realtime[event_date] = _d )",
    // IoT CO2 Display  (800 / 1500 approved thresholds)
    @"VAR c = [IoT CO2 Live] RETURN SWITCH ( TRUE (), ISBLANK ( c ), ""--"", c < 800, ""Good "" & FORMAT ( c, ""0"" ) & "" ppm"", c <= 1500, ""Fair "" & FORMAT ( c, ""0"" ) & "" ppm"", ""Poor "" & FORMAT ( c, ""0"" ) & "" ppm"" )",
    // IoT CO2 Color  (800 / 1500 approved thresholds)
    @"VAR c = [IoT CO2 Live] RETURN SWITCH ( TRUE (), ISBLANK ( c ), ""#AAAAAA"", c < 800, ""#2ECC40"", c <= 1500, ""#FF851B"", ""#FF4136"" )",
    // IoT FDD Findings Today  (MAX event_date, not TODAY())
    @"VAR d = MAX ( gold_iot_fdd[event_date] ) RETURN CALCULATE ( COUNTROWS ( gold_iot_fdd ), gold_iot_fdd[event_date] = d )",
    // IoT Total Cost Today EUR  (FDD single source of truth)
    @"[IoT FDD Cost Today EUR]",
    // Active Sensor Locations  (building-qualified distinct zones, latest day)
    @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN CALCULATE ( COUNTROWS ( SUMMARIZE ( gold_iot_realtime, gold_iot_realtime[building_id], gold_iot_realtime[sensor_location] ) ), gold_iot_realtime[event_date] = _d )"
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

// ---- 2) ADD new measures on gold_iot_realtime -----------------------------------
var rt = Model.Tables["gold_iot_realtime"];
string[] addNames = new string[] { "IoT Data As Of", "IoT CO2 Peak ppm" };
string[] addExprs = new string[] {
    @"VAR _t = MAX ( gold_iot_realtime[timestamp] ) RETURN IF ( ISBLANK ( _t ), ""No data"", ""Data as of "" & FORMAT ( _t, ""dd MMM HH:mm"" ) )",
    @"VAR _t = MAX ( gold_iot_realtime[timestamp] ) RETURN CALCULATE ( MAX ( gold_iot_realtime[reading_value_max] ), gold_iot_realtime[timestamp] = _t, gold_iot_realtime[sensor_type] = ""CO2"" )"
};
string[] addFmt = new string[] { "", "#,##0" };

int added = 0, addUpd = 0;
for (int i = 0; i < addNames.Length; i++)
{
    Measure found = null;
    foreach (var m in rt.Measures)
    {
        if (m.Name == addNames[i]) { found = m; }
    }
    if (found == null)
    {
        var nm = rt.AddMeasure(addNames[i], addExprs[i]);
        nm.FormatString = addFmt[i];
        nm.DisplayFolder = "IoT (Page 8)";
        added++;
    }
    else { found.Expression = addExprs[i]; addUpd++; }
}

Info("Page8 fixpack -- updated: " + upd + "/12, added: " + added + ", add-updated: " + addUpd + ". Missing (verify these names exist): " + (missing == "" ? "none" : missing));
