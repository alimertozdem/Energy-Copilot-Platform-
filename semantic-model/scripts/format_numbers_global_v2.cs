// =====================================================================
// Global number formatting v2 — also overwrites "General" format (the cause
// of raw floats like 162.40709... in tooltips). Run in TE2 (F5), Save, Refresh.
// =====================================================================
// v1 only touched EMPTY formats; columns/measures with FormatString = "General"
// (which displays full float precision) were skipped. v2 also rewrites "General"
// and "0", while leaving real formats (%, €, custom) untouched.

System.Func<string,bool> needs = (fs) =>
    string.IsNullOrEmpty(fs)
    || fs.Trim().Equals("General", System.StringComparison.OrdinalIgnoreCase)
    || fs.Trim() == "0";

int mf = 0, cf = 0;

foreach (var m in Model.AllMeasures) {
    if (needs(m.FormatString)) { m.FormatString = "#,##0.0"; mf++; }
}

foreach (var t in Model.Tables) {
    foreach (var c in t.Columns) {
        var dt = c.DataType.ToString();
        if ((dt == "Double" || dt == "Decimal") && needs(c.FormatString)) {
            c.FormatString = "#,##0.0";
            cf++;
        }
    }
}

Output("=====================================================");
Output("v2 formatted " + mf + " measures + " + cf + " numeric columns (incl. 'General').");
Output("IMPORTANT: File -> Save (Ctrl+S), then in Power BI press Refresh. If a visual still");
Output("shows raw numbers, close & reopen the report so the live model reloads.");
Output("=====================================================");
