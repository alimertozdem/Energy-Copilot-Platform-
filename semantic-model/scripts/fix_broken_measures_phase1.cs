// =====================================================================
// PHASE 1 — fix the EASY broken measures (post-refresh schema drift)
// Run in Tabular Editor 2 (C# Script → F5), then File → Save, then PBI Refresh.
// =====================================================================
// Fixes 12 of the 20 errors:
//   - column renames (refresh changed the schema):
//       gold_kpi_daily[hdd_normalized_eui]            -> [climate_adjusted_eui]
//       gold_battery_dispatch[battery_tech]            -> [battery_type]
//       gold_battery_dispatch[round_trip_efficiency_percent] -> [round_trip_efficiency]
//   - the 6 IoT "Today" measures: the date table's real name contains apostrophes
//     ('Date'), so REMOVEFILTERS('Date') failed to resolve. Page 8 is real-time
//     (no date slicer), so we drop the slicer override entirely.
// The remaining ~7 errors are the battery I4 schema drift (battery_health / SoH gone,
//   cumulative_cycles moved to daily_summary, is_active_strategy removed) + the
//   pre-existing U-Value DATATABLE — handled separately after the pipeline decision.
// =====================================================================

int renamed = 0;
foreach (var m in Model.AllMeasures) {
    string e = m.Expression;
    string n = e
        .Replace("[hdd_normalized_eui]", "[climate_adjusted_eui]")
        .Replace("[battery_tech]", "[battery_type]")
        .Replace("[round_trip_efficiency_percent]", "[round_trip_efficiency]");
    if (n != e) { m.Expression = n; renamed++; Output("RENAMED column in: " + m.Name); }
}

System.Action<string,string,string> FixDate = (name, expr, fmt) => {
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name);
    if (m == null) { Output("MISS (not found): " + name); return; }
    m.Expression = expr;
    if (fmt != null) m.FormatString = fmt;
    Output("FIXED 'Date' ref: " + name);
};

FixDate("IoT FDD Findings Today",
@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[event_date] = TODAY() )", "#,##0");
FixDate("IoT FDD High Today",
@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[severity] = ""High"", gold_iot_fdd[event_date] = TODAY() )", "#,##0");
FixDate("IoT FDD Cost Today EUR",
@"CALCULATE( SUM(gold_iot_fdd[cost_eur_estimate]), gold_iot_fdd[event_date] = TODAY() )", "#,##0.00");
FixDate("IoT Total Cost Today EUR",
@"[IoT FDD Cost Today EUR] + CALCULATE( SUM(gold_iot_realtime[cost_eur_window]), gold_iot_realtime[event_date] = TODAY() )", "#,##0.00");
FixDate("IoT FDD Diagnoses Today",
@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[event_date] = TODAY() )", "#,##0");
FixDate("IoT FDD Energy Impact kWh Today",
@"CALCULATE( SUM(gold_iot_fdd[energy_impact_kwh]), gold_iot_fdd[event_date] = TODAY() )", "#,##0.0");

Output("=====================================================");
Output("PHASE 1 DONE — columns renamed in " + renamed + " measures + 6 IoT date refs fixed.");
Output("Save (Ctrl+S) → PBI Refresh. ~7 battery/U-Value errors remain (Phase 2).");
Output("=====================================================");
