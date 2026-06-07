# Page 7 — HVAC & Building Envelope · v37 FINAL IMPLEMENTATION PLAN

**Status:** READY TO APPLY · 2026-05-04  
**Background:** `report-design/backgrounds/07_hvac_building_envelope_sidebar.png`  
**Layout:** Sol panel (slicerlar) + 6 KPI kart + V1–V5 (5 görsel)  
**DAX kaynakları:**
- `43_dax_v34_page7_hvac_self_contained.dax` — C1–C5, V1, V2 temel ölçüler  
- `44_dax_v35_page7_hvac_allexcept_fix.dax` — V2/V5 ALLEXCEPT fix + U-Value Actual  
- `45_dax_v36_page7_format_and_precomputed.dax` — Pre-computed alternatifler  
- `46_dax_v37_page7_c6_co2_and_layout.dax` — **C6 HVAC CO₂ (YENİ)**  

---

## BÖLÜM 0 — ARKA PLAN DEĞİŞİKLİĞİ (2 dk)

### 0.1 — Eski arka planı değiştir
**Format pane → Page background:**
1. **Image:** `07_hvac_building_envelope_sidebar.png` seç
2. **Image fit:** Fit
3. **Transparency:** 0%

### 0.2 — Canvas boyutu kontrolü
Sayfa ayarları → Type: Custom · Width: **1280** · Height: **720**

---

## BÖLÜM 1 — DAX İMPORT (5 dk)

v35, v36, v37 henüz import edilmediyse:

**Power BI DAX Query View → her dosyayı sırayla aç, içeriği yapıştır → Run (▶)**

1. `44_dax_v35_page7_hvac_allexcept_fix.dax` → import
2. `45_dax_v36_page7_format_and_precomputed.dax` → import
3. `46_dax_v37_page7_c6_co2_and_layout.dax` → import

**Data pane'de şunlar görünmeli:**
| Ölçü | Tablo |
|---|---|
| `HVAC CO2 tCO2 v37` | gold_hvac_analytics |
| `System Type Display v35` | gold_hvac_analytics |
| `Renovation Priority Icon v35` | gold_hvac_analytics |
| `COP Display v35` | gold_hvac_analytics |
| `Action Recommendation v35` | gold_hvac_analytics |
| `Renovation Priority Color v35` | gold_hvac_analytics |
| `U-Value Actual` | gold_hvac_analytics |
| `HVAC Share Pct v36` | gold_hvac_analytics |
| `Heat Loss kWh m2 Annual v36` | gold_hvac_analytics |

> **Not:** Eğer `U-Value Categories` calculated table henüz yoksa Bölüm 5.1'de oluşturulacak.

---

## BÖLÜM 2 — VİZÜELLERİ SİL VE YENİDEN YERLEŞTIR

**Eski layout** (5 slicer üstte + 5 card + 5 visual) tamamen farklıydı.  
En temiz yaklaşım: **tüm sayfadaki görselleri sil → sıfırdan yeniden yerleştir.**

> Eski görselleri taşımak yerine silmek daha hızlıdır çünkü pozisyon + binding aynı anda değişecek.

**Home → Select all (Ctrl+A) → Delete**

---

## BÖLÜM 3 — SLICERLAR (SOL PANEL) — 5 slicer (10 dk)

Her slicer için: **Insert → Slicer** ekle → **Format** → pozisyon gir → **Field** bağla

### Ortak Slicer Format Ayarları
```
Background: Transparency 100%
Border: Off
Header: Off (arka planda label var — çakışmasın)
Visual header: Off
Items → Font: Segoe UI 10pt · Color: #C8DCF0
```

### S1 — Date Range (Mavi)
| Ayar | Değer |
|---|---|
| X | 13 | Y | 87 | W | 180 | H | 52 |
| Field | `Date[Date]` veya `Date[YearMonth]` |
| Slicer style | Between (tarih aralığı) |
| Border | 1px #00D4FF |

### S2 — Country (Amber)
| X | 13 | Y | 157 | W | 180 | H | 31 |
|---|---|---|---|---|---|---|---|
| Field | `silver_building_master[country]` |
| Slicer style | Dropdown |
| Border | 1px #FFC107 |

