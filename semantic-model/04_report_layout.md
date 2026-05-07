# EnergyLens — Power BI Rapor Layout Rehberi
## Final Versiyon — Sayfa Sayfa, Görsel Görsel, Alan Alan
**Versiyon:** v5 Final  
**Tarih:** 2026-04-16  
**Model:** EnergycopilotModel (Live Connection)

---

## ⚠️ BAŞLAMADAN ÖNCE — 4 Zorunlu Adım

Bu adımları raporu açar açmaz yap, sonrasında tek visual bozuk kalmasın.

### Adım 1 — Date Tablosunu İşaretle (Time Intelligence için zorunlu)
1. Power BI Desktop → sol menüde **Model** ikonuna tıkla
2. Sol panelde `Date` tablosunu bul → **sağ tıkla**
3. **"Mark as date table"** seç
4. Açılan pencerede **`Date[Date]`** kolonunu seç → **OK**
5. ✅ Tablonun yanında 📅 ikonu çıkmalı

### Adım 2 — MonthIndex Hesaplanmış Kolonu Ekle (X ekseni kronolojik sıra)
1. Model görünümünde `Date` tablosunu seç
2. Üstten **"New column"** tıkla
3. Formül yaz:
   ```dax
   MonthIndex = YEAR('Date'[Date]) * 100 + MONTH('Date'[Date])
   ```
4. `Date[YearMonth]` kolonuna sağ tıkla → **"Sort by column"** → `MonthIndex`

### Adım 3 — Day Name Kolonu Ekle (Sayfa 5 Heat Map için)
1. `gold_occupancy_profile` tablosunu seç → **"New column"**
2. Formül yaz:
   ```dax
   Day Name TR =
   SWITCH(gold_occupancy_profile[day_of_week],
       0, "0-Pzt", 1, "1-Sal", 2, "2-Çar",
       3, "3-Per", 4, "4-Cum", 5, "5-Cmt", 6, "6-Paz", "?"
   )
   ```
3. `Day Name TR` kolonuna sağ tıkla → **"Sort by column"** → `day_of_week`

### Adım 4 — % Format Kuralı (EN KRİTİK)
> Tüm `*Pct` ölçüleri DAX'ta **zaten 0–100 arasında sayı** döndürür.
> Kart/grafik format string'ini **`0.0`** yap. **`0%` kullanma** → 2587% hatası.

---

## ═══════════════════════════════════════
## SAYFA 1 — Portfolio Overview
## ═══════════════════════════════════════
**Başlık:** `Portfolio Overview`
**Alt başlık:** `Building Portfolio Intelligence`
**Amaç:** Tüm portföyü tek bakışta — yönetici özeti

---

### 🔲 SLICER PANELİ (sol şerit — dikey)

4 slicer, birbirinin altına:

| Slicer # | Görsel Tipi | Fields → Field | Format seçeneği |
|---|---|---|---|
| 1 | Date range slicer | `Date[Date]` | Style: Between |
| 2 | Dropdown slicer | `silver_building_master[building_name]` | Multi-select: ON |
| 3 | Dropdown slicer | `silver_building_master[city]` | Multi-select: ON |
| 4 | Dropdown slicer | `silver_building_master[building_type]` | Multi-select: ON |

> ⚠️ Fazla slicer varsa (özellikle birden fazla "Building Name") **hepsini sil**, yukarıdaki 4'ü yeniden ekle.

---

### 🔲 SATIR 1 — 5 KPI KARTI (yan yana, üst satır)

#### Kart 1 — Total Energy Consumption

| Ayar | Değer |
|---|---|
| **Görsel tipi** | KPI veya Card |
| **Fields → Value** | `[Total Consumption kWh]` |
| **Fields → Target goals** | `[Total Energy PY kWh]` |
| **Format → Callout value → Format** | `#,##0` |
| **Format → Callout value → Display units** | None |
| **Başlık** | `Total Energy Consume kWh` |

> `[Total Energy PY kWh]` = Geçen yıl aynı dönem tüketimi. KPI kartı otomatik % fark hesaplar.
> ✅ Beklenen: ~2,955,169 kWh (tüm 2024, 3 bina)

---

#### Kart 2 — Avg EUI

| Ayar | Değer |
|---|---|
| **Görsel tipi** | KPI veya Card |
| **Fields → Value** | `[Avg EUI kWh m2]` |
| **Fields → Target goals** | `[EUI Target Daily]` (sabit = 0.27) |
| **Format → Callout value → Format** | `0.000` ← **3 ondalık basamak zorunlu** |
| **Format → Callout value → Display units** | None |
| **Başlık** | `Avg EUI (kWh/m²/day)` |

