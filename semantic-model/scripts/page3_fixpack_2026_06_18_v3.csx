// =====================================================================
// Energy Copilot Platform - Page 3 Fix Pack v3 (additive, run AFTER v2)
// File: semantic-model/scripts/page3_fixpack_2026_06_18_v3.csx
//
// Adds:
//   P3 Top Risk Score    - MAX single-building open risk (=3), for the
//                          "Top Risk Building" card number (was showing the
//                          portfolio TOTAL 15 because the card has no building
//                          context). Pair with P3 Top Risk Building (name).
//   P3 Buildings Affected - count of buildings with >=1 open anomaly (=9),
//                          a useful new top KPI card.
//   (For an "Open Risk (weighted)" card you can reuse the existing
//    P3 Risk Score measure -> shows 15 at portfolio scope.)
// =====================================================================

string home   = "gold_anomaly_log";
string folder = "Page3 Anomalies";

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

// Top single-building open risk score (=3: Berliner/Hamburg)
upsert("P3 Top Risk Score",
    "MAXX ( VALUES ( silver_building_master[building_name] ), [P3 Risk Score] )", "#,##0");

// Buildings with at least one open anomaly (=9 of 10)
upsert("P3 Buildings Affected",
    "COUNTROWS ( FILTER ( VALUES ( silver_building_master[building_name] ), [P3 Open Total] > 0 ) )", "#,##0");

Info("Page 3 v3 applied. Save (Ctrl+S), Refresh. Top Risk card: score -> "
   + "P3 Top Risk Score (=3), name -> P3 Top Risk Building (Berliner/Hamburg). "
   + "New cards: Buildings Affected (=9), Open Risk weighted -> P3 Risk Score (=15).");
