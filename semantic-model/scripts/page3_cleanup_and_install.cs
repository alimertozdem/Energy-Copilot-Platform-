// =============================================================================
// Energy Copilot Platform — Page 3 CLEANUP + INSTALL (Duplicate Fix)
// File: semantic-model/scripts/page3_cleanup_and_install.cs
// Last updated: 2026-05-18
//
// AMAÇ:
//   Önceki page3_full_install.cs script'i model-wide unique check yapmıyordu
//   → bazı P3 ölçüleri başka tablolarda var olduğu için duplicate oluştu
//   → model invalid → tüm visual'lar "See details" hatası
//
// BU SCRIPT:
//   PHASE 1 — Model'deki TÜM "P3 " prefix'li ölçüleri sil (duplikleri temizler)
//   PHASE 2 — 23 ölçüyü temiz şekilde gold_anomaly_log'a yükle
//   PHASE 3 — Diagnostic raporu
//
// VISUAL BINDING:
//   Power BI ölçü referanslarını İSİM ile çözer → delete+recreate sonrası
//   mevcut görsel bağlantıları otomatik restore olur.
//
// ÇALIŞTIRMA:
//   Tabular Editor → C# Script → bu dosyayı yapıştır → F5 → Ctrl+S → Save
// =============================================================================

const string HOME_TABLE     = "gold_anomaly_log";
const string DISPLAY_FOLDER = "P3 - Anomalies & Alerts";
const string PREFIX         = "P3 ";

// ── Home table kontrolü ─────────────────────────────────────────────────────
Table homeTable = null;
foreach (var t in Model.Tables)
{
    if (t.Name == HOME_TABLE) { homeTable = t; break; }
}
if (homeTable == null)
{
    Error("Home table '" + HOME_TABLE + "' bulunamadı.");
    return;
}

// =============================================================================
// PHASE 1 — CLEANUP: Tüm "P3 *" ölçülerini sil
// =============================================================================

Info("=== PHASE 1: CLEANUP ===");

var toDelete = new System.Collections.Generic.List<Measure>();
foreach (var m in Model.AllMeasures)
{
    if (m.Name.StartsWith(PREFIX))
    {
        toDelete.Add(m);
    }
}

int deletedCount = 0;
foreach (var m in toDelete)
{
    Info("DELETED: " + m.Name + " (was on table: " + m.Table.Name + ")");
    m.Delete();
    deletedCount++;
}

Info("Silinen ölçü sayısı: " + deletedCount);
Info("");

// =============================================================================
// PHASE 2 — INSTALL: 23 ölçüyü temiz şekilde ekle
// =============================================================================

Info("=== PHASE 2: INSTALL ===");

int createdCount = 0;

System.Action<string, string, string> add = (name, expression, format) =>
{
    var m = homeTable.AddMeasure(name, expression);
    m.FormatString  = format;
    m.DisplayFolder = DISPLAY_FOLDER;
    Info("CREATED: " + name);
    createdCount++;
};


// ── v21 BASE — KPI CARDS C1-C5 + V6/V8/V9 ────────────────────────────────────

add("P3 Total Anomaly Count",
@"COUNTROWS ( gold_anomaly_log )",
"#,##0");

add("P3 Total Anomaly PY",
@"CALCULATE (
    [P3 Total Anomaly Count],
    DATEADD ( 'Date'[Date], -1, YEAR )
)",
"#,##0");

add("P3 Critical Open Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""CRITICAL"",
    gold_anomaly_log[is_resolved] = FALSE
)",
"#,##0");

add("P3 High Anomaly Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""HIGH""
)",
"#,##0");

add("P3 High Anomaly Previous Month",
@"CALCULATE (
    [P3 High Anomaly Count],
    DATEADD ( 'Date'[Date], -1, MONTH )
)",
"#,##0");

add("P3 Unresolved Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[is_resolved] = FALSE
)",
"#,##0");

add("P3 Unresolved YoY",
@"CALCULATE (
    [P3 Unresolved Count],
    DATEADD ( 'Date'[Date], -1, YEAR )
)",
"#,##0");

add("P3 Data Quality Score",
@"AVERAGE ( silver_data_quality[quality_score_pct] )",
"0.0");

add("P3 Data Quality Target",
@"VAR _target = 95
RETURN _target",
"0.0");

add("P3 Medium Anomaly Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""MEDIUM""
)",
"#,##0");

add("P3 Critical Anomaly Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""CRITICAL""
)",
"#,##0");

add("P3 Low Anomaly Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[severity] = ""LOW""
)",
"#,##0");

