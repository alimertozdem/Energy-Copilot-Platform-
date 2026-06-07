# Page 7 — HVAC & Building Envelope · Final Plan

**Status:** Directly applicable layout & DAX patch
**Last updated:** 2026-05-03
**Canvas:** 1280 × 720 px · Accent: `#FF7B54` (thermal orange)
**Driver philosophy:** "What does an energy manager need to decide *today*?"

---

## 1. Why we're rebuilding this page

Mevcut sayfada 8 KPI + 8 görsel var ve enerji yöneticisinin gerçekten kullanacağı bilgi 3 ekranda da düzgün çıkmıyor. Ekranlardan ve veri katmanından çıkardığım kök nedenler:

| # | Problem | Root cause | Fix layer |
|---|---|---|---|
| 1 | **Avg COP "—"** her seçimde | `cop_actual_avg` fiziksel kolonu yok → `[COP Monthly Actual]` blank | DAX (cop_rated fallback) |
| 2 | **HVAC Share %** "2.78401…" | Format string yanlış + denominator filter context | DAX v10 zaten var, bağlanmamış |
| 3 | **Frankfurt'ta her şey "—"** | B005 `gold_hvac_analytics`'te yok | Notebook 11 yeniden çalıştır |
| 4 | **Tabloda her bina "Heat Pump"** | `CALCULATE+ALLEXCEPT` row context bug'ı | DAX (sade `MAX` versiyon) |
| 5 | **Insulation by Building** sadece 3 bar | 3 binada gold satırı yok | Notebook 11 + edit interactions |
| 6 | **Heat Pump COP visual** boş | 6 binadan sadece B001 HP, sparse data | Görseli sayfadan **kaldır** |
| 7 | **Buildings For Renovation tek bina seçince "—"** | BLANK → 0 olmalı | DAX wrapper |
| 8 | **8 KPI kartı çok fazla** | Bilgi sisi | Layout: 8 → 5 kart |

**Manager perspektifinden 5 cevaplaması gereken soru:**
1. HVAC enerjimin ne kadarını yiyor? → C1 HVAC share %
2. HVAC sistemim sağlıklı mı? → C2 HVAC efficiency score
3. Bina kabuğum nasıl? → C3 Insulation score
4. Ne kadar ısı kaybediyorum? → C4 Heat loss kWh/m²
5. Hangi binayı önce retrofit etmeliyim? → C5 Buildings for retrofit + V2 table + V5 matrix

---

## 2. Final layout (final-card grid)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Title: HVAC & BUILDING ENVELOPE                       Slicers row →     │
│  Slicers: Building | Year | Month | System Type | Reno Priority          │
├──────────────────────────────────────────────────────────────────────────┤
│  C1 HVAC % | C2 Efficiency | C3 Insulation | C4 Heat Loss | C5 Retrofit  │
├──────────────────────────────────────────────────────────────────────────┤
│  V1 — HVAC Energy Breakdown      │  V2 — Building HVAC Summary Table     │
│  (100% Stacked Column · monthly) │  (per-building system + actions)      │
├──────────────────────────────────┴───────────────────────────────────────┤
│  V3 — U-Values vs GEG  │  V4 — Insulation by Building  │  V5 — Reno      │
│  (Bullet/Clustered Bar)│  (Horizontal Bar + target)    │  Priority Matrix│
└──────────────────────────────────────────────────────────────────────────┘
```

**Çıkartılan görseller (eski v6 layout'tan):**
- ❌ V3 eski: "Heat Pump COP vs SCOP 3-month Rolling" — sadece 1 HP binası, sparse, sayfayı boğuyor.
- ❌ V6 eski: "Monthly Heat Loss Through Envelope" — 6 bina legend trend, tooltip'le aynısı veriyor.
- ❌ V8 eski: "Benchmark Comparison Cards" — multi-row card C1-C5 ile tekrarlı.

**Yerine eklenen / vurgulanan:**
- ✅ V2 (Building Summary Table) **büyütüldü ve sağ üste alındı** — sayfanın "ne yapayım" cevabı burası.
- ✅ V5 (Renovation Priority Matrix) **quadrant etiketleri ile** — manager bir bakışta hangi binanın hangi kuadrantta olduğunu görür.
- ✅ Tabloya yeni `Action Recommendation Short` kolonu — her bina için 1 satırlık yapılacak.

---

## 3. Slicer row (Y: 20 · H: 36)

| ID | Field | X | W | Header |
|---|---|---|---|---|
| S1 | `silver_building_master[building_name]` | 20 | 200 | Building |
| S2 | `Date[Year]` | 230 | 100 | Year |
| S3 | `Date[YearMonth]` (sort by `MonthIndex`) | 340 | 130 | Month |
| S4 | `gold_hvac_analytics[system_type]` | 480 | 160 | System type |
| S5 | `gold_hvac_analytics[renovation_priority]` | 650 | 160 | Reno priority |

**Edit Interactions kuralı:** S1 (Building) hariç hiçbir slicer V2 tablosunu filtrelemez. Tablo her zaman tüm binayı listeler — manager portföy tablosunu görür, S1 ile tek satıra zoom yapar.

---

## 4. KPI Cards (Row 2 · Y: 70 · H: 90)

5 eşit kart, ~250 × 90 px her biri (8 px gap).

| Card | X | Measure | Format | Target / Conditional |
|---|---|---|---|---|
| **C1 HVAC share** | 20 | `Card: HVAC Share Pct Display` (v33) | `0.0 "%"` (suffix) | Range gauge 0–100, target 40–60 yeşil |
| **C2 HVAC efficiency** | 278 | `Card: HVAC Efficiency Display` (v33) | `0.0` | KPI indicator target 60 |
| **C3 Insulation score** | 536 | `Card: Avg Insulation Score` (v33) | `0.0` | KPI indicator target 75 |
| **C4 Heat loss** | 794 | `Heat Loss kWh m2 Annual` | `0.0 " kWh/m²"` | Conditional: >50 amber, >100 red |
| **C5 Buildings for retrofit** | 1052 | `Card: Buildings For Retrofit` (v33) | `0` | Conditional: >0 → font `#E24B4A` |

