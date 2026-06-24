// =====================================================================
// Energy Copilot Platform - Page 3 Fix Pack v2 (fixes v1 compile error)
// File: semantic-model/scripts/page3_fixpack_2026_06_18_v2.csx
// v1 used regular "..." strings for the P3 Open Critical/High measures, but
// their DAX contains ""CRITICAL"" which only escapes inside a verbatim @"..."
// string -> C# compile error (CS1002/CS1026/CS1525, lines 59-60).
// v2: every DAX arg with embedded quotes is now @"...". Behaviour identical.
//
// Verified vs live gold: 9 open (2 Crit + 2 High + 5 Med), resolution 99.7%,
// top risk = Berliner / Hamburg (score 3).
// =====================================================================

string home   = "gold_anomaly_log";
string folder = "Page3 Anomalies";
if (!Model.Tables.Contains(home))
    throw new Exception("Home table '" + home + "' not found.");

Action<string,string,string> upsert = (name, dax, fmt) => {
    Measure m = null;
    foreach (var t in Model.Tables) {
        if (m != null) break;
        foreach (var ms in t.Measures)
            if (ms.Name == name) { m = ms; break; }
    }
    if (m == null) m = Model.Tables[home].AddMeasure(name);
    m.Expression = dax.Trim();
    if (!string.IsNullOrEmpty(fmt)) m.FormatString = fmt;
    m.DisplayFolder = folder;
};

// 1) Real resolution rate -> 99.7%
upsert("P3 Resolution Rate Pct", @"
DIVIDE (
    CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = TRUE () ),
    COUNTROWS ( gold_anomaly_log )
)", "0.0%");

// 2) Severity-weighted OPEN risk score (per building)
upsert("P3 Risk Score", @"
VAR _c = CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""CRITICAL"" )
VAR _h = CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""HIGH"" )
VAR _m = CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""MEDIUM"" )
RETURN _c * 3 + _h * 2 + _m", "#,##0");

// 3) Building's share of OPEN portfolio risk
upsert("P3 Risk Share Pct", @"
DIVIDE ( [P3 Risk Score], CALCULATE ( [P3 Risk Score], ALL ( silver_building_master ) ) )", "0.0%");

// 4) Top risk building by OPEN severity weight
upsert("P3 Top Risk Building", @"
VAR _t = ADDCOLUMNS ( VALUES ( silver_building_master[building_name] ), ""@r"", [P3 Risk Score] )
VAR _top = TOPN ( 1, FILTER ( _t, [@r] > 0 ), [@r], DESC )
RETURN CONCATENATEX ( _top, silver_building_master[building_name], "", "" )", "");

// 5) Clean open counts (now verbatim -> no compile error)
upsert("P3 Open Critical", @"CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""CRITICAL"" ) + 0", "#,##0");
upsert("P3 Open High",     @"CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""HIGH"" ) + 0", "#,##0");
upsert("P3 Open Total",    @"CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE () ) + 0", "#,##0");

Info("Page 3 v2 applied. Save (Ctrl+S), Refresh. Expect: Resolution 99.7%, "
   + "Top Risk = Berliner/Hamburg (3), Open Total 9, Critical 2, High 2.");