> ⚠️ **Sıfır gösteriyorsa:** Format string `0.000` yap (0 veya #,##0 değil).
> ✅ Beklenen: ~0.350 kWh/m²/gün

---

#### Kart 3 — Active Anomalies

| Ayar | Değer |
|---|---|
| **Görsel tipi** | KPI veya Card |
| **Fields → Value** | `[Active Anomaly Count]` |
| **Fields → Target goals** | `[Anomaly Count PY Same Period]` |
| **Format → Callout value → Format** | `#,##0` |
| **Format → Callout value → Display units** | None |
| **Format → Callout value → Font color** | Kırmızı: `#E74C3C` |
| **Başlık** | `Active Anomalies` |

> ⚠️ **Target goals alanını boş bırakma** → KPI kartı "vs" satırı göstermez.
> ✅ Beklenen: ~4,067 (tüm aktif anomaliler)

---

#### Kart 4 — Total Energy Cost

| Ayar | Değer |
|---|---|
| **Görsel tipi** | KPI veya Card |
| **Fields → Value** | `[Total Energy Cost EUR]` |
| **Fields → Target goals** | `[Previous Year Cost EUR]` |
| **Format → Callout value → Format** | `€ #,##0` |
| **Format → Callout value → Display units** | None |
| **Başlık** | `Total Energy Cost (€)` |

> ✅ Beklenen: ~681,000 €

---

#### Kart 5 — Net Carbon Footprint ⚠️ HATA DÜZELTME

| Ayar | Değer |
|---|---|
| **Görsel tipi** | KPI veya Card |
| **Fields → Value** | `[Net Carbon Footprint tCO2]` ← **BU OLMALI** |
| **Fields → Target goals** | `[Previous Year Net Carbon tCO2]` |
| **Format → Callout value → Format** | `#,##0.0` |
| **Format → Callout value → Display units** | None |
| **Başlık** | `Net Carbon Footprint (tCO₂)` |

> 🔴 **Mevcut hata:** Kart `[Total Consumption kWh]` ölçüsüne bağlı, bu yüzden 2,955,169 gösteriyor.
> **Düzeltme:** Fields → Value alanındaki mevcut ölçüyü kaldır (×) → `[Net Carbon Footprint tCO2]` ekle.
> ✅ Beklenen: ~928 tCO₂

---

### 🔲 SATIR 2 — ORTA ALAN (sol + sağ)

#### Sol — Building-Based Consumption (Clustered Bar Chart)

**Görsel tipi:** Clustered bar chart (yatay)

| Fields Alanı | Eklenecek Alan |
|---|---|
| **Y axis** | `silver_building_master[building_name]` |
| **X axis** | `[Total Consumption kWh]` |
| **Line values** (ikincil eksen) | `[Avg EUI kWh m2]` |
| **Tooltips** | `[Total Energy Cost EUR]`, `[Active Anomaly Count]`, `[Net Carbon Footprint tCO2]` |

**Format ayarları:**

| Ayar | Değer |
|---|---|
| X axis → Format | `#,##0` |
| X axis → Display units | None |
| Secondary Y axis (EUI) → Format | `0.000` |
| Data labels → ON | Format: `#,##0` |
| Sort | `[Total Consumption kWh]` Descending |
| **Başlık** | `Building-Based Consumption (kWh)` |

**Conditional Formatting (çubuk rengi — EUI'ya göre):**
1. Görseli seç → Format → **Data colors** → **fx** tıkla
2. Format by: **Field value** → Alan: **`[EUI Benchmark Tier]`**
3. Kural: 1=`#2ECC71`, 2=`#F39C12`, 3=`#FF6B35`, 4=`#E74C3C`

---

#### Sağ — Anomaly Summary Table

**Görsel tipi:** Table (Tablo)

| Fields Alanı | Eklenecek Alan | Sütun Başlığı | Format |
|---|---|---|---|
| **Column 1** | `silver_building_master[building_name]` | `Building` | — |
| **Column 2** | `[Active Anomaly Count]` | `Active` | `#,##0` |
| **Column 3** | `[Critical Anomaly Count]` | `Critical` | `#,##0` |
| **Column 4** | `[Active Anomaly Rate Pct]` | `Rate (%)` | `0.0` |

**Sıralama:** `[Active Anomaly Count]` Descending

**Conditional Formatting (Kritik > 0 ise kırmızı):**
1. Tablo → Column 3 seç → Format → **Conditional formatting** → **Background color** → ON
2. Rules: Değer > 0 → arka plan `#E74C3C`, yazı rengi `#FFFFFF`

**Başlık:** `Anomaly Count by Building`

> ⚠️ **Mevcut hata:** Tabloda `COUNT(anomaly_id)` ham alanı var → her bina için 4067 gösteriyor.
> **Düzeltme:** O sütunu kaldır, yukarıdaki DAX measure'larını ekle.

---

### 🔲 SATIR 3 — ALT ALAN (sol + sağ)

#### Sol — Monthly Energy Trend (Line Chart)

**Görsel tipi:** Line chart

| Fields Alanı | Eklenecek Alan | Seri Adı | Renk |
|---|---|---|---|
| **X axis** | `Date[YearMonth]` | — | — |
| **Y axis → Line 1** | `[Total Consumption kWh]` | `Consumption` | `#0F4C81` kalın |
| **Y axis → Line 2** | `[Total Energy PY kWh]` | `Prior Year` | `#95A5A6` kesikli |
| **Y axis → Line 3** | `[Energy Reduction Target kWh]` | `Target` | `#2ECC71` noktalı |
| **Tooltips** | `[Total Solar Generated kWh]`, `[Total Energy Cost EUR]` | — | — |

**Format ayarları:**

| Ayar | Değer |
|---|---|
| X axis → Sort by | `Date[MonthIndex]` (Adım 2'de kuruldu) |
| Y axis → Format | `#,##0` |
| Y axis → Display units | None |
| **Başlık** | `Monthly Energy Trend (kWh)` |

---

#### Sağ — EUI Benchmark by Building (Bar Chart)

**Görsel tipi:** Clustered bar chart (yatay)

| Fields Alanı | Eklenecek Alan |
|---|---|
| **Y axis** | `silver_building_master[building_name]` |
| **X axis** | `[Avg EUI kWh m2]` |
| **Tooltips** | `[EUI Benchmark Status]`, `[EUI Target Daily]` |

**Format ayarları:**

| Ayar | Değer |
|---|---|
| X axis → Format | `0.000` |
| X axis → Display units | None |
| X axis → Min | 0 |
| X axis → Max | 0.70 |
| Data labels → ON | Format: `0.000` |
| **Başlık** | `EUI Benchmark by Building` |

**Reference Line (0.27 benchmark):**
1. Görsel seçli → **Analytics** pane (büyüteç ikonu) → **Constant line** → Add
2. Value: `0.27` / Label: `Excellent` / Renk: `#2ECC71` / Style: Dashed

**Conditional Formatting (renk — EUI değerine göre):**
1. Format → Data colors → **fx** → Format by: Rules
2. Kural 1: ≤ 0.27 → `#2ECC71`
3. Kural 2: > 0.27 ve ≤ 0.41 → `#F39C12`
4. Kural 3: > 0.41 → `#E74C3C`

---

## ═══════════════════════════════════════
## SAYFA 2 — Building Detail
## ═══════════════════════════════════════
**Başlık:** `Building Detail`
**Alt başlık:** `Deep Operational Analysis`
**Amaç:** Tek bina derinlemesine inceleme

---

### 🔲 SLICER PANELİ

| Slicer # | Field | Tür | Seçenek |
|---|---|---|---|
| 1 | `Date[Date]` | Date range | Style: Between |
| 2 | `silver_building_master[building_name]` | Dropdown | **Single select: ON** ← zorunlu |

> ⚠️ Birden fazla Building Name slicer varsa hepsini sil, sadece 1 tane bırak.

---

### 🔲 SATIR 1 — 6 KPI KARTI

| Kart | Fields → Value | Fields → Target goals | Format | Display units |
|---|---|---|---|---|
| Avg Daily Consumption | `[Avg Daily Consumption kWh]` | `[Avg Daily Consumption 30Day Rolling]` | `#,##0.0` | None |
| Peak Demand | `[Peak Demand kW]` | `[Avg Peak Demand 30Day kW]` | `#,##0.0` | None |
| EUI | `[Avg EUI kWh m2]` | `[EUI Target Daily]` | `0.000` | None |
| Solar Generated | `[Total Solar Generated kWh]` | — | `#,##0.0` | None |
| Battery SoC ⚠️ | `[Avg Battery SoC Pct]` | — | `0.0` ← **"0%" DEĞİL** | None |
| Carbon Intensity | `[Avg Carbon Intensity kg m2]` | — | `0.000` | None |

> ⚠️ `[Avg Battery SoC Pct]` formatı `0%` olursa 7450% görürsün → `0.0` yap.

---

### 🔲 SATIR 2 — ORTA ALAN

#### Sol — Consumption & Temperature (Çift Eksenli Çizgi)

**Görsel tipi:** Line chart

| Fields Alanı | Alan | Renk |
|---|---|---|
| **X axis** | `Date[YearMonth]` (Sort by: MonthIndex) | — |
| **Column y-axis** | `[Total Consumption kWh]` | `#0F4C81` mavi |
| **Line y-axis** (ikincil) | `[Avg Temperature C]` | `#FF6B35` turuncu, kesikli |
| **Tooltips** | `[Total HDD]`, `[Total CDD]` | — |

**Format:** Y sol `#,##0` / Y sağ `0.0` / Display units: None / **Başlık:** `Consumption vs Temperature`

---

#### Sağ — EUI Gauge

**Görsel tipi:** Gauge

| Fields Alanı | Alan |
|---|---|
| **Value** | `[Avg EUI kWh m2]` |
| **Minimum value** | `0` |
| **Target value** | `[EUI Target Daily]` |
| **Maximum value** | `0.70` |

**Format:** `0.000` / Target renk: `#2ECC71` / **Başlık:** `EUI Performance Gauge (kWh/m²/day)`

---

### 🔲 SATIR 3 — SOLAR & BATARYA

#### Sol — Solar vs Consumption (Line and Stacked Column)

**Görsel tipi:** Line and stacked column chart

| Fields Alanı | Alan | Renk |
|---|---|---|
| **X axis** | `Date[YearMonth]` (Sort by: MonthIndex) | — |
| **Column y-axis → Seri 1** | `[Solar Self Consumed kWh]` | `#F39C12` sarı |
| **Column y-axis → Seri 2** | `SUM(gold_kpi_daily[solar_exported_kwh])` | `#F1C40F` açık sarı |
| **Line y-axis** (ikincil) | `[Total Grid Consumption kWh]` | `#95A5A6` gri |

**Format:** Y `#,##0` / Display units: None / **Başlık:** `Solar Energy & Grid Consumption (kWh)`

---

#### Sağ — Battery SoC Range (Area Chart)

**Görsel tipi:** Area chart

| Fields Alanı | Alan | Renk |
|---|---|---|
| **X axis** | `gold_kpi_daily[date]` | — |
| **Y axis → Seri 1** | `SUM(gold_kpi_daily[battery_soc_min_pct])` | `#AED6F1` |
| **Y axis → Seri 2** | `SUM(gold_kpi_daily[battery_soc_max_pct])` | `#2E86C1` |

**Format ayarları:**

| Ayar | Değer |
|---|---|
| Y axis → Format | `0.0` ← **"0%" DEĞİL** |
| Y axis → Display units | **None** ← "K" olursa 0.0K hatası |
| Y axis → Min | 0 |
| Y axis → Max | 100 |
| **Başlık** | `Battery SoC Range (%)` |

---

### 🔲 SATIR 4 — HDD / CDD SCATTER

#### Sol — HDD vs Consumption

**Görsel tipi:** Scatter chart | X: `SUM(gold_kpi_daily[hdd_day])` | Y: `[Total Consumption kWh]` | Details: `gold_kpi_daily[date]` | Format X: `0.0`, Y: `#,##0` | **Başlık:** `Heating Degree Days vs Consumption`

#### Sağ — CDD vs Consumption

**Görsel tipi:** Scatter chart | X: `SUM(gold_kpi_daily[cdd_day])` | Y: `[Total Consumption kWh]` | Details: `gold_kpi_daily[date]` | Format X: `0.0`, Y: `#,##0` | **Başlık:** `Cooling Degree Days vs Consumption`

---

## ═══════════════════════════════════════
## SAYFA 3 — Anomalies & Alerts
## ═══════════════════════════════════════
**Başlık:** `Anomalies & Alerts`
**Alt başlık:** `Fault Detection & Response`
**Amaç:** Aktif anomaliler, trend ve öncelik analizi

---

### 🔲 SLICER PANELİ

| Slicer # | Field | Tür |
|---|---|---|
| 1 | `Date[Date]` | Date range |
| 2 | `silver_building_master[building_name]` | Dropdown, multi-select |
| 3 | `gold_anomaly_log[severity]` | Dropdown, multi-select |
| 4 | `gold_anomaly_log[anomaly_type]` | Dropdown, multi-select |
| 5 | `gold_anomaly_log[is_resolved]` | Dropdown, tek seçim |

---

### 🔲 SATIR 1 — 5 KPI KARTI

| Kart | Fields → Value | Fields → Target goals | Format |
|---|---|---|---|
| Total Anomalies | `[Total Anomaly Count]` | — | `#,##0` |
| Critical Open ⚠️ | `[Critical Anomaly Open Count]` | — | `#,##0` |
| High Priority | `[High Anomaly Count]` | `[High Anomaly Count Previous Week]` | `#,##0` |
| Unresolved | `[Unresolved Count]` | `[Unresolved Count Previous Week]` | `#,##0` |
| Active Rate ⚠️ | `[Active Anomaly Rate Pct]` | — | `0.0` ← **"0%" DEĞİL** |

> `[Critical Anomaly Open Count]` = kritik + çözülmemiş → hiç yoksa 0 döner, BLANK değil.

---

### 🔲 SATIR 2 — ORTA ALAN

#### Sol — Anomaly Detail Table (60% genişlik)

**Görsel tipi:** Table

| Field | Sütun Başlığı | Format |
|---|---|---|
| `silver_building_master[building_name]` | `Building` | — |
| `gold_anomaly_log[severity]` | `Severity` | — |
| `gold_anomaly_log[anomaly_type]` | `Type` | — |
| `gold_anomaly_log[detected_date]` | `Detected` | `DD.MM.YYYY` |
| `gold_anomaly_log[metric_value]` | `Value` | `#,##0.00` |
| `gold_anomaly_log[is_resolved]` | `Resolved` | — |

**Sıralama:** `detected_date` Descending

**Conditional Formatting (severity sütunu arka planı):**
1. Tablo → `severity` sütununu seç → Format → **Cell elements** → **Background color** → fx
2. Format by: **Rules**
3. Kural 1: "critical" → `#E74C3C` / Kural 2: "high" → `#FF6B35` / Kural 3: "medium" → `#F39C12`

**Başlık:** `Active Anomaly List`

---

#### Sağ — Anomaly Type Distribution (Donut Chart)

**Görsel tipi:** Donut chart | Legend: `gold_anomaly_log[anomaly_type]` | Values: `[Total Anomaly Count]` | Format: `#,##0` | **Başlık:** `Anomaly Type Distribution`

---

### 🔲 SATIR 3 — ALT ALAN

#### Sol — Monthly Anomaly Trend (Stacked Column)

**Görsel tipi:** Stacked column chart

| Fields Alanı | Alan |
|---|---|
| **X axis** | `Date[YearMonth]` (Sort by: MonthIndex) |
| **Y axis** | `[Total Anomaly Count]` |
| **Legend** | `gold_anomaly_log[severity]` |

**Severity renkleri (manuel ata):** critical=`#E74C3C` / high=`#FF6B35` / medium=`#F39C12` / low=`#95A5A6`

**Format:** Y `#,##0` / Display units: None / **Başlık:** `Monthly Anomaly Trend by Severity`

---

#### Sağ — Building Anomaly Distribution (100% Stacked Bar)

**Görsel tipi:** 100% Stacked bar chart | Y: `silver_building_master[building_name]` | X: `[Total Anomaly Count]` | Legend: `gold_anomaly_log[severity]` | **Başlık:** `Anomaly Distribution by Building`

---

## ═══════════════════════════════════════
## SAYFA 4 — Forecast & Recommendations
## ═══════════════════════════════════════
**Başlık:** `Forecast & Recommendations`
**Alt başlık:** `Predictive Energy Intelligence`
**Amaç:** Tüketim tahmini + verimlilik önerileri

---

### 🔲 SLICER PANELİ

| Slicer # | Field | Tür |
|---|---|---|
| 1 | `Date[Date]` | Date range |
| 2 | `silver_building_master[building_name]` | Dropdown |
| 3 | `gold_recommendations[action_type]` | Multi-select |

---

### 🔲 ÜST BÖLÜM — FORECAST

#### Forecast KPI Kartları (3 adet)

| Kart | Fields → Value | Format | Display units |
|---|---|---|---|
| 7-Day Forecast | `[Forecast 7Day kWh]` | `#,##0.0` | None |
| Model MAPE ⚠️ | `[Avg Model MAPE Pct]` | `0.0` ← **"0%" DEĞİL** | None |
| Forecast Days | `[Forecast Period Days]` | `#,##0` | None |

---

#### Sol — Forecast Line Chart (60% genişlik)

**Görsel tipi:** Line chart

| Fields Alanı | Alan | Renk |
|---|---|---|
| **X axis** | `gold_consumption_forecast[forecast_date]` | — |
| **Y axis → Line 1** | `[Predicted Consumption kWh]` | `#0F4C81` kalın |
| **Y axis → Line 2** | `[Forecast Lower Bound kWh]` | `#AED6F1` kesikli |
| **Y axis → Line 3** | `[Forecast Upper Bound kWh]` | `#AED6F1` kesikli |

**Format:** Y `#,##0` / Display units: None / X sort: Ascending

> ⚠️ **Grafik boşsa:** Model view → `gold_consumption_forecast[forecast_date]` → Data type: **Date**

**Başlık:** `Consumption Forecast with Confidence Interval`

---

#### Sağ — MAPE by Building (Bar Chart)

**Görsel tipi:** Clustered bar chart | Y: `silver_building_master[building_name]` | X: `[Avg Model MAPE Pct]` | Tooltips: `[MAPE Bucket]`

**Format:** X `0.0` / **"0%" DEĞİL** / Data labels: ON

**Conditional Formatting:** ≤10 → `#2ECC71` / 10–20 → `#F39C12` / >20 → `#E74C3C`

**Başlık:** `Model Accuracy by Building (MAPE %)`

---

### 🔲 ALT BÖLÜM — RECOMMENDATIONS

#### Öneri KPI Kartları (4 adet)

| Kart | Fields → Value | Format |
|---|---|---|
| Expected Annual Savings | `[Expected Annual Savings EUR]` | `€ #,##0` |
| Total CO₂ Saving | `[Total CO2 Saving tCO2]` | `#,##0.0` |
| Net Investment | `[Total Net Investment EUR]` | `€ #,##0` |
| Avg Payback | `[Avg Payback Years]` | `0.0` |

---

#### Sol — Recommendations Table (50% genişlik)

**Görsel tipi:** Table

| Field | Başlık | Format |
|---|---|---|
| `silver_building_master[building_name]` | `Building` | — |
| `gold_recommendations[action_type]` | `Action Type` | — |
| `gold_recommendations[priority_label]` | `Priority` | — |
| `gold_recommendations[annual_saving_eur]` | `Annual Saving (€)` | `€ #,##0` |
| `gold_recommendations[payback_years]` | `Payback (yr)` | `0.0` |
| `gold_recommendations[capex_eur]` | `CAPEX (€)` | `€ #,##0` |
| `gold_recommendations[grant_eur]` | `Grant (€)` | `€ #,##0` |

**Sıralama:** `priority_score` Descending

**Conditional Formatting (Priority sütunu):** "CRITICAL"=`#E74C3C` / "HIGH"=`#FF6B35` / "MEDIUM"=`#F39C12`

**Başlık:** `Efficiency Recommendations`

---

#### Sağ — ROI Scatter Chart (50% genişlik)

**Görsel tipi:** Scatter chart

| Fields Alanı | Alan |
|---|---|
| **X axis** | `gold_recommendations[payback_years]` |
| **Y axis** | `gold_recommendations[annual_saving_eur]` |
| **Size** | `gold_recommendations[capex_eur]` |
| **Color saturation** | `gold_recommendations[action_type]` |
| **Details** | `gold_recommendations[title_en]` |
| **Tooltips** | `priority_label`, `grant_eur`, `net_capex_eur` |

**Format:** X `0.0` / Y `€ #,##0` / **Başlık:** `Payback vs Annual Savings (ROI Analysis)`

> Sol üst köşe = en iyi yatırım (düşük geri ödeme + yüksek tasarruf).

---

## ═══════════════════════════════════════
## SAYFA 5 — Occupancy Analysis
## ═══════════════════════════════════════
**Başlık:** `Occupancy Analysis`
**Alt başlık:** `Space-Energy Correlation`
**Amaç:** Doluluk profili ve enerji israfı tespiti

---

### 🔲 SLICER PANELİ

| Slicer # | Field | Tür |
|---|---|---|
| 1 | `Date[Date]` | Date range |
| 2 | `silver_building_master[building_name]` | Dropdown |
| 3 | `gold_occupancy_profile[profile_source]` | Dropdown |

---

### 🔲 SATIR 1 — 4 KPI KARTI

| Kart | Fields → Value | Format | Not |
|---|---|---|---|
| Business Hours Occupancy ⚠️ | `[Avg Business Hours Occupancy Pct]` | `0.0` | **"0%" DEĞİL → 2587%** |
| After Hours Occupancy ⚠️ | `[Avg After Hours Occupancy Pct]` | `0.0` | **"0%" DEĞİL** |
| Peak Occupancy Hour | `[Peak Occupancy Hour]` | `0` | Tam sayı saat |
| Phantom Load Risk ⚠️ | `[Phantom Load Risk Pct]` | `0.0` | **"0%" DEĞİL** |

**After Hours Conditional Formatting (arka plan):**
- Değer > 40 → `#E74C3C`
- 20 < Değer ≤ 40 → `#F39C12`

---

### 🔲 SATIR 2 — HEAT MAP (tam genişlik) ⚠️ DETAYLI KURULUM

**Görsel tipi:** Matrix

**Adım 1 — Fields panelini kur:**

| Fields Alanı | Alan |
|---|---|
| **Rows** | `gold_occupancy_profile[Day Name TR]` ← Adım 3'te oluşturuldu |
| **Columns** | `gold_occupancy_profile[hour_of_day]` |
| **Values** | `[Avg Occupancy Probability]` ← 0–1 arası, ×100 yapılmamış |

> `[Avg Occupancy Probability]` = `AVERAGE(gold_occupancy_profile[occupancy_probability])`
> Bu ölçü ×100 yapmaz — gradyan renklendirme için 0–1 aralığı gerekli.

**Adım 2 — Format paneli:**

| Ayar | Değer |
|---|---|
| Values → Format | `0.00` |
| Column sizing → Auto-size columns | OFF, genişlik: 35px |
| Word wrap | OFF |

**Adım 3 — Conditional Formatting (renk gradyanı) — ZORUNLU:**
1. Matrix seçli → **Format** pane → **Cell elements** bölümünü bul
2. **Background color** → Toggle **ON**
3. **fx** düğmesine tıkla
4. "Format by" → **Gradient** seç
5. Ayarları gir:

| Nokta | Değer | Renk |
|---|---|---|
| **Minimum** | 0.00 | `#FFFFFF` (beyaz) |
| **Middle** | 0.50 | `#7FB3D3` (orta mavi) |
| **Maximum** | 1.00 | `#1A5276` (koyu lacivert) |

6. **Apply** → OK

✅ Sonuç: 7 satır (Pzt–Paz) × 24 sütun (00–23) → doluluk yoğunluğu renkle gösterilir.

**Başlık:** `Weekly & Hourly Occupancy Heatmap`

---

### 🔲 SATIR 3 — ALT ALAN

#### Sol — Building Occupancy Comparison (Clustered Bar)

**Görsel tipi:** Clustered bar chart

| Fields Alanı | Alan | Renk |
|---|---|---|
| **Y axis** | `silver_building_master[building_name]` | — |
| **X axis → Seri 1** | `[Avg Business Hours Occupancy Pct]` | `#0F4C81` |
| **X axis → Seri 2** | `[Avg After Hours Occupancy Pct]` | `#FF6B35` |

**Format:** X `0.0` / **"0%" DEĞİL** / Display units: None / **Başlık:** `Business vs After-Hours Occupancy (%)`

---

#### Sağ — Hourly Occupancy Profile (Line Chart)

**Görsel tipi:** Line chart

| Fields Alanı | Alan |
|---|---|
| **X axis** | `gold_occupancy_profile[hour_of_day]` |
| **Y axis** | `[Avg Occupancy Probability]` |
| **Legend** | `silver_building_master[building_type]` |

**Format:** X Min=0, Max=23 / Y `0.00`, Min=0, Max=1 / **Başlık:** `Hourly Occupancy Profile by Building Type`

---

## ═══════════════════════════════════════
## SAYFA 6 — Sustainability & Compliance
## ═══════════════════════════════════════
**Başlık:** `Sustainability & Compliance`
**Alt başlık:** `Carbon Management & ESG Reporting`
**Amaç:** ESG raporlama, karbon ayak izi, uyumluluk

---

### 🔲 SLICER PANELİ

| Slicer # | Field | Tür |
|---|---|---|
| 1 | `Date[Date]` | Date range |
| 2 | `silver_building_master[building_name]` | Dropdown |
| 3 | `silver_building_master[country_code]` | Dropdown |

---

### 🔲 SATIR 1 — 5 KPI KARTI

| Kart | Fields → Value | Fields → Target goals | Format |
|---|---|---|---|
| CO₂ Emissions | `[Total CO2 Emissions tCO2]` | `[Previous Year CO2 Emissions tCO2]` | `#,##0.0` |
| Solar CO₂ Savings | `[CO2 Savings Tons]` | — | `#,##0.0` |
| Net Carbon Footprint ⚠️ | `[Net Carbon Footprint tCO2]` | — | `#,##0.0` |
| Renewable Energy Rate ⚠️ | `[Renewable Energy Rate Pct]` | — | `0.0` ← **"0%" DEĞİL** |
| Carbon Intensity | `[Carbon Intensity kgCO2 m2 yr]` | — | `0.0` |

> ⚠️ Net Carbon Footprint kartı boşsa `[Net Carbon Footprint tCO2]` ekle → ~928 tCO₂ görünmeli.
> ⚠️ Renewable Rate `0%` formatıyla 2016% görünür → `0.0` yap.

---

### 🔲 SATIR 2 — ORTA ALAN

#### Sol — Monthly CO₂ Trend (Line Chart, 3 çizgi)

**Görsel tipi:** Line chart

| Fields Alanı | Alan | Renk |
|---|---|---|
| **X axis** | `Date[YearMonth]` (Sort by: MonthIndex) | — |
| **Y axis → Line 1** | `[Total CO2 Emissions tCO2]` | `#E74C3C` kırmızı |
| **Y axis → Line 2** | `[CO2 Savings Tons]` | `#2ECC71` yeşil |
| **Y axis → Line 3** | `[Net Carbon Footprint tCO2]` | `#95A5A6` gri, kesikli |

**Format:** Y `0.0` / Display units: None / **Başlık:** `Monthly CO₂ Trend (tCO₂)`

---

#### Sağ — Emissions by Country (Clustered Bar)

**Görsel tipi:** Clustered bar chart

| Fields Alanı | Alan | Renk |
|---|---|---|
| **Y axis** | `silver_building_master[country_code]` | — |
| **X axis → Seri 1** | `[Total CO2 Emissions tCO2]` | `#E74C3C` |
| **X axis → Seri 2** | `[CO2 Savings Tons]` | `#2ECC71` |

**Format:** X `0.0` / Display units: None / **Başlık:** `Emissions & Savings by Country (tCO₂)`

---

### 🔲 SATIR 3 — ALT ALAN

#### Sol — HDD/CDD Climate Analysis (Clustered Column)

**Görsel tipi:** Clustered column chart

| Fields Alanı | Alan | Renk |
|---|---|---|
| **X axis** | `Date[YearMonth]` (Sort by: MonthIndex) | — |
| **Y axis → Seri 1** | `[Total HDD]` | `#2E86C1` mavi |
| **Y axis → Seri 2** | `[Total CDD]` | `#FF6B35` turuncu |

**Format:** Y `0.0` / Display units: None / **Başlık:** `Monthly Heating & Cooling Load (HDD / CDD)`

---

#### Sağ — CO₂ Emission Sources (Treemap) ⚠️

**Görsel tipi:** Treemap

> ⚠️ **Görsel tipi yanlışsa:** Görseli seç → Visualizations panelinden **Treemap** ikonunu tıkla.

| Fields Alanı | Alan |
|---|---|
| **Category** | `silver_building_master[building_name]` |
| **Values** | `[Total CO2 Emissions tCO2]` |
| **Details** | `[Avg Carbon Intensity kg m2]` |
| **Tooltips** | `[Net Carbon Footprint tCO2]`, `[CO2 Savings Tons]`, `[Renewable Energy Rate Pct]` |

**Format:** Data labels ON / Values: `0.0 tCO₂` / **Başlık:** `CO₂ Emission Sources by Building`

---

## ══════════════════════════════════
## GENEL KURALLAR — TÜM SAYFALAR
## ══════════════════════════════════

### Renk Paleti

| Amaç | Hex |
|---|---|
| Ana mavi | `#0F4C81` |
| Uyarı turuncu | `#FF6B35` |
| Başarı yeşil | `#2ECC71` |
| Kritik kırmızı | `#E74C3C` |
| Orta sarı | `#F39C12` |
| Nötr gri | `#95A5A6` |

### Severity Renkleri (Tüm grafiklerde tutarlı)

| Değer | Hex |
|---|---|
| critical | `#E74C3C` |
| high | `#FF6B35` |
| medium | `#F39C12` |
| low | `#95A5A6` |

### Format String Özeti

| Ölçü Tipi | Doğru Format | Yanlış |
|---|---|---|
| kWh (büyük) | `#,##0` | K/M kısaltmalı |
| kWh (küçük) | `#,##0.0` | — |
| € | `€ #,##0` | K kısaltmalı |
| **% (Pct ölçüleri)** | **`0.0`** | **`0%` ← YASAK** |
| EUI | `0.000` | `0` veya `#,##0` |
| tCO₂ | `#,##0.0` | — |
| Tarih | `DD.MM.YYYY` | Otomatik |
| Count | `#,##0` | K kısaltmalı |

### Display Units — Her Görselde

> Tüm kartlar ve grafik eksenlerinde: **Display units = None**

### Beklenen Değerler (Tüm 2024, 3 bina)

| Ölçü | Beklenen |
|---|---|
| `[Total Consumption kWh]` | ~2,955,169 |
| `[Total Energy Cost EUR]` | ~681,000 € |
| `[Active Anomaly Count]` | ~4,067 |
| `[Net Carbon Footprint tCO2]` | ~928 tCO₂ |
| `[Avg EUI kWh m2]` | ~0.350 |
| `[Solar Coverage Pct]` | ~20–30 (format: 0.0) |
| `[Avg Business Hours Occupancy Pct]` | ~50–65 (format: 0.0) |
| `[Renewable Energy Rate Pct]` | ~20–30 (format: 0.0) |
| `[Forecast 7Day kWh]` | ~58,000–60,000 |
| `[Total Annual Saving EUR]` | ~46,565 € |
