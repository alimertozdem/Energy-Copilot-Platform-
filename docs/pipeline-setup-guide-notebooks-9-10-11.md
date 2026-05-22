# Data Pipeline Setup Guide — Notebooks 9, 10, 11
**Energy Copilot Platform — Microsoft Fabric**  
Updated: 2026-04-17

---

## Overview

Bu rehber, aşağıdaki üç notebook'u Microsoft Fabric Data Pipeline'a nasıl ekleyeceğini adım adım gösterir:

| Notebook | Dosya | Output Tablo | Çalışma Sırası |
|----------|-------|--------------|----------------|
| **09** | `09_ghg_scope_engine.py` | `gold_ghg_scope` | Compute_KPIs'dan sonra |
| **10** | `10_crrem_pathway_loader.py` | `gold_crrem_pathway` | Paralel (başlangıçta) |
| **11** | `11_hvac_analytics_engine.py` | `gold_hvac_analytics` | GHG Scope'dan sonra |

**Referans pipeline JSON:** `pipelines/batch/03_gold_analytics_pipeline.json`  
Bu dosya nihai hedef yapıyı gösterir — aşağıdaki adımlar Fabric UI'da bunu nasıl kuracağını açıklar.

---

## Adım 1 — Fabric'te Pipeline'ı Aç

1. Microsoft Fabric workspace'ine git: `https://app.fabric.microsoft.com`
2. Sol menüden **Data Engineering** → **Data pipelines** seç
3. Mevcut pipeline: **03_gold_analytics_pipeline** varsa bunu aç  
   Yoksa: **+ New pipeline** → isim: `03_gold_analytics_pipeline`

---

## Adım 2 — Mevcut Pipeline Yapısını Anla

`03_gold_analytics_pipeline` şu anda şu aktiviteleri içeriyor (veya içermesi gerekiyor):

```
Compute_KPIs (Notebook 03)
    ↓
Run_Simulation_Engine (Notebook 04)
    ↓
Check_Compliance (Notebook 05)
    ↓
Generate_Recommendations (Notebook 06)
```

**Ekleyeceğimiz yeni aktiviteler:**

```
Load_CRREM_Pathway (Notebook 10) ──────────────────────────┐
                                                           ↓
Compute_KPIs (Notebook 03) ──→ Run_GHG_Scope_Engine (09) ──→ Run_HVAC_Analytics (11) ──→ Gold_Completed
                          ↘                                                             ↗
                           Run_Simulation_Engine → Check_Compliance → Generate_Recs ──┘
```

---

## Adım 3 — Notebook 10 Ekle (Load_CRREM_Pathway)

**Neden paralel?** CRREM pathway tablosu statik referans veridir (2020–2050 yılları, bina tipi × ülke). Hiçbir aktiviteye bağımlı değildir — pipeline başladığında hemen çalışır.

### Adımlar:
1. Pipeline canvas'ında **+ Add activity** → **Notebook** seç
2. Activity name: `Load_CRREM_Pathway`
3. **Settings** sekmesi → **Notebook** alanı → `10_crrem_pathway_loader` seç
4. **Timeout:** `0.00:10:00` (10 dakika — küçük tablo, hızlı çalışır)
5. **Retry:** 1 | **Retry interval:** 30 saniye
6. **Dependency:** Boş bırak (hiçbir aktiviteye bağımlı değil)
7. **Save**

> **Not:** Notebook'un Fabric workspace'inde var olduğundan emin ol.  
> Eğer yoksa: Fabric'te **+ New Notebook** → kod yapıştır → kaydet → pipeline'da seç.

---

## Adım 4 — Notebook 9 Ekle (Run_GHG_Scope_Engine)

**Bağımlılık:** `Compute_KPIs` başarılı olmalı — GHG hesabı `gold_kpi_daily` kullanır.

