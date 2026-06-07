// =============================================================================
// Energy Copilot Platform — Page 3 FULL Measures Installer
// File: semantic-model/scripts/page3_full_install.cs
// Last updated: 2026-05-18
//
// AMAÇ:
//   Sayfa 3 (Anomalies & Alerts) için GEREKEN TÜM ölçüleri tek tıkla yükler.
//   v21 (clean measures) + v22 (supplementary) + v23 (insight cards) + 5 yeni.
//
// SCRIPT TE2 UYUMLU:
//   .Find() yerine foreach loop kullanıyor (TableCollection .Find()'i desteklemez)
//   System.Action lambdaları TE2'de çalışır
//
// HOME TABLE: gold_anomaly_log
//
// EKLENEN ÖLÇÜLER (24 toplam):
//   --- v21 Base (KPI cards C1-C5 + V6/V8/V9 visuals) ---
//   1.  P3 Total Anomaly Count
//   2.  P3 Total Anomaly PY
//   3.  P3 Critical Open Count
//   4.  P3 High Anomaly Count
//   5.  P3 High Anomaly Previous Month
//   6.  P3 Unresolved Count
//   7.  P3 Unresolved YoY
//   8.  P3 Data Quality Score
//   9.  P3 Data Quality Target
//   10. P3 Medium Anomaly Count
//   11. P3 Critical Anomaly Count
//   12. P3 Low Anomaly Count
//   13. P3 Anomaly Deviation Pct
//   --- v22 Supplementary ---
//   14. P3 Building Anomaly Share Pct (with ROUND fix)
//   15. P3 Anomaly Status
//   --- v23 Insight Cards (bottom row) ---
//   16. P3 Avg Days Open
//   17. P3 High Priority Open Count
//   18. P3 After Hours Waste Rate Pct
//   --- 2026-05-18 Page 3 fix ---
//   19. P3 Resolution Rate Pct
//   20. P3 Resolution Rate Pct PY
//   21. P3 Top Risk Building Score (FIXED — v23 TOPN bug)
//   22. P3 Top Risk Building Name
//   23. P3 Active Anomaly Rate Pct
//
// ÇALIŞTIRMA:
//   1. Tabular Editor → C# Script tab → bu dosyayı yapıştır → F5
//   2. Output: "=== Page 3 FULL install: 23 ölçü ==="
//   3. Ctrl+S → Save changes to model → Yes
// =============================================================================

const string HOME_TABLE     = "gold_anomaly_log";
const string DISPLAY_FOLDER = "P3 - Anomalies & Alerts";

// ── Home table kontrolü ─────────────────────────────────────────────────────
Table homeTable = null;
foreach (var t in Model.Tables)
{
    if (t.Name == HOME_TABLE) { homeTable = t; break; }
}
if (homeTable == null)
{
    var sb = new System.Text.StringBuilder();
    foreach (var t in Model.Tables) { sb.Append(t.Name); sb.Append(", "); }
    Error("Home table '" + HOME_TABLE + "' bulunamadı.\nMevcut: " + sb.ToString());
    return;
}

// ── Date tablosu kontrolü (DATEADD için) ────────────────────────────────────
Table dateTable = null;
foreach (var t in Model.Tables)
{
    if (t.Name == "Date") { dateTable = t; break; }
}
if (dateTable == null)
{
    Warning("'Date' tablosu bulunamadı — PY ölçüleri (Total Anomaly PY, Unresolved YoY, Resolution Rate PY, High Anomaly Previous Month) çalışmayabilir.\n" +
            "DateTable model'de yoksa Power BI Desktop'ta önce DateTable oluştur.");
}

// ── Helper: Upsert ──────────────────────────────────────────────────────────
int createdCount = 0;
int updatedCount = 0;

System.Action<string, string, string> upsert = (name, expression, format) =>
{
    Measure existing = null;
    foreach (var m in homeTable.Measures)
    {
        if (m.Name == name) { existing = m; break; }
    }
    if (existing != null)
    {
        existing.Expression    = expression;
        existing.FormatString  = format;
        existing.DisplayFolder = DISPLAY_FOLDER;
        Info("UPDATED: " + name);
        updatedCount++;
    }
    else
    {
        var m = homeTable.AddMeasure(name, expression);
        m.FormatString  = format;
        m.DisplayFolder = DISPLAY_FOLDER;
        Info("CREATED: " + name);
        createdCount++;
    }
};


// =============================================================================
// === v21 BASE — KPI CARDS C1-C5 + V6/V8/V9 ===
// =============================================================================

upsert("P3 Total Anomaly Count",
@"COUNTROWS ( gold_anomaly_log )",
"#,##0");

upsert("P3 Total Anomaly PY",
@"CALCULATE (
    [P3 Total Anomaly Count],
    DATEADD ( 'Date'[Date], -1, YEAR )
)",
"#,##0");

upsert("P3 Critical Open Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""CRITICAL"",
    gold_anomaly_log[is_resolved] = FALSE
)",
"#,##0");

upsert("P3 High Anomaly Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""HIGH""
)",
"#,##0");

upsert("P3 High Anomaly Previous Month",
@"CALCULATE (
    [P3 High Anomaly Count],
    DATEADD ( 'Date'[Date], -1, MONTH )
)",
"#,##0");

upsert("P3 Unresolved Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[is_resolved] = FALSE
)",
"#,##0");

upsert("P3 Unresolved YoY",
@"CALCULATE (
    [P3 Unresolved Count],
    DATEADD ( 'Date'[Date], -1, YEAR )
)",
"#,##0");