**Card visual tipi:** Tümü "Card (new)". KPI Indicator KULLANMA — Direct Lake context'iyle çakışıyor (v19c lesson).

**Format fix kritik:** C1 için Power BI Desktop → Format card → "Display units: None" → "Decimal places: 1" → "Suffix: ` %`" (boşlukla). `0%` veya `0.00%` formatı KULLANMA — DAX zaten 0–100 döndürüyor, Power BI yine ×100 yapar.

---

## 5. V1 — HVAC Energy Breakdown by Month (X: 20, Y: 175, W: 615, H: 230)

**Visual:** 100% Stacked Column Chart
**X-axis:** `Date[YearMonth]` (Sort by `MonthIndex`)
**Values (legend):**
- `Heating Energy kWh` — color `#FF4560`
- `Cooling Energy kWh` — color `#00C8FF`
- `Ventilation Energy kWh` — color `#7DB4DC`

**Title:** "HVAC energy breakdown — heating dominates winter (HDD-driven)"
**Tooltip:** absolute kWh + % share
**Toggle:** Bookmark ile "Stacked column" (absolute) ↔ "100% Stacked column" (composition)

**Validation:** Berliner (HP) seçildiğinde Aralık-Şubat arasında heating %75+ olmalı, Temmuz-Ağustos cooling %20+. Eğer bütün aylar aynı görünüyorsa → `gold_hvac_analytics[year_month] → Date[Date]` ilişkisini kontrol et.

---

## 6. V2 — Building HVAC Summary Table (X: 645, Y: 175, W: 615, H: 230)

**Visual:** Table
**Columns (sırasıyla):**

| Column | Source | Width | Notes |
|---|---|---|---|
| Building | `silver_building_master[building_name]` | 130 | — |
| System | `System Type Display Robust` (v33) | 110 | Replaces buggy mevcut ölçü |
| Priority | `Renovation Priority Icon Robust` (v33) | 100 | Color: High `#E24B4A`, Med `#FFC107`, Low `#1D9E75` |
| Insulation | `Insulation Rating Label` | 80 | Mevcut, A–E |
| COP | `COP Display Robust` (v33) | 90 | "(actual)" / "(rated)" / "n/a (gas)" |
| Heat loss | `Heat Loss kWh m2 Annual` | 70 | "0.0" — kWh/m² |
| Action | `Action Recommendation Short` (v33) | 140 | 1 cümle yapılacak |

**Sort:** "Priority" kolonuna göre custom sort: High → Medium → Low. Bunun için Power Query'de `renovation_priority_sort` kolonu eklenmeli (1=High, 2=Medium, 3=Low) ya da `[Renovation Priority Color]` ölçüsünü Sort kolonu olarak ekle.

**Conditional formatting:** Priority kolonunda "Background color → Field value" ile color column kullan. Veya basit kural: "High" satırı için arka plan `rgba(255, 69, 96, 0.10)` kullan.