### Adımlar:
1. **+ Add activity** → **Notebook**
2. Activity name: `Run_GHG_Scope_Engine`
3. Settings → Notebook: `09_ghg_scope_engine`
4. **Timeout:** `0.00:30:00` (30 dakika)
5. **Retry:** 2 | **Retry interval:** 60 saniye
6. **Dependency ekle:**
   - `Run_GHG_Scope_Engine` aktivitesine sağ tıkla → **Add dependency**
   - Kaynak aktivite: `Compute_KPIs`
   - Koşul: **Succeeded** ✓
7. **Save**

### Fabric UI'da bağlantı çizme:
- `Compute_KPIs` aktivitesinin sağ kenarındaki **yeşil** çıkış noktasına tıkla
- Fare ile `Run_GHG_Scope_Engine` aktivitesine çek → bırak
- Bağlantı çizgisi oluşur → koşul otomatik "Succeeded" olur

---

## Adım 5 — Notebook 11 Ekle (Run_HVAC_Analytics)

**Bağımlılık:** `Run_GHG_Scope_Engine` — GHG verisi HVAC'ta opsiyonel enrichment olarak kullanılır.  
**Önemli fark:** Bağımlılık koşulu **Succeeded VEYA Failed** — GHG başarısız olsa bile HVAC çalışmalı.

### Adımlar:
1. **+ Add activity** → **Notebook**
2. Activity name: `Run_HVAC_Analytics`
3. Settings → Notebook: `11_hvac_analytics_engine`
4. **Timeout:** `0.00:30:00`
5. **Retry:** 2 | **Retry interval:** 60 saniye
6. **Dependency ekle (soft dependency):**
   - `Run_GHG_Scope_Engine` aktivitesinin **kırmızı** çıkış noktasına (Failed) tıkla → `Run_HVAC_Analytics`'e çek
   - `Run_GHG_Scope_Engine` aktivitesinin **yeşil** çıkış noktasına (Succeeded) tıkla → `Run_HVAC_Analytics`'e çek
   - Sonuç: HVAC her durumda çalışır (GHG başarılı veya başarısız)

### Neden soft dependency?
Notebook 11 kodu şunu yapar:
```python
try:
    df_ghg = spark.read.format("delta").load(GOLD_GHG_SCOPE)
    HAS_GHG = True
except Exception:
    HAS_GHG = False  # GHG yoksa da çalışmaya devam eder
```
GHG tablosu yoksa Notebook 11 hata vermez, sadece GHG kolonları boş kalır.

---

## Adım 6 — Gold_Completed Wait Aktivitesi Güncelle

`Gold_Completed` aktivitesi tüm gold işlemler bitince tetiklenmeli.

### Mevcut bağımlılıklar:
- `Generate_Recommendations` → Succeeded
- `Detect_Anomalies` → Succeeded

### Eklenecek yeni bağımlılıklar:
- `Run_HVAC_Analytics` → Succeeded
- `Load_CRREM_Pathway` → Succeeded

### Adımlar:
1. `Gold_Completed` aktivitesine tıkla
2. **Dependencies** sekmesi → **+ Add dependency**
3. `Run_HVAC_Analytics` ekle → koşul: **Succeeded**
4. `Load_CRREM_Pathway` ekle → koşul: **Succeeded**
5. **Save**

---

## Adım 7 — Master Orchestrator'ı Güncelle

`04_master_orchestrator.json` dosyasını da güncelle. Fabric'te:

1. **04_master_orchestrator** pipeline'ı aç
2. `Run_Gold_Analytics` aktivitesini bul (Execute Pipeline activity)
3. Bu aktivite `03_gold_analytics_pipeline`'ı çağırıyor → değişiklik gerekmiyor
4. Pipeline `03` içinde yaptığımız değişiklikler otomatik yansır

---

## Adım 8 — Pipeline'ı Test Et

### İlk test (manuel tetikleme):
1. Pipeline canvas'ında **▶ Run** → **Run now** seç
2. **Monitoring** sekmesinden her aktivitenin durumunu izle
3. Beklenen çalışma sırası:

```
t=0:00  → Load_CRREM_Pathway (paralel)    → ~5-8 dk
t=0:00  → Compute_KPIs                    → ~10-20 dk
t=0:20  → Run_GHG_Scope_Engine            → ~8-12 dk
t=0:32  → Run_HVAC_Analytics             → ~8-12 dk
t=0:32  → Run_Simulation_Engine           → (paralel kolda)
...
t=0:55  → Gold_Completed                  → tamamlandı
```

### Başarı kontrolleri:
- ✅ `gold_ghg_scope` tablosu Lakehouse'da görünüyor
- ✅ `gold_crrem_pathway` tablosu Lakehouse'da görünüyor  
- ✅ `gold_hvac_analytics` tablosu Lakehouse'da görünüyor
- ✅ Her üç tabloda da `reporting_year = 2024` satırlar var
- ✅ `gold_hvac_analytics`'te B001 için `insulation_score` ve `system_type` dolu

### Log kontrol:
```
Lakehouse Explorer → Tables → gold_hvac_analytics
→ Sağ tıkla → "Load to new notebook"
→ display(spark.read.format("delta").load("Tables/gold_hvac_analytics").limit(10))
```

---

## Adım 9 — Zamanlama (Schedule)

Günlük otomatik çalıştırma için:

1. Pipeline canvas'ı → **Schedule** → **+ Add schedule**
2. **Recurrence:** Daily
3. **Start time:** `02:00` (gece 2 — peak saati değil)
4. **Time zone:** Kendi timezone'unu seç (CET/CEST)
5. **Save**

> **Uyarı:** Bronze ve Silver pipeline'larının (01 ve 02) Gold'dan önce tamamlanması gerekir.  
> Eğer 01 ve 02 pipeline'larının kendi schedule'ları varsa:
> - 01 Bronze: `00:00`
> - 02 Silver: `00:45`
> - 03 Gold (bu pipeline): `02:00`
> Bu şekilde sıralı çalışma garantilenir.

---

## Sorun Giderme

### Problem: "Notebook not found" hatası
- **Sebep:** Notebook Fabric workspace'inde kayıtlı değil
- **Çözüm:** Fabric'te Data Engineering → Notebooks → notebook dosyasını yükle ve kaydet → pipeline'da notebook ID'yi güncelle

### Problem: `Run_GHG_Scope_Engine` timeout
- **Sebep:** `gold_kpi_daily` büyük bir tabloysa Spark süresi uzuyor
- **Çözüm:** Timeout'u `0.01:00:00` (1 saat) yap + Retry: 2 bırak

### Problem: `Run_HVAC_Analytics` hata veriyor: `AnalysisException: cop_actual_avg`
- **Çözüm:** Notebook 11 v2 (güncel dosya) kullan — fiziksel kolon varlık testi eklendi. Eski versiyonu kullanıyorsan `11_hvac_analytics_engine.py`'yi Fabric'te güncelle.

### Problem: `gold_crrem_pathway` boş tablo
- **Sebep:** `Load_CRREM_Pathway` aktivitesi başarılı görünse de tablo yok
- **Çözüm:** Notebook 10'da `CRREM_CSV_PATH` değişkenini kontrol et — CSV dosyası Lakehouse'da `Files/reference/crrem_pathway.csv` yolunda olmalı

---

## Özet — Nihai Pipeline Yapısı

```
t=0 ────┬─── Load_CRREM_Pathway (10) ────────────────────────┐
        │                                                    ↓
        └─── Compute_KPIs (03) ──→ Run_GHG_Scope_Engine (09) ──→ Run_HVAC_Analytics (11) ──┐
                                ↘                                                           ↓
                                 Run_Simulation_Engine (04) → Check_Compliance (05) →       Gold_Completed
                                                                Generate_Recommendations ───┘
                                 Detect_Anomalies (parallel) ──────────────────────────────┘
```

**Referans dosyalar:**
- `pipelines/batch/03_gold_analytics_pipeline.json` — tam JSON tanımı
- `pipelines/batch/04_master_orchestrator.json` — üst düzey orchestrator
- `notebooks/gold/09_ghg_scope_engine.py`
- `notebooks/gold/10_crrem_pathway_loader.py`
- `notebooks/gold/11_hvac_analytics_engine.py`