upsert("P3 Data Quality Score",
@"AVERAGE ( silver_data_quality[quality_score_pct] )",
"0.0");

upsert("P3 Data Quality Target",
@"VAR _target = 95
RETURN _target",
"0.0");

upsert("P3 Medium Anomaly Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""MEDIUM""
)",
"#,##0");

upsert("P3 Critical Anomaly Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""CRITICAL""
)",
"#,##0");

upsert("P3 Low Anomaly Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""LOW""
)",
"#,##0");

upsert("P3 Anomaly Deviation Pct",
@"VAR _metric    = AVERAGE ( gold_anomaly_log[metric_value] )
VAR _threshold = AVERAGE ( gold_anomaly_log[threshold_value] )
RETURN
    IF (
        NOT ISBLANK ( _threshold ) && ABS ( _threshold ) > 0,
        DIVIDE ( _metric - _threshold, ABS ( _threshold ) ) * 100,
        BLANK ()
    )",
"+0.0;-0.0;—");


// =============================================================================
// === v22 SUPPLEMENTARY ===
// =============================================================================

upsert("P3 Building Anomaly Share Pct",
@"VAR _building =
    [P3 Total Anomaly Count]
VAR _portfolio =
    CALCULATE (
        [P3 Total Anomaly Count],
        ALL ( silver_building_master )
    )
RETURN
    ROUND ( DIVIDE ( _building, _portfolio ) * 100, 1 )",
"0.0");

upsert("P3 Anomaly Status",
@"IF (
    MAX ( gold_anomaly_log[is_resolved] ),
    ""Resolved"",
    ""Open""
)",
"");


// =============================================================================
// === v23 INSIGHT CARDS (BOTTOM ROW) ===
// =============================================================================

upsert("P3 Avg Days Open",
@"ROUND (
    AVERAGEX (
        FILTER (
            gold_anomaly_log,
            gold_anomaly_log[is_resolved] = FALSE
        ),
        DATEDIFF ( gold_anomaly_log[detected_date], TODAY (), DAY )
    ),
    0
)",
"#,##0");

upsert("P3 High Priority Open Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[is_resolved] = FALSE,
    gold_anomaly_log[severity] IN { ""CRITICAL"", ""HIGH"" }
)",
"#,##0");

upsert("P3 After Hours Waste Rate Pct",
@"VAR _ahw =
    CALCULATE (
        COUNTROWS ( gold_anomaly_log ),
        gold_anomaly_log[anomaly_type] = ""AFTER_HOURS_WASTE""
    )
RETURN
    ROUND ( DIVIDE ( _ahw, [P3 Total Anomaly Count], 0 ) * 100, 1 )",
"0.0");


// =============================================================================
// === 2026-05-18 PAGE 3 FIX (Resolution Rate, Top Risk, Active Rate) ===
// =============================================================================

upsert("P3 Resolution Rate Pct",
@"VAR _resolved =
    CALCULATE (
        COUNTROWS ( gold_anomaly_log ),
        gold_anomaly_log[is_resolved] = TRUE
    )
VAR _total = [P3 Total Anomaly Count]
RETURN
    ROUND ( DIVIDE ( _resolved, _total, 0 ) * 100, 1 )",
"0.0");

upsert("P3 Resolution Rate Pct PY",
@"VAR _resolved_py =
    CALCULATE (
        COUNTROWS ( gold_anomaly_log ),
        gold_anomaly_log[is_resolved] = TRUE,
        DATEADD ( 'Date'[Date], -1, YEAR )
    )
VAR _total_py =
    CALCULATE (
        [P3 Total Anomaly Count],
        DATEADD ( 'Date'[Date], -1, YEAR )
    )
RETURN
    ROUND ( DIVIDE ( _resolved_py, _total_py, 0 ) * 100, 1 )",
"0.0");

upsert("P3 Top Risk Building Score",
@"VAR _tbl =
    ADDCOLUMNS (
        VALUES ( silver_building_master[building_name] ),
        ""@cnt"", [P3 Unresolved Count]
    )
RETURN
    MAXX ( TOPN ( 1, _tbl, [@cnt], DESC ), [@cnt] )",
"#,##0");

upsert("P3 Top Risk Building Name",
@"VAR _tbl =
    ADDCOLUMNS (
        VALUES ( silver_building_master[building_name] ),
        ""@cnt"", [P3 Unresolved Count]
    )
RETURN
    MAXX ( TOPN ( 1, _tbl, [@cnt], DESC ), silver_building_master[building_name] )",
"");

upsert("P3 Active Anomaly Rate Pct",
@"VAR _open = [P3 Unresolved Count]
VAR _total = [P3 Total Anomaly Count]
RETURN
    ROUND ( DIVIDE ( _open, _total, 0 ) * 100, 1 )",
"0.0");


// =============================================================================
// ÖZET
// =============================================================================
Info("");
Info("=======================================================");
Info("=== Page 3 FULL install: " + (createdCount + updatedCount) + " ölçü ===");
Info("   Created : " + createdCount);
Info("   Updated : " + updatedCount);
Info("=======================================================");
Info("");
Info("SONRAKİ ADIM:");
Info("  1. Ctrl+S → Save changes to model → Yes");
Info("  2. Power BI Desktop'a dön → Refresh visuals");
Info("  3. Resolution Rate, Top Risk Building kartlarını bind et");
Info("");
Info("NOT: Notebook (anomaly_detection.py) çalışmadıysa P3 ölçüleri 14,224K");
Info("     gibi eski veriyi gösterir. Önce notebook'u BACKFILL_MODE=True ile");
Info("     çalıştır, sonra Power BI Refresh.");
