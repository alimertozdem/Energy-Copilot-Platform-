// =============================================================================
// DUMP ALL MEASURES  —  Tabular Editor 2 C# Script  (paste once, run with F5)
// =============================================================================
// Writes EVERY measure in the live model (table, name, format string, display
// folder, and the full DAX expression) to a single text file, plus every
// calculated column. Send me that file and I'll review all of them wholesale and
// return ONE consolidated fix script you paste once.
//
// If you don't have write access to the path below, change OUT_PATH (e.g. to
// @"C:\Users\<you>\Desktop\measures_dump.txt").
// =============================================================================

var OUT_PATH = @"C:\Energy Management App\Energy-copilot-platform\semantic-model\measures_dump.txt";

var sb = new System.Text.StringBuilder();

sb.AppendLine("############################################################");
sb.AppendLine("# MEASURES");
sb.AppendLine("############################################################");
sb.AppendLine();

int nm = 0;
foreach (var m in Model.AllMeasures.OrderBy(x => x.Table.Name).ThenBy(x => x.Name))
{
    nm++;
    sb.AppendLine("### TABLE   : " + m.Table.Name);
    sb.AppendLine("### MEASURE : " + m.Name);
    sb.AppendLine("### FORMAT  : " + (m.FormatString ?? ""));
    sb.AppendLine("### FOLDER  : " + (m.DisplayFolder ?? ""));
    sb.AppendLine("--- DAX ---");
    sb.AppendLine(m.Expression);
    sb.AppendLine();
    sb.AppendLine("------------------------------------------------------------");
}

sb.AppendLine();
sb.AppendLine("############################################################");
sb.AppendLine("# CALCULATED COLUMNS");
sb.AppendLine("############################################################");
sb.AppendLine();

int nc = 0;
foreach (var t in Model.Tables)
{
    foreach (var c in t.Columns)
    {
        // Only calculated columns have a DAX expression.
        var cc = c as CalculatedColumn;
        if (cc == null) continue;
        nc++;
        sb.AppendLine("### TABLE  : " + t.Name);
        sb.AppendLine("### COLUMN : " + cc.Name);
        sb.AppendLine("--- DAX ---");
        sb.AppendLine(cc.Expression);
        sb.AppendLine();
        sb.AppendLine("------------------------------------------------------------");
    }
}

System.IO.File.WriteAllText(OUT_PATH, sb.ToString());
Info(nm + " measures + " + nc + " calculated columns written to:\n" + OUT_PATH);
