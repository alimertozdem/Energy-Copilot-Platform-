// =====================================================================
// DUMP — All measures with errors (copyable from Output dialog)
// =====================================================================
// Read-only. Iterates every measure in the model and prints:
//   - Measure name
//   - Home table
//   - Error message (full text)
//   - Expression (truncated to 500 chars)
// for each measure that has a non-empty error state.
//
// USAGE
//   1. TE2 → C# Script tab → paste this → F5
//   2. Output dialog opens (long) → click "Copy to clipboard" at bottom
//   3. Paste here in chat
// =====================================================================

int errorCount = 0;
int totalMeasures = 0;

Output("=================================================================");
Output("MEASURE ERROR REPORT");
Output("=================================================================");

foreach (var t in Model.Tables) {
    foreach (var m in t.Measures) {
        totalMeasures++;

        // ErrorMessage is set by TE when the measure fails compile/validate
        string errMsg = m.ErrorMessage;
        if (string.IsNullOrEmpty(errMsg)) continue;

        errorCount++;
        Output("");
        Output("-----------------------------------------------------------------");
        Output("MEASURE  : " + m.Name);
        Output("TABLE    : " + t.Name);
        Output("FOLDER   : " + (string.IsNullOrEmpty(m.DisplayFolder) ? "(none)" : m.DisplayFolder));
        Output("ERROR    : " + errMsg);
        Output("");
        Output("EXPRESSION:");
        string expr = m.Expression ?? "";
        if (expr.Length > 600) expr = expr.Substring(0, 600) + "...[truncated]";
        Output(expr);
    }
}

// Also dump table-level errors (e.g. calculated tables, DataTable foreach errors)
foreach (var t in Model.Tables) {
    string tErr = "";
    var ct = t as CalculatedTable;
    if (ct != null && !string.IsNullOrEmpty(ct.ErrorMessage)) {
        tErr = ct.ErrorMessage;
    }
    if (!string.IsNullOrEmpty(tErr)) {
        errorCount++;
        Output("");
        Output("-----------------------------------------------------------------");
        Output("CALCULATED TABLE : " + t.Name);
        Output("ERROR            : " + tErr);
    }
}

// Also dump calculated column errors
foreach (var t in Model.Tables) {
    foreach (var c in t.Columns) {
        var cc = c as CalculatedColumn;
        if (cc != null && !string.IsNullOrEmpty(cc.ErrorMessage)) {
            errorCount++;
            Output("");
            Output("-----------------------------------------------------------------");
            Output("CALCULATED COLUMN : " + t.Name + "[" + c.Name + "]");
            Output("ERROR             : " + cc.ErrorMessage);
            Output("EXPRESSION        : " + (cc.Expression ?? "").Replace("\n", " "));
        }
    }
}

Output("");
Output("=================================================================");
Output("SUMMARY: " + errorCount + " errors across " + totalMeasures + " measures.");
Output("=================================================================");
