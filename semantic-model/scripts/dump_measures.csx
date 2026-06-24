// dump_measures.csx
// Tabular Editor 2 - Advanced Scripting (C# Script tab)
// Purpose: regenerate semantic-model/measures_dump.txt from the LIVE model,
//          so fixes are verified against ground truth, not a stale file.
// Rule: NO LINQ - plain foreach only.
//
// HOW TO RUN
//   1. Open the .pbix in Power BI Desktop (the model you publish from).
//   2. External Tools -> Tabular Editor (TE2).
//   3. Open the "C# Script" tab, paste this script, press Run (F5).
//   4. It overwrites measures_dump.txt in place. Then say "done".

var sb = new System.Text.StringBuilder();
int count = 0;

foreach (var m in Model.AllMeasures)
{
    count++;
    sb.AppendLine("------------------------------------------------------------");
    sb.AppendLine("### TABLE   : " + m.Table.Name);
    sb.AppendLine("### MEASURE : " + m.Name);
    sb.AppendLine("### FORMAT  : " + (m.FormatString ?? ""));
    sb.AppendLine("### FOLDER  : " + (m.DisplayFolder ?? ""));
    sb.AppendLine("--- DAX ---");
    sb.AppendLine("");
    sb.AppendLine(m.Expression);
    sb.AppendLine("");
}

var header =
    "# EnergyCopilotModel - measures dump (regenerated from LIVE model)\r\n" +
    "# Total measures: " + count + "\r\n\r\n";

System.IO.File.WriteAllText(
    @"C:\Energy Management App\Energy-copilot-platform\semantic-model\measures_dump.txt",
    header + sb.ToString(),
    new System.Text.UTF8Encoding(false)
);

Info("Dumped " + count + " measures to measures_dump.txt");
