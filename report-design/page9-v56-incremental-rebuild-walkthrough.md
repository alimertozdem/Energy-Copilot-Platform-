# Page 9 v56 — Incremental Rebuild Walkthrough
**Date:** 2026-05-21
**Strategy:** Aşamalı (mevcut çalışan visual'ları koru, yeni measure'lar + yeni visual'lar ekle, eski overlap'ları sil)
**Format:** Single-page 16:9 (yatay scroll yok)
**Tahmini süre:** ~75 dakika

> Notu: Ekran görüntülerine göre Page 9 layout'una uygun, mümkün olduğunca mevcut kutuları yeniden kullanıyoruz.

---

## STEP 0 — TE2 cache fix + v56 install (5 dk)

Bu olmadan diğer adımlar çalışmaz (measure'lar henüz oluşturulmadı).

1. TE2 → **File → Refresh** (veya **Ctrl+R**) — yeni Lakehouse tablolarını sense yapar
2. Sol panelden `gold_battery_dispatch`, `gold_country_regulations`, `gold_strategy_fitness` tablolarını gör — varsa devam
3. **C# Script** tab → yeni script: paste [`page9_v56_relationships.cs`](computer://C:\Energy Management App\Energy-copilot-platform/semantic-model/scripts/page9_v56_relationships.cs) → **F5** → **Ctrl+S**
4. Output: `[CREATE]` veya `[EXISTS]` 2 satır görmelisin
5. Script'i sil → paste [`page9_v56_master_install.cs`](computer://C:\Energy Management App\Energy-copilot-platform/semantic-model/scripts/page9_v56_master_install.cs) → **F5** → **Ctrl+S**
6. Output: `[CREATE]` veya `[UPDATE]` toplam **~26 satır** — `[SKIP]` olmamalı
7. Power BI Desktop → Home → **Refresh**
8. Data panelinde `gold_battery_dispatch > Page 9 / KPI` klasörünü gör: `C1 Annual Savings EUR`, `C2 Payback Years`, vs.

> Tıkanırsan: Ctrl+R'dan sonra TE2 tabloları görmüyorsa → TE2'yi tamamen kapat → Power BI Desktop'tan External Tools → TE2'yi tekrar aç (fresh state).

---

## STEP 1 — KPI kartlarını v56 measure'larıyla rebind (10 dk)

Mevcut 4 kartı koru, sadece field değiştir:

| Kart | Mevcut field (eski) | Yeni v56 field |
|---|---|---|
| **C1 Annual Savings** | `[Annual Savings]` (v47/v50) | `[C1 Annual Savings EUR]` |
| **C2 Payback Period** | `[Payback Years]` (v47) | `[C2 Payback Years]` + callout `[C2 Payback Status Label]` |
| **C3 CO2 Avoided** | `[CO2 Avoided]` (v47) | `[C3 CO2 Avoided Tonnes Annual]` |
| **C4 Efficiency + EU** | birleşik | `[C4 Round Trip Efficiency Pct]` — sadece % gösterir |

**Nasıl:**
1. KPI kartına tıkla → Visualizations → Build visual paneli açılır
2. Mevcut "Value" field'ı (sarı tasarımdaki tek field) çıkar → yeni v56 measure'ını sürükle
3. C2 için: callout label slotuna `[C2 Payback Status Label]` ekle (✓ Excellent gibi gösterir)
4. C4 için: %94,1 / %94,5 değerini koru

**Yeni C5 kartı oluştur:**
1. C4 kartını seç → **Ctrl+C → Ctrl+V** (kopyala)
2. Yeni kartın value'sini `[C5 EU Compliance Status Text]` yap
3. Format → Callout value → text size 14pt (uzun metin sığsın)
4. Pozisyon: C4'ün sağı (4 kart → 5 kart için her birinin genişliğini ~20% daralt)

---

## STEP 2 — Yeni slicer'lar S3 + S4 (5 dk)

Sayfanın üstüne, mevcut "DATE RANGE" slicer'ının yanına:

**S3 Chemistry slicer:**
1. Insert → Slicer
2. Field: `gold_battery_technologies[battery_type]`
3. Format → Slicer settings → Style: **Dropdown** → Selection: **Multi-select with CTRL = OFF**, **Select all = ON**
4. Header text: "Chemistry"
5. Width: ~120px

**S4 Country slicer:**
1. Insert → Slicer
2. Field: `silver_building_master[country_code]`
3. Format → Slicer settings → Style: **Dropdown**, **Single select = ON**
4. Header text: "Country"

**Edit Interactions:**
- Click S3 → ribbon → Format → Edit interactions ON
- S3 → C1, C2, C3, C4, V1, V2, V3, V4, V6, V7 — **None** (S3 sadece V5'i filtreler)
- S4 → C5, V5, I2, I3 — Filter; diğerleri **None**

---

## STEP 3 — V1 Strategy Recommender Matrix (10 dk)

**ROI Gauge'i sil → yerine bu matrisi koy.**

1. Sol alt'taki "ROI GAUGE" visual'ını seç → Delete
2. Insert → Visual → **Matrix**
3. Build pane:
   - **Rows:** `gold_strategy_fitness[building_type]`
   - **Columns:** `gold_strategy_fitness[strategy_label]`
   - **Values:** `[V1 Strategy Fitness Score]`
4. Format → Cell elements → Background color → **fx** (conditional)
   - Format style: **Rules**
   - Based on: `[V1 Strategy Fitness Score]`
   - Add 4 rules:
     - 0 ≤ value < 40 → `#C0392B` (red)
     - 40 ≤ value < 60 → `#E67E22` (orange)
     - 60 ≤ value < 80 → `#F39C12` (amber)
     - 80 ≤ value ≤ 100 → `#27AE60` (green)
5. Format → Values → Font color: white (kontrast için)
6. Format → Title → "Strategy Fitness Matrix"
7. Size: ~480 × 240 px

Sonuç: 7 building_type × 7 strategy = 49 hücreli renkli matrix.

---

## STEP 4 — V5 EU Country × Chemistry Heatmap (10 dk)

**Sayfada yer:** Mevcut "Scenario Comparison" tablosunun **altına** (full-width row).

1. Insert → Visual → **Matrix**
2. Build pane:
   - **Rows:** `gold_country_regulations[country_name]`
   - **Columns:** `gold_battery_technologies[battery_type]`
   - **Values:** `[V5 Country Chemistry Symbol]` (gösterir ✓/⚠/✗)
3. Format → Cell elements → Background color → **fx**
   - Format style: **Rules**
   - Based on: `[V5 Country Chemistry Flag]`
   - Rules:
     - value = -1 → `#C0392B` (red)
     - value = 0 → `#F39C12` (amber)
     - value = 1 → `#27AE60` (green)
4. Format → Values → Font color: white, Font size: 14pt
5. Format → Row headers → Font size: 11pt
6. Format → Column headers → Font size: 11pt, Word wrap: ON
7. Title: "EU Regulation Heatmap — Country × Chemistry"
8. Size: ~960 × 200 px (full-width, kısa)

Sonuç: DE × NMC kırmızı ✗, NO × LFP yeşil ✓, TR × NMC amber ⚠ vs.

---

## STEP 5 — V4 Monthly Net Savings + CO2 (10 dk)

**Sayfada yer:** Mevcut "Monthly Charge / Discharge" visual'ının **YANINA** (sağına) veya altına.

1. Insert → Visual → **Line and clustered column chart**
2. Build pane:
   - **X-axis:** `gold_battery_dispatch[date]` veya varsa `[month_year_en]` (Categorical, ay seviyesinde)
   - **Column y-axis:** `[V4 Monthly Net Savings EUR]`
   - **Line y-axis:** `[V4 Monthly CO2 Avoided Kg]`
   - **Column legend:** `gold_battery_dispatch[strategy_label]`
3. Format → Columns → Color: Emerald palette (`#27AE60`)
4. Format → Lines → Color: Sodium yellow (`#F1C40F`)
5. Title: "Monthly Savings & CO₂ Avoided"
6. Size: ~480 × 240 px

> Eğer mevcut Monthly Charge/Discharge'ı silmek istersen yer açar; ama enerji manager'ları her ikisini görmek ister: V2 = "ne kadar enerji aktardım", V4 = "bundan ne kadar para kazandım".

---

## STEP 6 — V7 Battery Health Strip (10 dk)

**Sayfada yer:** En alta, full-width tek satır. 3 küçük kart yan yana.

1. Insert → Card (3 kez)
2. Kart 1:
   - Value: `[V7 Current SoH Pct]`
   - Title: "Battery Health (SoH)"
   - Format → green if > 90%, amber 80-90%, red < 80% (conditional formatting)
3. Kart 2:
   - Value: `[V7 Cycles Used Pct]`
   - Title: "Cycles Used"
4. Kart 3:
   - Value: `[V7 Years Until Replacement]`
   - Title: "Years to Replacement"
5. Hepsini select et → **Format → Align → Distribute horizontally**
6. Size: her biri ~300 × 100 px

> Bu strip Mert'in "battery sağlık ve replacement planlaması" hikayesini anlatır — Siemens DEMS bile bunu yapmıyor.

---

## STEP 7 — I1-I4 Insight Cards (10 dk)

**Sayfada yer:** V7'nin altı, 4 eşit text card.

Her bir card için:
1. Insert → Card
2. Value field: `[I1 Strategy Recommendation Text]` (I2, I3, I4 için aynı pattern)
3. Format:
   - Callout value → Font size 10pt → Word wrap ON
   - Subtitle → Font size 9pt, gray
4. Title (her birinde farklı):
   - I1: "Recommended Strategy"
   - I2: "Recommended Chemistry"
   - I3: "Compliance Status"
   - I4: "Next Action"
5. Her kartın boyutu: ~240 × 110 px

> Bu prescriptive layer çok kıymetli. Page 5 v54'te aynı pattern büyük başarı sağladı.

---

## STEP 8 — Cleanup (5 dk)

Mevcut artık ihtiyaç dışı:

1. **"Best: Peak-Shaving · Portfolio · 5 buildings wit..." kartı (sol orta)** → Sil
   - Bu I1 Strategy Recommendation Text ile çakışıyor + I1 daha zengin
2. **Eski "Strategy: ★ Best: Peak-Shaving · LFP - 5,600 kWh" kartı** → Sil
   - Bu da Active Battery Label + I2 Chemistry Recommendation ile çakışıyor
3. **Eski Active Strategy "● Peak-Shaving" kartı** varsa → Sil (yenisi: Active Strategy Short Label)
4. Page 9'a sığmayan visual'lar varsa boyutları küçült:
   - Slicer'ların yüksekliği azalt
   - V6 Scenario tablosu görünür satır sayısını 6'ya indir (scroll yine çalışır)

---

## STEP 9 — Final smoke test

[validation checklist](computer://C:\Energy Management App\Energy-copilot-platform/docs/page9_v56_validation_checklist.md) §D-§J'yi adım adım takip et.

Kritik testler:
- [ ] Hamburg seçili → C2 = ~1.7-2 yr ✓ Excellent
- [ ] Frankfurt seçili → C5 = "❌ NMC banned for new installs in DE"
- [ ] All seçili → C1 ≈ €99k (mevcut screenshot'unla uyumlu)
- [ ] V5 heatmap: DE × NMC kırmızı, NO × LFP yeşil
- [ ] I1: Hamburg → "logistics building in DE, primary strategy: Peak-Shaving"
- [ ] I3: Frankfurt → "⚠ Active battery is NMC — banned in DE..."

---

## Eğer yer kalmazsa (fallback)

Tek ekrana sığmazsa şu sırayla küçült/birleştir:

1. V7 Health Strip → tek satır yerine 3 küçük metric in single tooltip page (drilldown)
2. V6 Scenario Table → height küçült (5 satır görünür yeter)
3. V2 Monthly Charge/Discharge ↔ V4 Monthly Net Savings → **bookmark toggle**: aynı yer, iki layout (bir buton ile değiştir)

## Files reference

- [DAX v56 master](computer://C:\Energy Management App\Energy-copilot-platform/semantic-model/68_dax_v56_page9_master.dax)
- [Install script](computer://C:\Energy Management App\Energy-copilot-platform/semantic-model/scripts/page9_v56_master_install.cs)
- [Relationships script](computer://C:\Energy Management App\Energy-copilot-platform/semantic-model/scripts/page9_v56_relationships.cs)
- [Master design doc](computer://C:\Energy Management App\Energy-copilot-platform/docs/page9_v56_master_design.md)
- [Validation checklist](computer://C:\Energy Management App\Energy-copilot-platform/docs/page9_v56_validation_checklist.md)
