// =============================================================================
// Diagnostic — Date Table & Columns
// File: semantic-model/scripts/diag_date_table.cs
// AMAÇ: Date table'ın gerçek adını ve kolonlarını listele
//        4 broken measure'ı doğru referansla fix edebilmek için
// ÇALIŞTIRMA: C# Script → yapıştır → F5 (Ctrl+S GEREKMEZ — sadece okuma)
// =============================================================================

Info("=== ALL TABLES ===");
foreach (var t in Model.Tables)
{
    Info("Table: '" + t.Name + "' (Hidden=" + t.IsHidden + ", DataCategory=" + t.DataCategory + ")");
}

Info("");
Info("=== DATE-LIKE TABLES (detailed columns) ===");
foreach (var t in Model.Tables)
{
    string nameLower = t.Name.ToLower();
    bool isDateLike = nameLower.Contains("date") ||
                      nameLower.Contains("calendar") ||
                      nameLower.Contains("time") ||
                      nameLower.Contains("dayofweek");

    if (isDateLike)
    {
        Info("");
        Info("Table: '" + t.Name + "'");
        foreach (var c in t.Columns)
        {
            Info("  Column: '" + c.Name + "' (DataType=" + c.DataType + ")");
        }
    }
}

Info("");
Info("=== EXISTING WORKING MEASURES THAT USE DATE ===");
int found = 0;
foreach (var m in Model.AllMeasures)
{
    if (m.Expression != null && m.Expression.Contains("DATEADD"))
    {
        Info("Measure: '" + m.Name + "' (table: " + m.Table.Name + ")");
        Info("  Expression: " + m.Expression.Replace("\n", " ").Replace("  ", " "));
        found++;
        if (found >= 5) break;
    }
}
if (found == 0)
{
    Info("(no existing DATEADD measures found)");
}
