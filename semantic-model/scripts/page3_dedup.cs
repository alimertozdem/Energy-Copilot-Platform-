// =============================================================================
// Energy Copilot Platform — Page 3 Deduplicate
// File: semantic-model/scripts/page3_dedup.cs
// Last updated: 2026-05-18
//
// AMAÇ:
//   Model'de aynı isimde birden fazla P3 measure varsa (duplikat), bunları
//   tespit edip her isimden sadece BİR tane bırakır (gold_anomaly_log'daki
//   tercih edilir). Diğerleri silinir.
//
// ÇALIŞTIRMA:
//   1. TE → C# Script → Ctrl+A → Delete → bu dosyayı yapıştır → F5
//   2. Output'ta kaç duplicate bulundu ve silindi gör
//   3. Ctrl+S → Save → Yes
//   4. Power BI'da Page 3 → "See details" kaybolmalı
// =============================================================================

const string PREFIX = "P3 ";
const string PREFERRED_TABLE = "gold_anomaly_log";

// 1. Tüm P3 measure'larını isme göre grupla
var groups = new System.Collections.Generic.Dictionary<string, System.Collections.Generic.List<Measure>>();

foreach (var m in Model.AllMeasures)
{
    if (m.Name.StartsWith(PREFIX))
    {
        if (!groups.ContainsKey(m.Name))
        {
            groups[m.Name] = new System.Collections.Generic.List<Measure>();
        }
        groups[m.Name].Add(m);
    }
}

Info("=== TÜM P3 MEASURE'LARI VE DUPLİKATLARI ===");
Info("");

int totalMeasures = 0;
int totalNames = 0;
int duplicateNames = 0;
int toDeleteCount = 0;

foreach (var kvp in groups)
{
    totalNames++;
    totalMeasures += kvp.Value.Count;

    string status = "";
    if (kvp.Value.Count > 1)
    {
        status = " ⚠️  DUPLİKAT (x" + kvp.Value.Count + ")";
        duplicateNames++;
        toDeleteCount += (kvp.Value.Count - 1);
    }

    Info(kvp.Key + status);
    foreach (var m in kvp.Value)
    {
        Info("  → table: " + m.Table.Name);
    }
}

Info("");
Info("==========================================");
Info("ÖZET:");
Info("  Toplam isim    : " + totalNames);
Info("  Toplam measure : " + totalMeasures);
Info("  Duplikat isim  : " + duplicateNames);
Info("  Silinecek      : " + toDeleteCount);
Info("==========================================");
Info("");

if (duplicateNames == 0)
{
    Info("✅ Duplikat yok — bu hata farklı bir sebepten olabilir.");
    Info("   Power BI'da farklı bir cache sorunu olabilir.");
    Info("   Çözüm: .pbix'i Save → Close → Reopen.");
    return;
}


// 2. Duplikatları temizle — her isim için BİR measure bırak (gold_anomaly_log tercih)
Info("=== DUPLİKAT TEMİZLİĞİ BAŞLIYOR ===");
Info("");

int deletedCount = 0;

foreach (var kvp in groups)
{
    if (kvp.Value.Count <= 1) continue;

    // gold_anomaly_log'daki measure'ı bul (varsa) — onu tut
    Measure keep = null;
    foreach (var m in kvp.Value)
    {
        if (m.Table.Name == PREFERRED_TABLE)
        {
            keep = m;
            break;
        }
    }
    // Yoksa ilk olanı tut
    if (keep == null) keep = kvp.Value[0];

    Info("KEEP: " + keep.Name + " (table: " + keep.Table.Name + ")");

    // Diğerlerini sil
    foreach (var m in kvp.Value)
    {
        if (m != keep)
        {
            Info("  DELETE: " + m.Name + " (table: " + m.Table.Name + ")");
            m.Delete();
            deletedCount++;
        }
    }
}

Info("");
Info("==========================================");
Info("Silinen duplikat : " + deletedCount);
Info("==========================================");
Info("");
Info("SONRAKİ ADIM:");
Info("  1. Ctrl+S → Save changes to model → Yes");
Info("  2. Save BAŞARILI olmalı (sadece silme)");
Info("  3. Power BI'a dön → Page 3 → 'See details' kaybolmalı");
