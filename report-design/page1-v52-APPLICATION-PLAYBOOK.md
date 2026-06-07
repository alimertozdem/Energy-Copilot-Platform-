# Page 1 v52 — Power BI Desktop Application Playbook

**Hedef:** Sayfa 1'i "Portfolio Overview" haline getirmek — tek bina değil, 6 binayı bir arada karşılaştırılabilir gösteren professional dashboard.

**Süre tahmini:** 35–50 dakika (DAX import dahil)

**Önceden olması gerekenler:**
- ✅ `60_dax_v52_page1_portfolio_scorecard.dax` DAX measures import edilmiş (17 measure)
- ✅ Fabric Lakehouse'a yeni `raw_energy_readings.csv` yüklenmiş ve pipeline (01→11) yeniden çalıştırılmış
- ⏳ Power BI Desktop açık, Sayfa 1 görünür

---

## LAYOUT KARARI: Hangi visual'ı değiştiriyoruz?

### Mevcut layout (1920×1080)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ EnergyLens logo │ PORTFOLIO OVERVIEW                          │ icons   │
├─────────────────┼───────────────────────────────────────────────────────┤
│                 │ ┌──────────┬──────────┬──────────┬──────────┬───────┐ │
│  Date slicer    │ │Total kWh │ Avg EUI  │Anomalies │ Cost €   │Carbon │ │  ← KPI Row 1
│                 │ └──────────┴──────────┴──────────┴──────────┴───────┘ │
│  Building Name  │ ┌─────┬─────┬─────┬─────┬─────┬─────────────────────┐ │
│  ▶ BUG: tek    │ │ LW  │WoW% │ LM  │MoM% │7Day€│ 30Day CO2           │ │  ← KPI Row 2
│    bina seçili  │ └─────┴─────┴─────┴─────┴─────┴─────────────────────┘ │
│                 │ ┌──────────────────────────┬──────────────────────┐   │
│  City Name      │ │ Building Consumption     │ ⚠️ Anomaly Heatmap   │   │  ← BU GİDECEK
│  Country        │ │ (Current vs PY)          │ (zayıf, sadece 1 sat)│   │
│  Building Type  │ │                          │                      │   │
│                 │ └──────────────────────────┴──────────────────────┘   │
│  ┌───────────┐  │ ┌──────────────────────────┬──────────────────────┐   │
│  │           │  │ │ Monthly Energy Trend     │ EUI Benchmark        │   │
│  │   Map     │  │ │ ⚠️ tarih sırası bozuk    │ ⚠️ tek bina          │   │
│  │  Berlin   │  │ │                          │                      │   │
│  │           │  │ │                          │                      │   │
│  └───────────┘  │ └──────────────────────────┴──────────────────────┘   │
└─────────────────┴───────────────────────────────────────────────────────┘
```

### Yeni layout (uygulanacak)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ EnergyLens logo │ PORTFOLIO OVERVIEW                          │ icons   │
├─────────────────┼───────────────────────────────────────────────────────┤
│                 │ ┌──────────┬──────────┬──────────┬──────────┬───────┐ │
│  Date slicer    │ │Total kWh │ Avg EUI  │Anomalies │ Cost €   │Carbon │ │
│                 │ └──────────┴──────────┴──────────┴──────────┴───────┘ │
│  ⛔ Building   │ ┌─────┬─────┬─────┬─────┬─────┬─────────────────────┐ │
│  Name slicer    │ │ LW  │WoW% │ LM  │MoM% │7Day€│ 30Day CO2           │ │
│  KALDIRILACAK   │ └─────┴─────┴─────┴─────┴─────┴─────────────────────┘ │
│                 │ ┌──────────────────────────┬──────────────────────┐   │
│  City Name      │ │ Building Consumption     │ 🆕 Portfolio         │   │  ← YENİ
│  Country        │ │ (Current vs PY) — 6 bar  │   Scorecard Table    │   │
│  Building Type  │ │                          │   6 satır × 6 sütun  │   │
│                 │ │                          │   renkli traffic-lt  │   │
│  ┌───────────┐  │ └──────────────────────────┴──────────────────────┘   │
│  │           │  │ ┌──────────────────────────┬──────────────────────┐   │
│  │   Map     │  │ │ Monthly Energy Trend     │ EUI Benchmark        │   │
│  │ 6 pin'li  │  │ │ ✅ MonthIndex sort fix   │ ✅ 6 bar + median ref │   │
│  │           │  │ │                          │                      │   │
│  └───────────┘  │ └──────────────────────────┴──────────────────────┘   │
└─────────────────┴───────────────────────────────────────────────────────┘
```

