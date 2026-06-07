// =============================================================================
// Energy Copilot Platform — Page 3 Fix Date References
// File: semantic-model/scripts/page3_fix_date_refs.cs
// Last updated: 2026-05-18
//
// AMAÇ:
//   4 P3 measure 'Date'[Date] referansı kullanıyordu → "Date tablosu bulunamadı"
//   hatası veriyordu. Bu script onları gold_anomaly_log[detected_date]
//   kolonuna yönlendiriyor — Date table dependency kalkıyor, garantili çalışır.
//
// FİX EDİLEN ÖLÇÜLER:
//   1. P3 Total Anomaly PY
//   2. P3 High Anomaly Previous Month
//   3. P3 Unresolved YoY
//   4. P3 Resolution Rate Pct PY
//
// ÇALIŞTIRMA:
//   1. TE → C# Script → Ctrl+A → Delete → bu dosyayı yapıştır → F5
//   2. Ctrl+S → Save (BAŞARILI olmalı, çünkü sadece 4 expression update)
//   3. Power BI Desktop'ı kontrol et → Page 3 visual'ları düzelmeli
// =============================================================================

const string HOME_TABLE = "gold_anomaly_log";

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

int fixedCount = 0;

System.Action<string, string> updateExpr = (name, expression) =>
{
    Measure existing = null;
    foreach (var m in homeTable.Measures)
    {
        if (m.Name == name) { existing = m; break; }
    }
    if (existing == null)
    {
        Warning("Bulunamadı: " + name);
        return;
    }
    existing.Expression = expression;
    Info("FIXED: " + name);
    fixedCount++;
};


// FİX 1: P3 Total Anomaly PY
updateExpr(
    "P3 Total Anomaly PY",
@"CALCULATE (
    [P3 Total Anomaly Count],
    DATEADD ( gold_anomaly_log[detected_date], -1, YEAR )
)"
);

// FİX 2: P3 High Anomaly Previous Month
updateExpr(
    "P3 High Anomaly Previous Month",
@"CALCULATE (
    [P3 High Anomaly Count],
    DATEADD ( gold_anomaly_log[detected_date], -1, MONTH )
)"
);

// FİX 3: P3 Unresolved YoY
updateExpr(
    "P3 Unresolved YoY",
@"CALCULATE (
    [P3 Unresolved Count],
    DATEADD ( gold_anomaly_log[detected_date], -1, YEAR )
)"
);

// FİX 4: P3 Resolution Rate Pct PY
updateExpr(
    "P3 Resolution Rate Pct PY",
@"VAR _resolved_py =
    CALCULATE (
        COUNTROWS ( gold_anomaly_log ),
        gold_anomaly_log[is_resolved] = TRUE,
        DATEADD ( gold_anomaly_log[detected_date], -1, YEAR )
    )
VAR _total_py =
    CALCULATE (
        [P3 Total Anomaly Count],
        DATEADD ( gold_anomaly_log[detected_date], -1, YEAR )
    )
RETURN
    ROUND ( DIVIDE ( _resolved_py, _total_py, 0 ) * 100, 1 )"
);


Info("");
Info("==========================================");
Info("Fix edilen ölçü sayısı: " + fixedCount + " / 4");
Info("==========================================");
Info("");
Info("SONRAKİ ADIM:");
Info("  1. Ctrl+S → Save changes to model → Yes");
Info("  2. 'Objects with errors' panel → 5 errors → 1 error'a düşmeli");
Info("     (kalan 1 = U-Value Categories pre-existing, bizimle ilgili değil)");
Info("  3. Power BI Desktop → Page 3 → 'See details' kaybolmalı");
