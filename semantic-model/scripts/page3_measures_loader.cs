// =============================================================================
// Energy Copilot Platform — Page 3 Anomalies & Alerts Measure Loader
// File: semantic-model/scripts/page3_measures_loader.cs
// Last updated: 2026-05-18
//
// AMAÇ:
//   Sayfa 3 (Anomalies & Alerts) için 5 eksik ölçüyü Tabular Editor üzerinden
//   tek tıkla yükler. Mevcutsa overwrite eder (idempotent → güvenle re-run).
//
// EKLENEN / GÜNCELLENEN ÖLÇÜLER (hepsi home table: gold_anomaly_log):
//   1. P3 Resolution Rate Pct          → Resolution Rate (%) kartı
//   2. P3 Resolution Rate Pct PY       → PY reference label
//   3. P3 Top Risk Building Score      → Top Risk Building Score kartı (FIX)
//   4. P3 Top Risk Building Name       → Top Risk Building subtitle / tooltip
//   5. P3 Active Anomaly Rate Pct      → Active Anomaly Rate % kartı
//
// ÇALIŞTIRMA (Tabular Editor 2 veya 3):
//   1. Power BI Desktop'ta .pbix dosyasını AÇIK tut.
//   2. External Tools → Tabular Editor (kuruluysa) veya tabulareditor.com indir.
//   3. Tabular Editor → File → Open → From DB → "localhost:XXXXX" semantic model'i seç.
//      (Veya External Tools'tan tek tık ile açılır — model otomatik bağlanır.)
//   4. C# Script tab'ı → bu dosyanın TÜM içeriğini yapıştır.
//   5. F5 (Run Script) — Output pane'de "CREATED" / "UPDATED" satırlarını gör.
//   6. File → Save (Ctrl+S) → değişiklikler Power BI Desktop'a yazılır.
//   7. Power BI Desktop → ölçüleri Fields pane'inde gör → kartlara bind et.
//
// DOĞRULAMA:
//   Script sonunda Output pane: "=== Page 3 measures yüklendi: 5 ölçü ==="
//   Yoksa: "Error: Home table 'gold_anomaly_log' not found" → tablo adını doğrula.
// =============================================================================

const string HOME_TABLE     = "gold_anomaly_log";
const string DISPLAY_FOLDER = "P3 - Anomalies & Alerts";

// ── Home table kontrolü ─────────────────────────────────────────────────────
// NOT (TE2 fix): TableCollection .Find() destekemez — LINQ FirstOrDefault kullan.
Table homeTable = null;
foreach (var t in Model.Tables)
{
    if (t.Name == HOME_TABLE) { homeTable = t; break; }
}
if (homeTable == null)
{
    var sb = new System.Text.StringBuilder();
    foreach (var t in Model.Tables) { sb.Append(t.Name); sb.Append(", "); }
    Error("Home table '" + HOME_TABLE + "' not found. Aborting.\nMevcut tablolar: " + sb.ToString());
    return;
}

// ── Bağımlılık kontrolü: P3 Total Anomaly Count ve P3 Unresolved Count olmalı ─
string[] requiredMeasures = new string[] { "P3 Total Anomaly Count", "P3 Unresolved Count" };
foreach (var reqName in requiredMeasures)
{
    Measure found = null;
    foreach (var m in Model.AllMeasures)
    {
        if (m.Name == reqName) { found = m; break; }
    }
    if (found == null)
    {
        Warning("Bağımlılık eksik: '" + reqName + "' ölçüsü bulunamadı.\n" +
                "Önce v21 (P3 Clean Measures) dosyasını yükle — bu script çalışır ama " +
                "ölçüler BLANK dönecek.");
    }
}

// ── Helper: Upsert measure ──────────────────────────────────────────────────
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


// ────────────────────────────────────────────────────────────────────────────
// 1. P3 Resolution Rate Pct
//    Kart: Resolution Rate (%) | Format: 0.0
//    Renk: >60 → #00E5A0 | 30-60 → #FFC107 | <30 → #FF4560
// ────────────────────────────────────────────────────────────────────────────
upsert(
    "P3 Resolution Rate Pct",
@"VAR _resolved =
    CALCULATE (
        COUNTROWS ( gold_anomaly_log ),
        gold_anomaly_log[is_resolved] = TRUE
    )
VAR _total = [P3 Total Anomaly Count]
RETURN
    ROUND ( DIVIDE ( _resolved, _total, 0 ) * 100, 1 )",
    "0.0"
);

// ────────────────────────────────────────────────────────────────────────────
// 2. P3 Resolution Rate Pct PY
//    Reference Label / PY karşılaştırma
// ────────────────────────────────────────────────────────────────────────────
upsert(
    "P3 Resolution Rate Pct PY",
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
    "0.0"
);

// ────────────────────────────────────────────────────────────────────────────
// 3. P3 Top Risk Building Score   ★ FIX ★
//    v23'teki TOPN-inside-CALCULATE patterni filter context oluşturmuyor
//    → measure her zaman portföy toplamını döndürüyordu.
//    Bu versiyon: önce ADDCOLUMNS ile bina başına unresolved tablosu kur,
//    sonra TOPN ile en yüksek olanı MAXX ile al.
// ────────────────────────────────────────────────────────────────────────────
upsert(
    "P3 Top Risk Building Score",
@"VAR _tbl =
    ADDCOLUMNS (
        VALUES ( silver_building_master[building_name] ),
        ""@cnt"", [P3 Unresolved Count]
    )
RETURN
    MAXX ( TOPN ( 1, _tbl, [@cnt], DESC ), [@cnt] )",
    "#,##0"
);

// ────────────────────────────────────────────────────────────────────────────
// 4. P3 Top Risk Building Name
//    Subtitle veya Reference Label olarak kullanılır (text measure)
// ────────────────────────────────────────────────────────────────────────────
upsert(
    "P3 Top Risk Building Name",
@"VAR _tbl =
    ADDCOLUMNS (
        VALUES ( silver_building_master[building_name] ),
        ""@cnt"", [P3 Unresolved Count]
    )
RETURN
    MAXX ( TOPN ( 1, _tbl, [@cnt], DESC ), silver_building_master[building_name] )",
    ""
);

// ────────────────────────────────────────────────────────────────────────────
// 5. P3 Active Anomaly Rate Pct
//    Kart: Active Anomaly Rate %
//    Yorum: Open/Total — 100 ise resolved=0 (notebook bug) demektir
// ────────────────────────────────────────────────────────────────────────────
upsert(
    "P3 Active Anomaly Rate Pct",
@"VAR _open = [P3 Unresolved Count]
VAR _total = [P3 Total Anomaly Count]
RETURN
    ROUND ( DIVIDE ( _open, _total, 0 ) * 100, 1 )",
    "0.0"
);


// ── ÖZET ──────────────────────────────────────────────────────────────────
Info("");
Info("======================================================");
Info("=== Page 3 measures yüklendi: " + (createdCount + updatedCount) + " ölçü ===");
Info("   Created : " + createdCount);
Info("   Updated : " + updatedCount);
Info("======================================================");
Info("Sonraki adım: Ctrl+S ile kaydet → Power BI Desktop'a dön → Fields pane'den ölçüleri görsel'lere bind et.");
