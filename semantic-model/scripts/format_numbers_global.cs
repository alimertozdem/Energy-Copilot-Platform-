// =====================================================================
// Global number formatting — stop raw float precision in visuals & tooltips.
// Run in Tabular Editor 2 (C# Script → F5), then File → Save, then PBI Refresh.
// =====================================================================
// Sets "#,##0.0" on every measure / numeric column that has NO format string yet.
// Measures/columns that already have a format (%, €, integers) are left untouched.
// Text measures ignore a numeric format, so they are safe.
// After this you can fine-tune individual %, €, or 2-decimal measures by hand.

int mf = 0, cf = 0;

foreach (var m in Model.AllMeasures) {
    if (string.IsNullOrEmpty(m.FormatString)) {
        m.FormatString = "#,##0.0";
        mf++;
    }
}

foreach (var t in Model.Tables) {
    foreach (var c in t.Columns) {
        var dt = c.DataType.ToString();
        if (string.IsNullOrEmpty(c.FormatString) && (dt == "Double" || dt == "Decimal")) {
            c.FormatString = "#,##0.0";
            cf++;
        }
    }
}

Output("=====================================================");
Output("Formatted " + mf + " measures + " + cf + " numeric columns to '#,##0.0'.");
Output("Save (Ctrl+S) -> PBI Refresh. Tooltips will now show clean 1-decimal numbers.");
Output("=====================================================");