### S3 — Building Type (Turuncu)
| X | 13 | Y | 205 | W | 180 | H | 31 |
|---|---|---|---|---|---|---|---|
| Field | `silver_building_master[building_type]` |
| Slicer style | Dropdown |
| Border | 1px #FF6B35 |

### S4 — System Type (Yeşil)
| X | 13 | Y | 253 | W | 180 | H | 31 |
|---|---|---|---|---|---|---|---|
| Field | `gold_hvac_analytics[system_type]` |
| Slicer style | Tile (daha görsel) veya Dropdown |
| Border | 1px #1D9E75 |

### S5 — Building (Kırmızı)
| X | 13 | Y | 301 | W | 180 | H | 31 |
|---|---|---|---|---|---|---|---|
| Field | `silver_building_master[building_name]` |
| Slicer style | Dropdown |
| Border | 1px #E24B4A |

---

## BÖLÜM 4 — 6 KPI KART (15 dk)

Tüm kartlar için ortak format:
```
Visual type: Card (new)
Background: Transparency 100%
Border: Off
Title: Off
Visual header: Off
Callout value → Font: Segoe UI Semibold, 32pt, #FFFFFF
Callout value → Display units: None
Label → Font: Segoe UI, 10pt, #7DB4DC
```

### C1 — HVAC SHARE % (Turuncu #FF6B35)
| Konum | X=215, Y=78, W=169, H=90 |
|---|---|
| **Measure** | `HVAC Share Pct v34` |
| **Format → Callout value** | Custom: `0.0"%"` · Display units: None |
| **Callout label** | "HVAC Share" |
| **Beklenen (All)** | 35–55 % |

> **Pipeline öncesi:** ~16% görebilirsin (HDD bug). Pipeline re-run sonrası 35-55% olacak.

### C2 — HVAC EFFICIENCY (Amber #FFC107)
| Konum | X=392, Y=78, W=169, H=90 |
|---|---|
| **Measure** | `HVAC Efficiency v34` |
| **Format** | 0.0 · Display units: None |
| **Callout label** | "Efficiency Score" |
| **Beklenen (All)** | 42–58 |

### C3 — AVG INSULATION (Yeşil #1D9E75)
| Konum | X=569, Y=78, W=169, H=90 |
|---|---|
| **Measure** | `Insulation Score v34` |
| **Format** | 0.0 · Display units: None |
| **Callout label** | "Avg Insulation Score" |
| **Beklenen (All)** | 62–78 |

### C4 — HEAT LOSS kWh/m² (Mavi #00D4FF)
| Konum | X=746, Y=78, W=169, H=90 |
|---|---|
| **Measure** | `Heat Loss kWh m2 Annual v34` |
| **Format → Callout value** | Custom: `0.0" kWh/m²"` · Display units: None |
| **Callout label** | "Heat Loss Annual" |
| **Beklenen (All)** | 60–110 kWh/m² |

> **Pipeline öncesi:** ~17 görebilirsin. Pipeline re-run sonrası 60-110 olacak.

### C5 — RETROFIT NEEDED (Kırmızı #E24B4A)
| Konum | X=923, Y=78, W=169, H=90 |
|---|---|
| **Measure** | `Retrofit Count v34` |
| **Format** | 0 (tam sayı) · Display units: None |
| **Callout label** | "Buildings for Retrofit" |
| **Beklenen (All)** | 1–3 (pipeline sonrası 3+) |

### C6 — HVAC CO₂ tCO₂/yr · YENİ (Mor #9B59B6)
| Konum | X=1100, Y=78, W=169, H=90 |
|---|---|
| **Measure** | `HVAC CO2 tCO2 v37` |
| **Format → Callout value** | Custom: `0.0" tCO₂"` · Display units: None |
| **Callout label** | "HVAC CO₂ Emissions" |
| **Beklenen (All binalar, 12 ay)** | 240–345 tCO₂ |
| **CSRD notu** | Gas binalar scope 1 riski, HP scope 2 |