add("P3 Anomaly Deviation Pct",
@"VAR _metric    = AVERAGE ( gold_anomaly_log[metric_value] )
VAR _threshold = AVERAGE ( gold_anomaly_log[threshold_value] )
RETURN
    IF (
        NOT ISBLANK ( _threshold ) && ABS ( _threshold ) > 0,
        DIVIDE ( _metric - _threshold, ABS ( _threshold ) ) * 100,
        BLANK ()
    )",
"+0.0;-0.0;—");


// ── v22 SUPPLEMENTARY ────────────────────────────────────────────────────────

add("P3 Building Anomaly Share Pct",
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

add("P3 Anomaly Status",
@"IF (
    MAX ( gold_anomaly_log[is_resolved] ),
    ""Resolved"",
    ""Open""
)",
"");


// ── v23 INSIGHT CARDS (BOTTOM ROW) ───────────────────────────────────────────

add("P3 Avg Days Open",
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

add("P3 High Priority Open Count",
@"CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[is_resolved] = FALSE,
    gold_anomaly_log[severity] IN { ""CRITICAL"", ""HIGH"" }
)",
"#,##0");

add("P3 After Hours Waste Rate Pct",
@"VAR _ahw =
    CALCULATE (
        COUNTROWS ( gold_anomaly_log ),
        gold_anomaly_log[anomaly_type] = ""AFTER_HOURS_WASTE""
    )
RETURN
    ROUND ( DIVIDE ( _ahw, [P3 Total Anomaly Count], 0 ) * 100, 1 )",
"0.0");


// ── 2026-05-18 PAGE 3 FIX ────────────────────────────────────────────────────

add("P3 Resolution Rate Pct",
@"VAR _resolved =
    CALCULATE (
        COUNTROWS ( gold_anomaly_log ),
        gold_anomaly_log[is_resolved] = TRUE
    )
VAR _total = [P3 Total Anomaly Count]
RETURN
    ROUND ( DIVIDE ( _resolved, _total, 0 ) * 100, 1 )",
"0.0");

add("P3 Resolution Rate Pct PY",
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

add("P3 Top Risk Building Score",
@"VAR _tbl =
    ADDCOLUMNS (
        VALUES ( silver_building_master[building_name] ),
        ""@cnt"", [P3 Unresolved Count]
    )
RETURN
    MAXX ( TOPN ( 1, _tbl, [@cnt], DESC ), [@cnt] )",
"#,##0");

add("P3 Top Risk Building Name",
@"VAR _tbl =
    ADDCOLUMNS (
        VALUES ( silver_building_master[building_name] ),
        ""@cnt"", [P3 Unresolved Count]
    )
RETURN
    MAXX ( TOPN ( 1, _tbl, [@cnt], DESC ), silver_building_master[building_name] )",
"");

add("P3 Active Anomaly Rate Pct",
@"VAR _open = [P3 Unresolved Count]
VAR _total = [P3 Total Anomaly Count]
RETURN
    ROUND ( DIVIDE ( _open, _total, 0 ) * 100, 1 )",
"0.0");


// =============================================================================
// PHASE 3 — DIAGNOSTIC
// =============================================================================

Info("");
Info("=== PHASE 3: DIAGNOSTIC ===");

// Tüm P3 ölçülerinin nerede olduğunu doğrula
int p3Total = 0;
foreach (var m in Model.AllMeasures)
{
    if (m.Name.StartsWith(PREFIX))
    {
        p3Total++;
        if (m.Table.Name != HOME_TABLE)
        {
            Warning("BEKLENMEYEN: '" + m.Name + "' tablosu '" + m.Table.Name + "' (olması gereken: gold_anomaly_log)");
        }
    }
}

Info("");
Info("==========================================");
Info("ÖZET:");
Info("  Silinen (cleanup) : " + deletedCount);
Info("  Eklenen (install) : " + createdCount);
Info("  Şu an mevcut P3   : " + p3Total);
Info("==========================================");
Info("");
Info("SONRAKİ ADIM:");
Info("  1. Ctrl+S → Save changes to model → Yes");
Info("  2. Power BI Desktop'a dön → otomatik refresh");
Info("  3. Page 3 visual'ları kontrol et");
Info("     - 'See details' hataları kaybolmalı");
Info("     - Mevcut binding'ler restore olmalı");
Info("");
Info("HÂLÂ HATA VARSA:");
Info("  - Power BI'da Home → Refresh tıkla");
Info("  - Veya .pbix'i kapat+aç");
