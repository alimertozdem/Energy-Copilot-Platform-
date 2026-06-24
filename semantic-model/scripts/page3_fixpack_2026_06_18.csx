// =====================================================================
// Energy Copilot Platform - Page 3 (Anomalies & Alerts) Fix Pack
// File: semantic-model/scripts/page3_fixpack_2026_06_18.csx
// Tool: Tabular Editor 2/3 -> C# Script -> Run -> Ctrl+S -> Refresh
//
// CORE REFRAME (verified vs live gold): the page drowns in 2,953 RESOLVED
//   historical anomalies; the actionable content is just 9 OPEN issues
//   (2 Critical + 2 High + 5 Medium). The table, "risk share" and "top risk"
//   all currently rank by ALL-TIME volume (mostly resolved) -> misleading.
//   These measures re-base everything on OPEN, severity-weighted risk.
//
// Verified risk (Critical*3 + High*2 + Medium*1, open only):
//   Berliner 3, Hamburg 3 (top), Wien 2, Amsterdam 2, others 1.
//   Resolution rate = 99.7% (NOT 100%).
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

// 1) Real resolution rate -> 99.7% (the card rounds 100% and hides 9 open)
upsert("P3 Resolution Rate Pct",
    "DIVIDE ( CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = TRUE () ), COUNTROWS ( gold_anomaly_log ) )",
    "0.0%");

// 2) Severity-weighted OPEN risk score (per building via the relationship)
upsert("P3 Risk Score", @"
VAR _c = CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""CRITICAL"" )
VAR _h = CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""HIGH"" )
VAR _m = CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""MEDIUM"" )
RETURN _c * 3 + _h * 2 + _m", "#,##0");

// 3) Building's share of OPEN portfolio risk (replaces all-time count share)
upsert("P3 Risk Share Pct",
    "DIVIDE ( [P3 Risk Score], CALCULATE ( [P3 Risk Score], ALL ( silver_building_master ) ) )",
    "0.0%");

// 4) Top risk building by OPEN severity weight (was picking by all-time/ties)
upsert("P3 Top Risk Building", @"
VAR _t = ADDCOLUMNS ( VALUES ( silver_building_master[building_name] ), ""@r"", [P3 Risk Score] )
VAR _top = TOPN ( 1, FILTER ( _t, [@r] > 0 ), [@r], DESC )
RETURN CONCATENATEX ( _top, silver_building_master[building_name], "", "" )", "");

// 5) Open count by severity (clean, slicer/building-aware) - optional rebind for cards
upsert("P3 Open Critical", "CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""CRITICAL"" ) + 0", "#,##0");
upsert("P3 Open High",     "CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE (), UPPER ( gold_anomaly_log[severity] ) = ""HIGH"" ) + 0", "#,##0");
upsert("P3 Open Total",    "CALCULATE ( COUNTROWS ( gold_anomaly_log ), gold_anomaly_log[is_resolved] = FALSE () ) + 0", "#,##0");

Info("Page 3 fix pack applied. Save (Ctrl+S), Refresh. Then rebind visuals - "
   + "see chat checklist. Expect: Resolution 99.7%, Top Risk = Berliner/Hamburg (score 3), "
   + "Open Total 9, Open Critical 2, Open High 2.");