**Edit interactions:** S2/S3/S4/S5 → V2 = "None" (slicer'lar tabloyu filtrelemez). S1 (Building) → V2 = "Filter" (varsayılan).

---

## 7. V3 — U-Values vs GEG 2023 Standard (X: 20, Y: 415, W: 400, H: 240)

**Visual seçeneği A (önerilen):** Clustered Bar Chart with overlay
- Y-axis: kategori etiketleri Wall / Roof / Floor / Window (`unsupported native` — ya manuel hardcoded label tablosu ya da ölçü-tabanlı uzun kolon)
- X-axis (clustered):
  - Series 1: Actual U-value
  - Series 2: GEG benchmark (static)

**Visual seçeneği B (daha basit):** Table visual
- Columns: Component label · Actual W/m²K · GEG limit · Compliance icon
- Measures: `U Wall Actual`, `U Roof Actual`, `U Floor Actual`, `U Window Actual` + `GEG Compliance Wall/Roof/Window`

**Tavsiye:** B yolu daha hızlı çıkar, sentetik veriyle de düzgün görünür. Gerçek müşteri demoda A'ya geçeriz.

**Title:** "Building envelope U-values vs GEG 2023 (lower = better)"

---

## 8. V4 — Insulation Score by Building (X: 430, Y: 415, W: 400, H: 240)

**Visual:** Clustered Horizontal Bar Chart
**Y-axis:** `silver_building_master[building_name]`
**X-axis:** `Insulation Score`
**Sort:** Descending by Insulation Score

**Conditional formatting on bars:**
- ≥ 75 → `#1D9E75` (green — GEG compliant)
- 55–75 → `#FFC107` (amber — partial upgrade)
- < 55 → `#E24B4A` (red — significant retrofit)

**Reference line:** at X = 75, label "GEG 2023 retrofit threshold", color `#7DB4DC` dashed.

**Title:** "Insulation score by building — target ≥ 75"

**Edit interactions:** S1 (Building) → V4 = "Filter". Diğer slicerlar = "None" (envelope skoru aydan bağımsız).

---

## 9. V5 — Renovation Priority Matrix (X: 840, Y: 415, W: 420, H: 240)

**Visual:** Scatter Chart
- X: `Insulation Score` (0–100)
- Y: `HVAC Efficiency Score` (0–100)
- Size: `Building Total Consumption kWh Annual` (v33)
- Details: `silver_building_master[building_name]`
- Color saturation / Legend: `Renovation Priority Color` (v33) — 1=Low, 2=Medium, 3=High

**Quadrant lines:** X=55, Y=50 (gridlines)

**Static text labels (text box overlays):**
- Top-right (X≥55, Y≥50): "Efficient — keep" — `#1D9E75`
- Top-left (X<55, Y≥50): "HP ok, envelope needs work" — `#FFC107`
- Bottom-right (X≥55, Y<50): "Envelope ok, system upgrade" — `#FFC107`
- Bottom-left (X<55, Y<50): "**Retrofit now**" — `#E24B4A`

**Title:** "Renovation priority matrix — bubble size = annual kWh"

**Validation:** Berliner sağ-üstte (efficient), Frankfurt/Amsterdam sol-altta (retrofit now), diğerleri ortada. Hepsi aynı yerdeyse → `[HVAC Efficiency Score]` veya `[Insulation Score]` ölçüleri row context'inde patliyor demektir → DAX v33'teki "Robust" wrapper'lara dönüştür.

---

## 10. DAX patch sırası (uygulama)

`semantic-model/42_dax_v33_page7_hvac_final.dax` dosyasındaki ölçüleri **bu sırayla** ekle (Power BI Desktop → New measure):

1. `COP Display Robust`
2. `Card: Avg HP COP Robust` (yedek — final layout'ta C2 yok ama tabloda kullanılabilir)
3. `System Type Display Robust`
4. `Renovation Priority Icon Robust`
5. `Card: HVAC Share Pct Display`
6. `Card: Avg Insulation Score`
7. `Card: Buildings For Retrofit`
8. `Card: HVAC Efficiency Display`
9. `Renovation Priority Color`
10. `Building Total Consumption kWh Annual`
11. `Action Recommendation Short`

Sonra V1–V5 ve C1–C5 görsellerini layout doğrultusunda bağla.

---

## 11. Notebook 11 — kalan veri işleri

Layout uygulamadan önce sadece **bir** notebook adımı kaldı:

**Frankfurt (B005) ve diğer eksik binaların `gold_hvac_analytics`'e gelmesi için:**
- Notebook 11 (`11_hvac_analytics_engine.py`) Fabric'te yeniden çalıştırılmalı.
- Pre-check: `gold_kpi_daily`'de tüm 6 binanın günlük tüketim verisi olduğunu doğrula:
  ```python
  spark.read.format("delta").load("Tables/gold_kpi_daily") \
       .groupBy("building_id").count().show()
  ```
- Eğer Frankfurt/Amsterdam/Wien/Istanbul kayıtları yoksa, bronze/silver pipeline'ında problem var (ayrı issue — bu sayfayı bloklamasın; layout 6 binadan kaçı geliyorsa o kadarıyla çalışır).

**Notebook 11'e KOD DEĞİŞİKLİĞİ GEREKMİYOR** — DAX v33 fallback'leri bu boşlukları görsel düzeyde yumuşatıyor.

---

## 12. Validation checklist (uygulama sonrası kontrol)

- [ ] **C1 HVAC share %**: ALL portföy seçiminde 30–55 % aralığında (ofis benchmark 40–60).
- [ ] **C2 HVAC efficiency**: ALL portföy → 40–55 (gas-ağırlıklı portföy).
- [ ] **C3 Insulation score**: ALL → 60–80; Berliner seçince 90+; Amsterdam seçince <50.
- [ ] **C4 Heat loss**: Format `0.0 kWh/m²` — değeri 30–150 arasında olmalı.
- [ ] **C5 Buildings for retrofit**: 0–6 arasında integer. Tek bina seçimde priorityi High değilse 0 göster.
- [ ] **V1 stacked column**: 12 ay × 3 series görünür; kış aylarında heating %70+, yaz aylarında cooling şişer.
- [ ] **V2 table**: Berliner = Heat Pump · Diğerleri = Gas Boiler. Action sütunu her satırda farklı.
- [ ] **V3 U-values**: 4 component görünür, GEG limitler dashed line/secondary bar olarak çakışıyor.
- [ ] **V4 Insulation by building**: 6 bar (data eksikse 5–6 arası), sort descending, target line at 75.
- [ ] **V5 scatter**: En az 4 bubble görünür (B005 olmasa bile), quadrant etiketleri okunabilir.

---

## 13. Bookmarks (opsiyonel — embedding sonrası)

- **Bookmark 1: "Portfolio overview"** — All slicers cleared
- **Bookmark 2: "Retrofit candidates"** — S5 = "High"
- **Bookmark 3: "Heat pump fleet"** — S4 = "heat_pump" (tek binada Berliner görünür)
- **Bookmark 4: "Winter mode"** — S3 = Dec/Jan/Feb (heating-dominant view)

Embedding sonrası web app'te bu bookmark'ları "filter chip" olarak ön plana çıkar.

---

## 14. Time estimate

| Adım | Süre |
|---|---|
| DAX v33 ölçülerini ekle (11 measure) | 15 dk |
| C1–C5 kartları rebind + format | 10 dk |
| V1 axis fix (gerekirse) | 5 dk |
| V2 table column update + conditional formatting | 15 dk |
| V3 yeni veya rebind | 10 dk |
| V4 conditional formatting + reference line | 5 dk |
| V5 scatter color/size rebind + quadrant text boxes | 15 dk |
| Edit interactions ayarı (S1 hariç slicerlar V2'ye filter etmesin) | 5 dk |
| Validation pass | 10 dk |
| **Total** | **~90 dk** |

---

## 15. Energy logic asssumptions (BMAD logic layer disclosure)

Bu sayfadaki tüm hesapların altında yatan varsayımlar:

| Hesap | Yöntem | Kaynak | Sınırlılık |
|---|---|---|---|
| Heating/Cooling disaggregation | HDD/CDD oransal model + bina tipi katsayısı | EN ISO 13790 + ASHRAE Handbook 2021 Ch. 32 | Sub-meter verisi yok — kalibrasyon yapılmadı |
| U-composite | 0.40 wall + 0.30 window + 0.20 roof + 0.10 floor weighted avg | CIBSE Guide A Tablo 3.2 | Ağırlıklar tipik ofis için; depo/hastane farklı olabilir |
| Insulation score | min(100, target_U / actual_U × 100), GEG 2023 reference | GEG 2023 §19 | Almanya benchmark'ı diğer ülkelere uygulandı (güvenli taraf) |
| Heat loss | U_composite × envelope_area × HDD × 24 / 1000 | EN ISO 13370 simplified + EN ISO 14683 thermal bridge | Envelope alanı kare plan + 3 kat varsayımı (BIM yok) |
| HVAC efficiency score | HP: COP/4.5 × 100, Gas: ≤50 capped | Eurovent + IEA HP roadmap 2023 | Karbon dezavantajı için gas başarımı 50'de kapatıldı |
| Renovation priority | Insulation band × system type 3×2 matrix | Internal | Tek-faktörlü; gerçek karar finansal payback'i de içerir |

Manager'a sunum sırasında bu "assumptions" bölümünü slide olarak hazırlamak isterseniz söyleyin — pptx skill ile basit 1-page özet üretebilirim.
