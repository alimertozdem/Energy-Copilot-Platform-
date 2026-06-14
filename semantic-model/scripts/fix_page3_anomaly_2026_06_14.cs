// =============================================================================
// FIX — PAGE 3 (Anomalies & Alerts) residuals   [Tabular Editor 2 — "C# Script" tab]
// Paste in the C# Script tab -> F5 -> File > Save.  (This is DAX tooling, NOT the
// Spark notebook. The notebook anomaly_detection.py runs in FABRIC, not here.)
//
// Context: after the anomaly_detection.py re-run (episode resolution now applies to
// the catalog table), the open-state cards are already correct (Unresolved 1,
// Critical Open 1, Active Rate 0.2%, High Priority Open 1). This script fixes the
// leftover measures that still ignored is_resolved or counted all-time daily rows:
//   (1) Resolution Rate showed 9980%  -> percent applied twice (return fraction + % fmt)
//   (2) "Total" / "Type Breakdown"    -> counted 418 daily occurrences, not open ISSUES
//   (3) "High" card counted all-time  -> make it open, consistent with "Critical (Open)"
// is_resolved is a real boolean in this table (= FALSE / = TRUE work — confirmed by the
// Critical-Open card already reading 1).
// =============================================================================

var t = Model.Tables["gold_anomaly_log"];
if (t == null) { Info("ABORT: gold_anomaly_log table not found."); return; }

System.Action<string,string,string> Up = (name, expr, fmt) => {
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name) ?? t.AddMeasure(name);
    m.Expression = expr;
    m.FormatString = fmt;
    m.DisplayFolder = "P3 - Anomalies & Alerts";
    Info("Set [" + name + "]");
};

// (1) Resolution Rate — return a FRACTION + true percent format -> 99.8% (not 9980%).
Up("P3 Resolution Rate Pct",
@"VAR _resolved = CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = TRUE )
VAR _total = [P3 Total Anomaly Count]
RETURN DIVIDE ( _resolved, _total )",
"0.0%");

// (2) Open ISSUES = distinct (building x anomaly_type) that still has an open row.
//     On the type-breakdown axis -> open issues per type (SOLAR shows ~1, not 418).
//     On a building axis -> open issues per building. Rebind the "Total" card + the
//     "Anomaly Type Breakdown" value to this.
Up("P3 Open Issue Count",
@"VAR _open = FILTER ( gold_anomaly_log, gold_anomaly_log[is_resolved] = FALSE )
RETURN COUNTROWS ( SUMMARIZE ( _open, gold_anomaly_log[building_id], gold_anomaly_log[anomaly_type] ) )",
"#,##0");

// (3) Open HIGH count — to match the "Critical (Open)" card.
Up("P3 High Open Count",
@"CALCULATE ( COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""HIGH"", gold_anomaly_log[is_resolved] = FALSE )",
"#,##0");

Info("DONE. Save, then REBIND in Power BI Desktop (Page 3 fields):\n" +
     "  - 'High Anomalies' card            -> [P3 High Open Count]\n" +
     "  - 'Total Anomalies' card           -> [P3 Open Issue Count]  (rename label to 'Open Issues')\n" +
     "  - 'Anomaly Type Breakdown' value   -> [P3 Open Issue Count]\n" +
     "Resolution Rate auto-fixes after refresh; if it still shows x100, set that card's format to 'General'.");