> **Neden C6 ekledik?**  
> HVAC CO₂ emisyonu CSRD/ESRS E1 kapsamında zorunlu raporlanacak (2026+).  
> Enerji yöneticisi "kaç ton CO₂ tasarruf eder gas→HP geçişi?" sorusunu doğrudan bu karttan görür.  
> HP olan Berliner (~18 tCO₂) vs Gas olan Amsterdam (~60 tCO₂) farkı çarpıcı olacak.

---

## BÖLÜM 5 — V1: HVAC ENERGY BREAKDOWN (15 dk)

**Visual type:** Stacked column chart (veya stacked area)  
**Konum:** X=215, Y=182, W=519, H=211  
**Format:** Background 100% transparent · Border Off · Title Off

| Slot | Field |
|---|---|
| X-axis | `Date[YearMonth]` → Sort by `Date[MonthIndex]` |
| Y-axis — Heating | `Heating Energy kWh v34` |
| Y-axis — Cooling | `Cooling Energy kWh v34` |
| Y-axis — Ventilation | `Ventilation Energy kWh v34` |
| Legend | Auto (3 series göster) |

**Data Colors:**
- Heating Energy kWh v34 → `#E24B4A` (kırmızı-sıcak)
- Cooling Energy kWh v34 → `#00D4FF` (mavi-soğuk)
- Ventilation Energy kWh v34 → `#FFC107` (amber)

**X-axis:** Color `#4A6E96` · Font 9pt  
**Y-axis:** Title "kWh" · Color `#4A6E96`  
**Legend:** Top · Color `#7DB4DC` · Font 9pt  
**Gridlines:** `#0E1E38`

**Beklenen:**
- Kış (Dec-Feb): Heating bar dominant (%70+)
- Yaz (Jun-Aug): Cooling bar görünür, heating minimal
- Ventilation her ay sabit ~%15

---

## BÖLÜM 6 — V2: BUILDING HVAC SYSTEM SUMMARY (10 dk)

**Visual type:** Table  
**Konum:** X=742, Y=182, W=528, H=211  
**Format:** Background 100% transparent · Border Off · Title Off

**Sütunlar (sırayla):**

| # | Sütun adı (Power BI'da) | Field/Measure | Not |
|---|---|---|---|
| 1 | Building | `silver_building_master[building_name]` | Kolon |
| 2 | System | `System Type Display v35` | ⚠️ v35 — ALLEXCEPT fix |
| 3 | Priority | `Renovation Priority Icon v35` | ⚠️ v35 |
| 4 | COP Rating | `COP Display v35` | ⚠️ v35 |
| 5 | Insulation | `Insulation Score v34` | v34 çalışıyor |
| 6 | Heat Loss | `Heat Loss kWh m2 Annual v34` | v34 çalışıyor |
| 7 | Action | `Action Recommendation v35` | ⚠️ v35 |

**Tablo Format:**
```
Header → Font: Segoe UI Semibold, 10pt, #7DB4DC · Background: #060E24
Values → Font: Segoe UI, 9pt, #C8DCF0
Banded rows → Alternate: #070F20
Row padding: 4px
Grid: Horizontal only, #0E1E38
```

**Beklenen V2 çıktısı:**
```
Berliner Bürogebäude   🔵 Heat Pump    🟢 Low    3.xx   82  38 kWh/m²  Monitor SCOP & service
Amsterdam Universiteit 🟠 Gas Boiler   🔴 High   n/a    38  88 kWh/m²  Switch to ASHP + insulate
Frankfurt Klinikum     🟠 Gas Boiler   🔴 High   n/a    55  72 kWh/m²  Switch to ASHP + insulate
Hamburg Logistics      🟠 Gas Boiler   🟡 Medium n/a    68  52 kWh/m²  Plan ASHP retrofit by 2030
Istanbul Office        🟠 Gas Boiler   🟡 Medium n/a    62  60 kWh/m²  Plan ASHP retrofit by 2030
Wien Office            🟠 Gas Boiler   🟡 Medium n/a    60  65 kWh/m²  Plan ASHP retrofit by 2030
```

---

## BÖLÜM 7 — V3: ENVELOPE U-VALUES (10 dk)

