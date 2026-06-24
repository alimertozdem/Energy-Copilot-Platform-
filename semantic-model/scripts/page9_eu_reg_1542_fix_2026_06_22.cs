// =============================================================================
// FIX — Page 9: EU Battery Regulation number  2023/1670  ->  2023/1542
// Tabular Editor 2 C# script.  Paste -> F5 -> Ctrl+S (F5 alone does NOT save the
// model) -> then Power BI Desktop -> Refresh.
// =============================================================================
// The EU Batteries Regulation is (EU) 2023/1542 (in force 2024-01-01). The wrong
// number "2023/1670" is hardcoded as a string literal in two LIVE model measures:
//   - C5 EU Compliance Status Text     (table: gold_battery_simulation)  2 hits
//   - I2 Chemistry Recommendation Text (table: gold_country_regulations) 1 hit
//
// The gold_country_regulations TABLE DATA is already correct
// ("EU 2023/1542 + BattG + EEG 2023", etc.) — only the measure strings are wrong.
// This replaces the literal in-place across ALL measures (safe, catches any other
// stray occurrence). Idempotent: after a successful run no measure contains 1670.
// =============================================================================

int fixedCount = 0;
foreach (var m in Model.AllMeasures)
{
    if (m.Expression != null && m.Expression.Contains("2023/1670"))
    {
        m.Expression = m.Expression.Replace("2023/1670", "2023/1542");
        fixedCount++;
        Info("Fixed EU reg number in measure: " + m.Name);
    }
}

Info("Done. Measures corrected: " + fixedCount +
     "  (expected 2: 'C5 EU Compliance Status Text', 'I2 Chemistry Recommendation Text').");

// AFTER RUNNING:
//   1) Ctrl+S to write back to the model (REQUIRED — F5 only runs in memory).
//   2) Power BI Desktop -> Refresh.
//   3) Page 9 should now read "EU 2023/1542" in the Compliance Status card and the
//      Chemistry Recommendation text.
//   4) If the embedded report still shows 2023/1670 anywhere, check for a static
//      TEXT BOX on the page (not a measure) — that is fixed in Desktop, not here.