**Değişikliklerin özeti:**
| # | Eylem | Neden |
|---|---|---|
| 1 | "Building Name" slicer → KALDIR (veya default = All) | Portfolio overview tek bina olmamalı |
| 2 | "Anomaly Severity × Building Heatmap" → KALDIR | Yerini Portfolio Scorecard alacak; anomali bilgisi scorecard'da bir sütun olarak korunuyor |
| 3 | "Portfolio Scorecard" Table → EKLE (heatmap'in yerine) | Building × KPI grid, renkli traffic-light, en aksiyonlanabilir görsel |
| 4 | Monthly Trend: YearMonth → Sort by Column → MonthIndex | X-ekseni şu an karmakarışık |
| 5 | EUI Benchmark: tüm binaları göster + median reference line | Karşılaştırma yapılabilir hale gel |
| 6 | KPI cards Goal alanları → dinamik measures | Sabit "+0%" placeholder'ı kalksın |

---

## ADIM 1 — Building Name slicer'ı KALDIR (2 dk)

**Neden:** Bu slicer Page 1'in default state'ini tek binaya filtreliyor.

1. Page 1'i aç
2. Sol panelde **"Building Name"** dropdown slicer'ını seç (içinde "Berliner Bürogebäu..." yazıyor)
3. Tıkla → Delete tuşuna bas (veya sağ tık → Remove)

**Alternatif (eğer slicer'ı kaybetmek istemiyorsan):**
- Slicer'ı seçili tut → Visualizations panelinde Selection controls'a git
- "Select all" toggle'ını aç
- Slicer üzerinde tüm checkbox'ları işaretli yap → Page'i kaydet
- Bu durumda slicer kalır ama default tüm binalar seçili olur

**Doğrulama:**
- Sayfa 1 yeniden render olmalı
- "Building-Based Consumption (Current vs PY)" visual'ı şimdi 6 bar göstermeli (Berliner, Istanbul, Hamburg, Vienna, Frankfurt, Amsterdam)
- KPI kartları toplam değerleri büyümeli (örn. Total Energy → 113K değil, ~1.4M+ olmalı)

---

## ADIM 2 — "Anomaly Severity × Building Heatmap" visual'ını KALDIR (1 dk)

1. Sağ-üst köşedeki **"Anomaly Severity × Building Heatmap"** matrix visual'ını seç
2. Delete tuşuna bas (visual silinir, alan boş kalır)

**Yer:** Bu alan yaklaşık olarak x=1330, y=290, genişlik=550, yükseklik=300 piksel. Tam koordinat değil — sayfanın sağ-üst dörtte birlik kısmı.

---

## ADIM 3 — Portfolio Scorecard Table visual'ı EKLE (8 dk)

### 3.1 — Yeni Table visual oluştur

1. Insert sekmesinde **"Visualizations" panelinden** "Table" ikonu (≡ üç yatay çizgi) tıkla
2. Veya: Sayfa boşluğuna sağ tık → Insert → Visualization → Table
3. Yeni boş table visual ekrana düşer → onu sürükleyerek silinen heatmap'in yerine yerleştir
4. Boyutlandır: yaklaşık 580×320 piksel

### 3.2 — Field well'i doldur (SIRA ÖNEMLİ — soldan sağa)

Visualizations panelinde **"Columns"** field well'ine bu alanları **sırasıyla** sürükle:

| Sıra | Alan | Kaynak tablo | Display name |
|---|---|---|---|
| 1 | `building_name` | silver_building_master | Building |
| 2 | `country_code` | silver_building_master | Country |
| 3 | `energy_certificate` | silver_building_master | EPC |
| 4 | `[P1 Scorecard EUI]` | Measures | EUI |
| 5 | `[P1 Scorecard Cost EUR]` | Measures | Annual Cost |
| 6 | `[P1 Scorecard Active Anomalies]` | Measures | Anomalies |
| 7 | `[P1 Scorecard CRREM Status]` | Measures | CRREM |

**Display name değiştirmek için:** Field well'de bir alanın sağ-tıkla → Rename for this visual

### 3.3 — Format ayarları

Visualizations → **Format visual** (boya fırçası ikonu) sekmesi:

**General:**
- Title → On → Text: "Portfolio Scorecard — All Buildings"
- Font size: 14, Color: white, Bold

**Style presets:**
- Style: "Minimal" veya "Bold header"

**Values (rows):**
- Font: Segoe UI, 11pt
- Alternate background: light gray (#2A2A2A — dark theme uyumlu)

**Column headers:**
- Background: #1D9E75 (EnergyLens emerald)
- Font color: white
- Bold

**Specific column:**
- EUI sütununu seç → Number format: 0 decimals
- Annual Cost sütunu → Currency format: € symbol, 0 decimals
- Anomalies sütunu → Number: 0 decimals

---

## ADIM 4 — Conditional formatting (renkli traffic-light) (10 dk)

Bu adım scorecard'ı "professional" hale getiren kritik kısım.

### 4.1 — EUI sütunu için renk kuralı

1. Field well'de **[P1 Scorecard EUI]** field'inin yanındaki **▼ dropdown ok**'una tıkla
2. **Conditional formatting → Background color** seç
3. Açılan panelde:
   - **Format style:** Rules
   - **What field should we base this on:** `[P1 Scorecard EUI Color]` (v52 DAX'da var)
   - **Summarization:** First
4. Rules:
   - If value `≥ 1 and < 2` → Color: **#3FA34D** (green)  → Label: "Good"
   - If value `≥ 2 and < 3` → Color: **#F0B100** (amber) → Label: "Warning"
   - If value `≥ 3 and <= 3` → Color: **#D14B4B** (red) → Label: "Critical"
5. OK

**Beklenen sonuç:**
- B001 Berlin Office (EUI 82) → Green
- B003 Hamburg Logistics (EUI 138) → Green
- B004 Vienna Hotel (EUI 289) → Green
- B006 Amsterdam Edu (EUI 173) → Amber/Red (yaşlı bina)
- B002 Istanbul Retail (EUI 251) → Amber
- B005 Frankfurt Health (EUI 501) → Green/Amber (sektör normu)

### 4.2 — CRREM sütunu için renk kuralı

Aynı yöntem:
1. **[P1 Scorecard CRREM Status]** ▼ → Conditional formatting → Background color
2. Format style: Rules
3. Base on: `[P1 Scorecard CRREM Color]`
4. Rules:
   - `= 1` → Green (#3FA34D)
   - `= 2` → Amber (#F0B100)
   - `= 3` → Red (#D14B4B)

### 4.3 — Active Anomalies sütunu

1. **[P1 Scorecard Active Anomalies]** ▼ → Conditional formatting → **Font color** (background değil — sayı zaten okunaklı olsun)
2. Format style: Rules
3. Base on field: `[P1 Scorecard Active Anomalies]`
4. Rules:
   - `= 0` → Green text (#3FA34D)
   - `> 0 and ≤ 3` → Amber text (#F0B100)
   - `> 3` → Red text (#D14B4B) + Bold

### 4.4 — Annual Cost sütunu (data bar — opsiyonel)

1. **[P1 Scorecard Cost EUR]** ▼ → Conditional formatting → **Data bars**
2. Color: gradient emerald (#1D9E75)
3. Show bar only: OFF (sayıyı da göster)

---

## ADIM 5 — Monthly Energy Trend X-ekseni FIX (3 dk)

**Bu adım en ucuz ama en yüksek etkili fix.** Şu an X-ekseni "2025-…, 2025-01, 2025-12, 2023-01" şeklinde tamamen karışık.

1. Sol panelde **Model view**'a geç (Ev → Model)
2. Tables panelinde **Date** tablosunu bul
3. **YearMonth** kolonunu seç
4. Üst sekmede **Column tools** → **Sort by Column** → **MonthIndex** seç
5. Geri Report view'a dön
6. Page 1'i refresh et (F5)
7. **Doğrulama:** Monthly Trend X-ekseni şimdi soldan sağa kronolojik (2023-01, 2023-02, ... 2026-04)

**Eğer MonthIndex kolonu yoksa:** v17 DAX dosyasında Bölüm 0 talimatlarını uygula (Date tablosu formülüne `"MonthIndex", YEAR([Date])*100 + MONTH([Date]),` ekle).

---

## ADIM 6 — EUI Benchmark visual fix (5 dk)

Şu an "EUI Benchmark by Building" tek bar gösteriyor (Berliner 0.24). Tüm binaları göstersin + reference line ekle.

### 6.1 — Field well kontrol

1. EUI Benchmark visual'ını seç
2. Eğer Y-axis'te `building_name` yoksa: silver_building_master[building_name]'i sürükle Y-axis'e
3. X-axis (values): mevcut EUI measure'ı tut, ya da `[P1 Scorecard EUI]` ile değiştir (daha tutarlı)
4. Visual otomatik 6 bar göstermeli

### 6.2 — Reference line ekle

1. Visual seçili → Format visual → **Analytics** sekmesi
2. **Constant line** → +Add → Toggle ON
3. Properties:
   - Value: type field button → **[Portfolio Median EUI]**
   - Color: light gray (#888)
   - Style: Dashed
   - Position: Behind
   - Data label: ON → Text: "Portfolio Median"
4. OK

### 6.3 — Bar color saturation (opsiyonel ama professional)

1. Format visual → **Bars → Colors → fx (Conditional formatting)**
2. Format style: Rules veya Gradient
3. Rules:
   - EUI ≤ Portfolio Median → Green
   - EUI > Median * 1.2 → Red
4. OK

---

## ADIM 7 — KPI cards Goal alanları → dinamik measures (8 dk)

Her büyük KPI kartının (Total Energy, Avg EUI, Active Anomalies, Total Cost, Net Carbon) sabit "Goal: 107,491 (-5.26%)" yazıları artık dinamik measure'lar olacak.

### 7.1 — Total Energy Consume kWh kartı

1. KPI kartını seç (Total Energy Consume kWh)
2. Field well → **Target value** alanını bul
3. Eski sabit target'i sürükle çıkar
4. **[P1 Goal Total Energy kWh]** measure'ı sürükle target value'ya
5. Format → Callout value → Number format: thousands

### 7.2 — Avg EUI kartı

1. Avg EUI kartı seç
2. Target value → **[P1 Goal Avg EUI]** (Portfolio Median)
3. Format → değer formatı: 2 decimal

### 7.3 — Active Anomalies kartı

1. Active Anomalies kartı seç
2. Target value → **[P1 Goal Active Anomalies]** (= 0)
3. KPI direction: lower is better (icon değişecek)

### 7.4 — Total Energy Cost € kartı

1. Total Cost kartı seç
2. Target value → **[P1 Goal Cost EUR]**

### 7.5 — Net Carbon Footprint kartı

1. Net Carbon kartı seç
2. Target value → **[P1 Goal Net Carbon tCO2]**

**Doğrulama:** Tüm KPI kartlarının goal kısmı artık gerçek hedefleri göstermeli (statik %0 sapma kalmamalı). Örnek:
- Total Energy: "Goal: 1,194,500 (-4.7%)" → "5% reduction vs 2024" anlamına gelir
- Active Anomalies: "Goal: 0 (-12 below)" → hedef sıfır anomali

---

## ADIM 8 — Final doğrulama checklist (5 dk)

Sayfa 1'i kaydet → Refresh (F5) → sırayla kontrol et:

- [ ] Building Name slicer YOK (veya default "All")
- [ ] Sol panelde Date / City / Country / Building Type slicer'ları kalmış
- [ ] KPI Row 1 (5 kart): Total Energy değeri artık ~1.4M+ (tek bina değil)
- [ ] KPI Row 1 Goal'leri dinamik (her birinin altında somut hedef + sapma %)
- [ ] Building-Based Consumption: **6 bar** görünüyor (Berlin, Istanbul, Hamburg, Vienna, Frankfurt, Amsterdam)
- [ ] **🆕 Portfolio Scorecard Table:** 6 satır, EUI sütunu renkli, CRREM sütunu renkli
- [ ] Anomaly Heatmap YOK (yerine Scorecard var)
- [ ] Monthly Energy Trend: X-ekseni 2023-01 → 2026-04 **kronolojik sıralı**
- [ ] EUI Benchmark: 6 bar görünüyor + dashed "Portfolio Median" reference line
- [ ] Map: 6 pin (Berlin, Istanbul, Hamburg, Vienna, Frankfurt, Amsterdam)

**Eğer tüm tick'ler ✅:** Sayfa 1 production-ready. Screenshot al, paylaş, Sayfa 2'ye geç.

**Eğer bir adım takılırsa:** Hangi adım, hangi hata? Detay ver, hemen çözeriz.

---

## TROUBLESHOOTING

### "Portfolio Scorecard tablosunda bir bina eksik"
- Sebep: Pipeline re-run eksik
- Çöz: Fabric'te 01_bronze → 02_silver → 03_gold pipeline'ı yeniden çalıştır

### "EUI sütunu renkli değil, hep aynı renk"
- Sebep: Conditional formatting "Base on field" yanlış measure'a bağlı
- Çöz: ADIM 4.1'i tekrar yap, "Base on field" mutlaka `[P1 Scorecard EUI Color]` olmalı (Color suffix'i kritik)

### "Monthly Trend hâlâ karışık sıralı"
- Sebep: YearMonth Sort by Column uygulanmadı
- Çöz: Model view → Date → YearMonth → Column tools → Sort by Column → MonthIndex

### "[P1 Goal ...] measure'lar BLANK dönüyor"
- Sebep: `Previous Year Consumption kWh` ya da `Previous Year Net Carbon tCO2` measure'ları henüz import edilmedi (v17'den)
- Çöz: 22_dax_v17_page1_final.dax'daki "Previous Year ..." measure'larını da import et

### "Scorecard'da Cost değeri çok yüksek/düşük"
- Sebep: Country price defaults yanlış olabilir (v52 BÖLÜM 1D)
- Çöz: `P1 Scorecard Cost EUR` measure'ı içindeki SWITCH bloğunu kendi ülke fiyatlarınla güncelle

---

**Süre:** 35–50 dakika. Acele etme, her adımdan sonra Refresh (F5) yapıp doğrulamayı geç. Tamamlanınca yeni Page 1 screenshot bana göster → Sayfa 2'ye geçeriz.
