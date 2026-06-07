// =============================================================================
// Energy Copilot Platform — Page 3 STEP 1: Cleanup Only
// File: semantic-model/scripts/page3_step1_cleanup_only.cs
// Last updated: 2026-05-18
//
// AMAÇ:
//   Tek bir transaction'da delete + add yaptığımızda server "duplicate adı zaten
//   var" diye reject ediyor. Bu scripti çalıştır → SADECE sil → Ctrl+S kaydet.
//   Server temiz state'e gelsin. Sonra step2_install_only.cs çalıştır.
//
// ÇALIŞTIRMA:
//   1. Tabular Editor'da connection'ın aktif olduğundan emin ol
//   2. C# Script tab → mevcut script'i SİL (Ctrl+A → Delete)
//   3. Bu dosyanın tüm içeriğini yapıştır
//   4. F5 (Run Script)
//   5. Confirmation dialog'larına Tamam de (her delete için)
//   6. Output: "Silinen: X" sayısını oku
//   7. Ctrl+S → "Save changes to model" → Yes
//   8. Save BAŞARILI olmalı (duplicate yok artık)
//   9. Devam → page3_step2_install_only.cs
// =============================================================================

const string PREFIX = "P3 ";

Info("=== STEP 1: CLEANUP ALL P3 MEASURES ===");
Info("");

// Tüm "P3 " prefix'li ölçüleri model genelinde topla
var toDelete = new System.Collections.Generic.List<Measure>();
foreach (var m in Model.AllMeasures)
{
    if (m.Name.StartsWith(PREFIX))
    {
        toDelete.Add(m);
    }
}

if (toDelete.Count == 0)
{
    Info("Silinecek P3 ölçüsü yok — temiz state.");
    Info("");
    Info("Devam: page3_step2_install_only.cs çalıştır.");
    return;
}

Info("Silinecek " + toDelete.Count + " ölçü bulundu:");
foreach (var m in toDelete)
{
    Info("  - " + m.Name + "  (table: " + m.Table.Name + ")");
}
Info("");

// Şimdi gerçekten sil
int deletedCount = 0;
foreach (var m in toDelete)
{
    m.Delete();
    deletedCount++;
}

Info("");
Info("==========================================");
Info("Silinen P3 ölçü sayısı: " + deletedCount);
Info("==========================================");
Info("");
Info("SONRAKİ ADIM:");
Info("  1. Ctrl+S → Save changes to model → Yes");
Info("  2. Save BAŞARILI olduğunu doğrula (hata yoksa)");
Info("  3. Sonra: page3_step2_install_only.cs scriptini çalıştır");
