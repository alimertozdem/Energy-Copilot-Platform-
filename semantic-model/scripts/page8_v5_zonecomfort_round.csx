// page8_v5_zonecomfort_round.csx   (USE THIS ONE; ignore page8_fixpack_2026_06_21_v5_matrix_round.csx)
// Tabular Editor 2 - C# Script. NO LINQ. Idempotent.
// Fixes the matrix "58.33333..." by ROUNDing in DAX (a FormatString alone was ignored
// by the matrix visual). Keeps the latest-day (event_date = MAX) anchor from v1.
// Run: F5 -> Ctrl+S -> Refresh in PBI Desktop.

int n = 0;
foreach (var t in Model.Tables)
{
    foreach (var m in t.Measures)
    {
        if (m.Name == "Zone Comfort Cell Pct")
        {
            m.Expression = @"VAR _d = MAX ( gold_iot_realtime[event_date] ) RETURN ROUND ( CALCULATE ( AVERAGE ( gold_iot_realtime[in_setpoint_pct] ), gold_iot_realtime[event_date] = _d ), 0 )";
            m.FormatString = "0";
            n++;
        }
    }
}
Info("Zone Comfort Cell Pct rounded + latest-day anchor: " + n + " (expected 1). Now Ctrl+S + Refresh.");
