// =====================================================================
// PROBE — List all tables in the currently-loaded semantic model
// =====================================================================
// Purpose : Diagnose "An object with name 'X' does not exist" errors
//           by printing every table the model actually has.
//
// USAGE   : Paste into Tabular Editor 2 → Advanced Scripting → Run (F5)
//           → Look at the Output panel (bottom).
//
// SAFE    : Read-only. Does NOT change the model. Nothing to save.
// =====================================================================

Output("================================================================");
Output("ALL TABLES in model: " + Model.Name);
Output("================================================================");

int idx = 0;
foreach (var t in Model.Tables.OrderBy(t => t.Name)) {
    idx++;
    Output(idx.ToString("00") + "  " + t.Name + "   (" + t.Columns.Count + " cols, " + t.Measures.Count + " measures)");
}

Output("================================================================");
Output("Total: " + idx + " tables");
Output("================================================================");

// Highlight Page 9-relevant tables
Output("");
Output("Looking for Page 9 / battery related tables:");
var keywords = new string[] { "battery", "country", "strategy", "regulation", "fitness" };
foreach (var t in Model.Tables) {
    string lower = t.Name.ToLower();
    foreach (var kw in keywords) {
        if (lower.Contains(kw)) {
            Output("  -> " + t.Name);
            break;
        }
    }
}
