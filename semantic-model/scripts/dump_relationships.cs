// =============================================================================
// DUMP RELATIONSHIPS + building keys — Tabular Editor 2 C# Script (paste, F5)
// =============================================================================
// The IoT visuals on Page 8 don't react to the building slicer. That is almost
// certainly a missing/inactive RELATIONSHIP between the gold_iot_* tables and the
// building dimension (the measures dump doesn't show relationships, so I need this).
// Run this, then send me semantic-model\relationships_dump.txt — I'll return the
// exact relationship(s) to add so every IoT visual follows the building selection.
// =============================================================================

var OUT = @"C:\Energy Management App\Energy-copilot-platform\semantic-model\relationships_dump.txt";
var sb = new System.Text.StringBuilder();

sb.AppendLine("=== RELATIONSHIPS (from -> to) ===");
foreach (var r in Model.Relationships.OrderBy(x => x.FromTable.Name).ThenBy(x => x.ToTable.Name))
{
    sb.AppendLine(
        r.FromTable.Name + "[" + r.FromColumn.Name + "]  ->  " +
        r.ToTable.Name + "[" + r.ToColumn.Name + "]" +
        "   active=" + r.IsActive +
        "  crossFilter=" + r.CrossFilteringBehavior);
}

sb.AppendLine();
sb.AppendLine("=== which slicer drives Page 8? -> list every column that looks like a building key ===");
foreach (var t in Model.Tables.OrderBy(x => x.Name))
{
    foreach (var c in t.Columns)
    {
        var nm = c.Name.ToLower();
        if (nm.Contains("building") || nm == "fabric_building_id")
            sb.AppendLine(t.Name + "[" + c.Name + "]   (dataType=" + c.DataType + ")");
    }
}

System.IO.File.WriteAllText(OUT, sb.ToString());
Info(Model.Relationships.Count() + " relationships written to:\n" + OUT);
