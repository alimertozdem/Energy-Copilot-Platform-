// page8_fixpack_2026_06_21_v5_matrix_round.csx
// Tabular Editor 2 - C# Script. NO LINQ. Idempotent.
// The matrix kept showing 58.33333... because a FormatString alone was not applied by
// the visual. ROUND in the measure guarantees the displayed value regardless of format.
// Run: F5 -> Ctrl+S -> Refresh in PBI Desktop.

int n = 0;
foreach (var t in Model.Tables)
{
    foreach (var m in t.Measures)
    {
        if (m.Name == "Zone Comfort Cell Pct")
        {
            m.Expression = @"ROUND ( AVERAGE ( gold_iot_realtime[in_setpoint_pct] ), 0 )";
            m.FormatString = "0";
            n++;
        }
    }
}
Info("Zone Comfort Cell Pct rounded: " + n + " (expected 1). Now Ctrl+S + Refresh.");