### 7.1 — Calculated Table (henüz yoksa)
**Modeling → New table:**
```dax
U-Value Categories =
DATATABLE (
    "Component", STRING, "SortIdx", INTEGER, "Reference_GEG", DOUBLE,
    {
        { "Wall",   1, 0.24 },
        { "Roof",   2, 0.20 },
        { "Floor",  3, 0.30 },
        { "Window", 4, 1.30 }
    }
)
```

### 7.2 — Visual Bind
**Visual type:** Clustered bar chart (horizontal)  
**Konum:** X=215, Y=405, W=346, H=307  
**Format:** Background 100% transparent · Border Off · Title Off

| Slot | Field |
|---|---|
| Y-axis | `U-Value Categories[Component]` → Sort by `SortIdx` |
| X-axis | `U-Value Actual` (v35'te import edildi — doğru kolon adları: `wall_u_value` vs) |

**Reference line:** X-axis → + Add reference line → `U-Value Categories[Reference_GEG]`
- Style: Dashed · Color: `#E24B4A` · Label: "GEG 2023" · Font: `#E24B4A`, 8pt

**Format:**
- X-axis title: "W/m²K" · Color `#4A6E96`
- Data color: `#00D4FF`
- Bar labels: On · Color `#FFFFFF` · Font 9pt

**Beklenen (All binalar ortalaması):**
```
Wall:   ~0.35–0.55 W/m²K  (GEG target: 0.24)
Roof:   ~0.20–0.35 W/m²K  (GEG target: 0.20)
Floor:  ~0.28–0.45 W/m²K  (GEG target: 0.30)
Window: ~1.4–2.1 W/m²K    (GEG target: 1.30)
```
→ Tüm bileşenler GEG 2023 hedefini aşıyor olmalı (portföy yenileme ihtiyacı görünür)

---

## BÖLÜM 8 — V4: INSULATION SCORE BY BUILDING (5 dk)

**Visual type:** Clustered bar chart (horizontal)  
**Konum:** X=569, Y=405, W=346, H=307  
**Format:** Background 100% transparent · Border Off · Title Off

| Slot | Field |
|---|---|
| Y-axis | `silver_building_master[building_name]` |
| X-axis | `Insulation Score v34` |

**Format:**
- Sort: `Insulation Score v34` Descending
- X-axis: Min=0, Max=100 · Title "Score (0-100)"
- Data colors → **fx → Rules:**
  - 0–55 → `#E24B4A` (kötü yalıtım — retrofit now)
  - 55–75 → `#FFC107` (orta — plan required)
  - 75–100 → `#1D9E75` (iyi yalıtım — monitor)
- Bar labels: On · `#FFFFFF` · 9pt

**Beklenen (6 bar, sıralı):**
```
Berliner Bürogebäude   ████████████████ 82  [yeşil]
Hamburg Logistics      ████████████████ 70  [amber]
Frankfurt Klinikum     ██████████████   62  [amber]
Istanbul Office        ██████████████   60  [amber]
Wien Office            █████████████    58  [amber]
Amsterdam Universiteit ███████          38  [kırmızı]
```

> **Sadece 2–3 bar görünüyorsa:** Edit interactions → S5 (Building slicer) → V4 → **None**

---

## BÖLÜM 9 — V5: RENOVATION PRIORITY MATRIX (10 dk)

**Visual type:** Scatter chart  
**Konum:** X=923, Y=405, W=347, H=307  
**Format:** Background 100% transparent · Border Off · Title Off

| Slot | Field |
|---|---|
| X-axis | `Insulation Score v34` |
| Y-axis | `HVAC Efficiency v34` |
| Size | `Total Consumption kWh v34` |
| Details | `silver_building_master[building_name]` |
| Color saturation | `Renovation Priority Color v35` |

**Bubble Colors → fx → Rules:**
- Value = 1 → `#1D9E75` (yeşil — Low priority)
- Value = 2 → `#FFC107` (amber — Medium)
- Value = 3 → `#E24B4A` (kırmızı — High priority: GAS + poor insulation)

**Reference lines:**
- Y-axis: Y=60, label "Efficiency target", dashed, `#7DB4DC`
- X-axis: X=70, label "Insulation target", dashed, `#7DB4DC`

**Bubble labels:** On → `building_name` · Font 7pt · White

**Format:**
- X-axis: Title "Insulation Score" · Min=0, Max=100
- Y-axis: Title "Efficiency Score" · Min=0, Max=100

**Beklenen scatter yerleşimi:**
```
Sağ-üst (iyi, yeşil):  Berliner  [HP, iyi insulation]
Sol-alt (acil, kırmızı): Amsterdam, Frankfurt [Gas + kötü insulation]
Orta (amber):           Istanbul, Hamburg, Wien
```

---

## BÖLÜM 10 — EDIT INTERACTIONS (5 dk)

**View → Edit interactions ON**

| Slicer → Visual | C1–C6 Cards | V1 Breakdown | V2 Table | V3 U-Values | V4 Insulation Bar | V5 Matrix |
|---|---|---|---|---|---|---|
| **S1 Date** | Filter ✓ | Filter ✓ | **None** | Filter ✓ | Filter ✓ | Filter ✓ |
| **S2 Country** | Filter ✓ | Filter ✓ | **None** | Filter ✓ | Filter ✓ | Filter ✓ |
| **S3 Building Type** | Filter ✓ | Filter ✓ | **None** | Filter ✓ | Filter ✓ | Filter ✓ |
| **S4 System Type** | Filter ✓ | Filter ✓ | **None** | Filter ✓ | Filter ✓ | Filter ✓ |
| **S5 Building** | Filter ✓ | Filter ✓ | Filter ✓ | **None** | **None** | Filter ✓ |

**Açıklama:**
- V2 tablo: hiçbir zaman date/country/type ile filtrelenemez — portföy özeti olarak kalmalı. Sadece S5 (Building) ile filtrelenebilir.
- V4 insulation bar: S5 ile filtrelenemez — her zaman tüm 6 binayı göster (bina karşılaştırma).
- V3 U-Values: S5 ile filtrelenemez — portföy ortalaması göster (bina bazlı U-value karşılaştırma için başka sayfa).

**Edit interactions → Off** (uygulama bitti)

---

## BÖLÜM 11 — FABRİC PİPELİNE RE-RUN

Bu adımı Power BI adımlarından **bağımsız ve paralel** yapabilirsin.

**Çalıştırma sırası (kesinlikle bu sırada):**

```
Fabric Workspace → Notebooks:
  1. 01_bronze_ingestion.py      [has_gas_heating şema fix]
  2. 02_silver_transformation.py [has_gas_heating → bool]
  3. 03_gold_kpi_engine.py       [hdd_hour/cdd_hour coalesce fix]
  4. 11_hvac_analytics_engine.py [heating/cooling/CO₂ yeniden hesap]
```

Her notebook: **Run All** → hata yok → bir sonrakine geç.

**Notebook 11 bittikten sonra:**
Power BI Desktop veya Service → **Semantic model → Refresh**

**Re-run sonrası ne değişir:**
| KPI | Önce | Sonra |
|---|---|---|
| C1 HVAC Share | ~16% | 35–55% |
| C4 Heat Loss | ~17 kWh/m² | 60–110 kWh/m² |
| C5 Retrofit | 1 | 3+ (Frankfurt dahil) |
| C6 CO₂ | düşük | 240–345 tCO₂ |
| V1 Heating | minimal | kış dominant |

---

## BÖLÜM 12 — VALİDASYON (Final Checklist)

Slicer'lar **(All)** + pipeline re-run + model refresh sonrası:

| # | Kontrol | Beklenen | ❌ Sorunsa |
|---|---|---|---|
| 1 | C1 HVAC Share | **35–55 %** | Notebook 11 re-run |
| 2 | C2 HVAC Efficiency | **42–58** | Measure bind yanlış |
| 3 | C3 Avg Insulation | **62–78** | Measure bind yanlış |
| 4 | C4 Heat Loss | **60–110 kWh/m²** | HDD pipeline bug |
| 5 | C5 Retrofit | **3** (Frankfurt dahil) | Bronze schema fix |
| 6 | C6 HVAC CO₂ | **240–345 tCO₂** | has_gas pipeline bug |
| 7 | V1 Breakdown | 12 ay · kış heating peak | Date ilişkisi inactive |
| 8 | V2 System Type | Berliner=HP, 5 bina=Gas | v35 bind edilmedi |
| 9 | V2 Action | Her satır farklı metin | v35 bind edilmedi |
| 10 | V3 U-Values | 4 bar + GEG reference line | U-Value Categories yok |
| 11 | V4 Insulation | **6 bar** · Berliner en yüksek | Edit interactions fix |
| 12 | V5 Matrix | 6 bubble · 3 renk · Berliner sağ-üst | v35 color saturation |

**Tek bina testi (S5 → "Berliner Bürogebäude"):**
- C1: 45–55% · C2: 55–65 · C3: 85–92 · C4: 35–50 · C5: 0 · C6: ~18–25 tCO₂
- V2: 1 satır · "🔵 Heat Pump" · COP: 3.xx
- V4: 1 bar highlighted · V5: 1 bubble (sağ-üst)

**Tek bina testi (S5 → "Amsterdam Universiteit"):**
- C1: 30–45% · C2: 20–30 · C3: 35–45 · C4: 85–110 · C5: 1 · C6: ~55–70 tCO₂
- V2: "🟠 Gas Boiler" · "🔴 High" · "Switch to ASHP + insulate"
- V5: 1 bubble (sol-alt, kırmızı) — retrofit now zone

---

## TAMAMLANDI KRİTERLERİ

- [ ] Arka plan değiştirildi (sidebar layout)
- [ ] 5 slicer sol panelde, doğru pozisyonlarda
- [ ] C1–C6 tüm kartlar sayısal değer gösteriyor
- [ ] C6 CO₂ kartı bağlı ve değer mantıklı
- [ ] V1: 12 ay × 3 series, kış heating peak
- [ ] V2: Berliner HP, diğerleri Gas, her satır farklı action
- [ ] V3: 4 component bar + GEG reference line
- [ ] V4: 6 bar, renk gradyanı (kırmızı→amber→yeşil)
- [ ] V5: 6 bubble, 3 renk, doğru scatter yerleşimi
- [ ] Edit interactions uygulandı

**Bu 10 madde tamam → ekran kaydı paylaş → embed aşamasına geçeriz.**

---

## EK: SEKTÖREL BEKLENTILER — HVAC SAYFASININ KAPSAMASI GEREKENLER

Bu sayfa aşağıdaki sektör sorularını yanıtlıyor:

| Soru | Görsel | Beklenen değer aralığı |
|---|---|---|
| Toplam enerjinin kaçı HVAC? | C1 | 35–65% (ticari bina ASHRAE) |
| HVAC sistemleri ne kadar verimli? | C2 | 40–80 (gas-heavy portfolyo) |
| Bina zarfı yalıtım kalitesi? | C3, V4 | 0–100 score |
| Isı kaybı kabul edilebilir mi? | C4 | 40–150 kWh/m²·yr (EN ISO 13790) |
| Kaç bina acil renovasyon istiyor? | C5 | 1–4 (6 binalı portföy) |
| CSRD kapsamında CO₂ riski ne? | C6 | Gas binalar scope 1 — yüksek |
| Hangi sistem tipi var? | V2 | HP vs Gas — retrofit karar desteği |
| U-değerleri GEG'e uyumlu mu? | V3 | Çoğunlukla uyumsuz → fırsat |
| En kötü yalıtımlı bina hangisi? | V4 | Amsterdam (<50 score) |
| Renovasyon önceliği ne? | V5 | Gas + kötü insulation = HIGH |

**Bu 10 soru yanıtlanıyorsa sayfa sektör beklentisini karşılıyor.**

---

## PHASE 2 EKLENTİLERİ (IoT bağlantısı sonrası)

Aşağıdakiler şu an için SCOPE DIŞI, Phase 2'de eklenecek:
- Gerçek zamanlı COP ölçümü (BMS/IoT connector)
- Saatlik HVAC yük profili (Page 8 — IoT dashboard)
- Ülke bazlı elektrik emisyon faktörü tablosu
- ASHRAE 90.1 / EN 15232 benchmark karşılaştırması
