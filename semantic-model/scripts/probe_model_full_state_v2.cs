// =====================================================================
// PROBE v2 — Full model state → WRITES TO FILE (READ-ONLY on the model)
// =====================================================================
// Why v2: copying the Output pane by hand is painful. This version builds
// the full dump and writes it to a file in the repo folder, which the
// assistant can read directly. You only run it — no copy/paste.
//
// HOW TO RUN (Tabular Editor 2):
//   1) C# Script tab → paste this whole script.
//   2) F5 (Run).
//   3) You'll see "WROTE: ...\_probe_output.txt" in the Output pane. Done.
//      Just tell the assistant "probe yazıldı".
//
// Nothing in the model is modified.
// =====================================================================

var sb = new System.Text.StringBuilder();
System.Action<string> W = (s) => sb.AppendLine(s);

W("######## 1. TABLES + COLUMNS ########");
foreach (var t in Model.Tables.OrderBy(t => t.Name)) {
    W("");
    W("TABLE: " + t.Name + "   (" + t.Columns.Count + " cols, " + t.Measures.Count + " measures)");
    foreach (var c in t.Columns.OrderBy(c => c.Name)) {
        W("   col | " + c.Name + " | " + c.DataType);
    }
}

W("");
W("######## 2. MEASURES (home table | measure name) ########");
int mcount = 0;
foreach (var t in Model.Tables.OrderBy(t => t.Name)) {
    foreach (var m in t.Measures.OrderBy(m => m.Name)) {
        mcount++;
        W("MEASURE | " + t.Name + " | " + m.Name);
    }
}
W("TOTAL MEASURES: " + mcount);

W("");
W("######## 3. RELATIONSHIPS ########");
foreach (var r in Model.Relationships) {
    W("REL | " + r.FromTable.Name + "[" + r.FromColumn.Name + "] -> "
      + r.ToTable.Name + "[" + r.ToColumn.Name + "]"
      + "  active=" + r.IsActive
      + "  xfilter=" + r.CrossFilteringBehavior);
}

// Write the dump to the repo folder (the assistant reads it directly).
string outPath = @"C:\Energy Management App\Energy-copilot-platform\semantic-model\_probe_output.txt";
try {
    System.IO.File.WriteAllText(outPath, sb.ToString());
    Output("WROTE: " + outPath);
    Output("Tables + measures + relationships dumped. Tell the assistant: probe yazildi.");
} catch (System.Exception ex) {
    // Fallback: if file write is blocked, show in Output to copy manually.
    Output("FILE WRITE FAILED (" + ex.Message + ") — copy the text below instead:");
    Output(sb.ToString());
}
