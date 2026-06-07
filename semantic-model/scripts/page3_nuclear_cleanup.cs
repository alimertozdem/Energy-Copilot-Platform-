// =============================================================================
// Energy Copilot Platform — NUCLEAR CLEANUP
// File: semantic-model/scripts/page3_nuclear_cleanup.cs
// Last updated: 2026-05-18
//
// AMAÇ:
//   Önceki TE oturumlarında C# script içeriği yanlışlıkla bazı tabloların
//   DetailRowsExpression alanına yapışmış (Expression Editor tab'ı kazara aktif
//   olduğunda paste yapınca olur). Bu da model validation'ı bozuyor → tüm
//   save'ler reject ediliyor.
//
//   Bu script:
//     1. Tüm tabloların DetailRowsExpression alanlarını temizler (C# kodu
//        içerenleri tespit edip null'lar)
//     2. Tüm "P3 " prefix'li ölçüleri siler (duplicate temizliği)
//     3. SADECE silme yapar — ekleme yok. Save BAŞARILI olmalı.
//
// ÇALIŞTIRMA:
//   1. Tabular Editor'ı tamamen kapat
//   2. Power BI Desktop'tan External Tools → Tabular Editor TEKRAR aç
//      (Bu, stale memory state'i temizler)
//   3. C# Script tab → bu dosyayı yapıştır
//   4. F5 → confirmation'lara Tamam
//   5. Output: Temizlenen tablo + silinen ölçü sayısı
//   6. Ctrl+S → Save
//   7. ✅ Save BAŞARILI olmalı
//   8. Sonra → page3_step2_install_only.cs
// =============================================================================

Info("=== NUCLEAR CLEANUP — Phase 1: Fix Broken DetailRowsExpression ===");
Info("");

int fixedTables = 0;
var brokenTables = new System.Collections.Generic.List<string>();

foreach (var t in Model.Tables)
{
    string expr = null;
    try
    {
        expr = t.DefaultDetailRowsExpression;
    }
    catch
    {
        // Bazı TE versiyonlarında bu property eksik olabilir — atla
        continue;
    }

    if (!string.IsNullOrEmpty(expr))
    {
        // C# kodu işaretleri ara — DAX değil, script artığı
        bool isBroken =
            expr.Contains("foreach") ||
            expr.Contains("Model.AllMeasures") ||
            expr.Contains("Model.Tables") ||
            expr.Contains("System.Action") ||
            expr.Contains("var existing") ||
            expr.Contains("AddMeasure") ||
            expr.Contains("Info(") ||
            expr.Contains("// ====");

        if (isBroken)
        {
            Info("CLEARING DetailRows: " + t.Name);
            brokenTables.Add(t.Name);
            t.DefaultDetailRowsExpression = null;
            fixedTables++;
        }
    }
}

Info("");
Info("Bozuk DetailRowsExpression temizlenen tablo sayısı: " + fixedTables);
if (fixedTables > 0)
{
    Info("Temizlenenler: " + string.Join(", ", brokenTables));
}
Info("");


Info("=== NUCLEAR CLEANUP — Phase 2: Delete All P3 Measures ===");
Info("");

var toDelete = new System.Collections.Generic.List<Measure>();
foreach (var m in Model.AllMeasures)
{
    if (m.Name.StartsWith("P3 "))
    {
        toDelete.Add(m);
    }
}

int deletedCount = 0;
foreach (var m in toDelete)
{
    Info("DELETED: " + m.Name + " (table: " + m.Table.Name + ")");
    m.Delete();
    deletedCount++;
}

Info("");
Info("==========================================");
Info("ÖZET:");
Info("  Bozuk DetailRows temizlenen   : " + fixedTables);
Info("  Silinen P3 measure            : " + deletedCount);
Info("==========================================");
Info("");
Info("ZORUNLU SONRAKI ADIM:");
Info("  1. Ctrl+S → 'Save changes to model' → Yes");
Info("  2. Save BAŞARILI olmalı (sadece silme/temizleme, ekleme yok)");
Info("  3. Save error verirse → bana hatanın tam metnini gönder");
Info("  4. Save başarılıysa → page3_step2_install_only.cs çalıştır");
