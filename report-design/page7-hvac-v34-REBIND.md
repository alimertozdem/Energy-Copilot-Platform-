# Page 7 — HVAC & Building Envelope · v34 REBIND GUIDE

**Status:** ACTION REQUIRED · 2026-05-04  
**DAX kaynak:** `semantic-model/43_dax_v34_page7_hvac_self_contained.dax`  
**Neden v34?** v33 ölçüleri `gold_kpi_daily[total_kwh]` kolonuna bağımlıydı; bu kolon modelde yok → tüm card'lar `--` dönüyordu. v34 sadece `gold_hvac_analytics` + `silver_building_master` kullanır, hiçbir eski ölçüye bağımlı değildir.

---

## ⚠️ v35 EK ADIMI — ALLEXCEPT Bug Fix (2026-05-04 güncelleme)

V2 tablosundaki tüm binalar "Air/Ground Source Heat Pump" ve "Medium — Plan in 2 Years" gösteriyorsa, v34'teki `ALLEXCEPT` bug'ı aktif. **v35 ölçülerini** (44_dax_v35_page7_hvac_allexcept_fix.dax) import et ve V2 ile V5'te v35 versiyonlarını kullan. Aşağıdaki adım 5'te detaylar var.

---

## ADIM 0 — v34 Ölçülerini Modele Import Et (5 dk)

Power BI Desktop → **DAX query view**:

1. `semantic-model/43_dax_v34_page7_hvac_self_contained.dax` dosyasını aç
2. Tüm içeriği kopyala
3. Power BI **DAX query view** penceresine yapıştır → **Run** (▶)
4. Hata yoksa: **Data pane** → `gold_hvac_analytics` altında şu ölçüler görünmeli:
   - `Total Consumption kWh v34`
   - `HVAC Total kWh v34`
   - `HVAC Share Pct v34`
   - `HVAC Efficiency v34`
   - `Insulation Score v34`
   - `Heat Loss kWh m2 Annual v34`
   - `Retrofit Count v34`
   - `Heating Energy kWh v34`
   - `Cooling Energy kWh v34`
   - `Ventilation Energy kWh v34`
   - `System Type Display v34`
   - `COP Display v34`
   - `Renovation Priority Icon v34`
   - `Action Recommendation v34`
   - `Renovation Priority Color v34`

> **Not:** DAX query view ile import edemiyorsan alternatif: Her ölçüyü ayrı ayrı **New Measure** olarak ekle (gold_hvac_analytics tablosuna sağ tık → New Measure).

---

## ADIM 1 — Sayfa 7'yi Aç, Edit Mode'a Gir

07_HVAC sekmesine tıkla → **Edit** (varsa view mode'daysan)

---

## ADIM 2 — İlişki Kontrolü (2 dk, kritik)

**Model view** → şu iki ilişki ACTIVE ve single-direction olmalı:
- `gold_hvac_analytics[building_id]` → `silver_building_master[building_id]` (M:1) ✅
- `gold_hvac_analytics[year_month]` → `'Date'[Date]` (M:1)

> **year_month → Date ilişkisi yoksa veya inactive ise:**  
> V1 chart daima boş kalır. İlişki aktif değilse:  
> Model view → Manage relationships → `gold_hvac_analytics[year_month]` – `Date[Date]` → **Active** işaretle.  
> Eğer ilişki hiç yoksa: New relationship → `gold_hvac_analytics[year_month]` → `Date[Date]`.

---

## ADIM 3 — 5 KPI CARD REBIND

> Her card için: **Card visual tıkla → Fields pane → Value slot → X ile ESKİ ÖLÇÜYÜ SİL → yeni ölçüyü sürükle**

### C1 — HVAC SHARE % (turuncu kart)
- **Kaldır:** `HVAC Share Pct` veya `Card: HVAC Share Pct Display` (hangisi varsa)
- **Ekle:** `HVAC Share Pct v34`
- **Format → Callout value → Custom:** `0.0"%"`
- **Beklenen (All):** 35–55 %

### C2 — HVAC EFFICIENCY (sarı kart)
- **Kaldır:** `HVAC Efficiency Score` veya `Card: HVAC Efficiency Display`
- **Ekle:** `HVAC Efficiency v34`
- **Format:** `0.0`, Display units = None
- **Beklenen (All):** 42–58

### C3 — AVG INSULATION SCORE (yeşil kart)
- **Kaldır:** `Card: Avg Insulation Score` veya `Card: Avg Portfolio Insulation Score`
- **Ekle:** `Insulation Score v34`
- **Format:** `0.0`, Display units = None
- **Beklenen (All):** 62–78

### C4 — HEAT LOSS kWh/m²·yr (mavi kart)
- **Kaldır:** `Heat Loss kWh m2 Annual` veya `Heat Loss kWh m2 Display`
- **Ekle:** `Heat Loss kWh m2 Annual v34`
- **Format → Custom:** `0.0" kWh/m²"`, Display units = None
- **Beklenen (All):** 60–110 kWh/m²

### C5 — BUILDINGS FOR RETROFIT (kırmızı kart)
- **Şu anda 0 gösteriyor — kontrol et:** eğer `Retrofit Count v34` bind'lıysa dokunma.
- Eğer eski ölçü bind'lıysa: **Ekle:** `Retrofit Count v34`
- **Format:** `0` (tam sayı)
- **Beklenen (All):** 1–3

> **C1–C4 hâlâ `--` dönüyorsa:** Data pane'de ölçü adını arama çubuğuna yaz (`v34` yaz) → görünüyor mu? Görünmüyorsa Adım 0 tamamlanmamış.

---

## ADIM 4 — V1: HVAC ENERGY BREAKDOWN (stacked area/column)

**V1 visual tıkla → Fields pane:**

| Slot | Şu an (muhtemelen) | Yeni (v34) |
|---|---|---|
| **X-axis** | `YearMonth` veya `Date[Date]` | `Date[YearMonth]` (sort by `Date[MonthIndex]`) |
| **Y-axis** | `Heating Energy kWh` (eski) | `Heating Energy kWh v34` |
| **Y-axis** | `Cooling Energy kWh` (eski) | `Cooling Energy kWh v34` |
| **Y-axis** | `Ventilation Energy kWh` (eski) | `Ventilation Energy kWh v34` |

**Adımlar:**
1. Y-axis'teki 3 eski ölçüyü X ile kaldır
2. `Heating Energy kWh v34` → Y-axis'e sürükle
3. `Cooling Energy kWh v34` → Y-axis'e sürükle
4. `Ventilation Energy kWh v34` → Y-axis'e sürükle
5. **Format → Data colors:**
   - Heating → `#E24B4A`
   - Cooling → `#00D4FF`
   - Ventilation → `#FFC107`
6. **Format → Background:** transparent ON
7. **X-axis sort:** `Date[YearMonth]` → Sort by Column → `Date[MonthIndex]`

> **V1 hâlâ boşsa:** Date ilişkisi sorunu (Adım 2'ye dön). Geçici test: X-axis'e `gold_hvac_analytics[year_month]` kolonunu direkt koy (ilişki bypass) → veri geliyorsa ilişki inactive.

---

## ADIM 5 — V2: BUILDING HVAC SYSTEM SUMMARY (tablo) — v35 gerekli!

**V2 visual tıkla → Columns pane:**

Bu tabloda tüm binalar "Heat Pump" gösteriyor — eski `System Type Display` / `System Type Display Robust` ölçüsünden geliyor. **Tüm sütunları aşağıdaki v34 versiyonlarıyla değiştir:**

⚠️ **v34 değil, v35 kullan!** v34'teki ALLEXCEPT bug'ı V2'yi bozuyor (tüm satırlar aynı değeri gösteriyor).

| # | Sütun adı | ESKİ | YENİ (v35) |
|---|---|---|---|
| 1 | Building Name | `silver_building_master[building_name]` | **Değişmez** (kolon, ölçü değil) |
| 2 | System Type | `System Type Display v34` / eski | **`System Type Display v35`** |
| 3 | Priority | `Renovation Priority Icon v34` / eski | **`Renovation Priority Icon v35`** |
| 4 | COP | `COP Display v34` / eski | **`COP Display v35`** |
| 5 | Insulation | `Insulation Score` veya eski | **`Insulation Score v34`** (bu çalışıyor, v35 yok) |
| 6 | Heat Loss | `Heat Loss kWh m2 Annual` | **`Heat Loss kWh m2 Annual v34`** (bu çalışıyor) |
| 7 | Action | `Action Recommendation v34` / eski | **`Action Recommendation v35`** |

**Adımlar:**
1. Her eski sütunu `Columns` listesinden **X** ile kaldır
2. Yeni ölçüleri sırayla sürükle
3. **Format → Values → Font size:** 8.5 · **Padding:** 4

**Beklenen V2 çıktısı:**
```
Berliner Bürogebäude    🔵 Heat Pump (ASHP/GSHP)  🟢 Low    3.xx (rated)  Monitor SCOP & service
Amsterdam Universiteit  🟠 Gas Boiler (CSRD risk)  🔴 High   n/a (gas)     Switch to ASHP + insulate
Frankfurt Klinikum      🟠 Gas Boiler (CSRD risk)  🔴 High   n/a (gas)     Switch to ASHP + insulate
Hamburg Logistics       🟠 Gas Boiler (CSRD risk)  🟡 Medium n/a (gas)     Plan ASHP retrofit by 2030
...
```

---

## ADIM 6 — V3: ENVELOPE U-VALUES (clustered bar)

V3 muhtemelen boş çünkü `U-Value Categories` calculated table eksik.

### 6.1 — Calculated Table Oluştur

**DAX query view → New measure değil, New table:**

```dax
U-Value Categories =
DATATABLE (
    "Component", STRING,
    "SortIdx", INTEGER,
    "Reference_GEG", DOUBLE,
    {
        { "Wall",   1, 0.24 },
        { "Roof",   2, 0.20 },
        { "Floor",  3, 0.30 },
        { "Window", 4, 1.30 }
    }
)
```

### 6.2 — U-Value Actual Ölçüsü Ekle

⚠️ **KOLON ADI DÜZELTİLDİ (2026-05-04)**: Önceki versiyonda `u_value_wall` gibi yanlış isimler vardı. Doğru isimler `wall_u_value` formatında.

```dax
U-Value Actual =
VAR _comp = MAX ( 'U-Value Categories'[Component] )
RETURN
    SWITCH (
        _comp,
        "Wall",   AVERAGE ( silver_building_master[wall_u_value] ),
        "Roof",   AVERAGE ( silver_building_master[roof_u_value] ),
        "Floor",  AVERAGE ( silver_building_master[floor_u_value] ),
        "Window", AVERAGE ( silver_building_master[window_u_value] )
    )
```

### 6.3 — V3 Visual Bind

**Visual type:** Clustered bar chart (horizontal)

| Slot | Field |
|---|---|
| Y-axis (categories) | `U-Value Categories[Component]` (sort by `SortIdx`) |
| X-axis (Value) | `U-Value Actual` |
| X-axis (Reference line) | `U-Value Categories[Reference_GEG]` — **Format → Reference line** olarak ekle |

**Format:**
- X-axis title: `W/m²K`
- Y-axis title: hide
- Data colors: `#00D4FF`
- Reference line: dashed, `#E24B4A`, label "GEG 2023"

> **Not:** `silver_building_master[u_value_wall]` gibi kolonlar yoksa → Notebook 02 veya silver_building_master tablosunu kontrol et. Bu kolonlar zaten silver schema'da tanımlandı.

---

## ADIM 7 — V4: INSULATION SCORE BY BUILDING (horizontal bar)

**V4 visual tıkla:**

| Slot | Eski | Yeni |
|---|---|---|
| Y-axis | `building_name` | `silver_building_master[building_name]` |
| X-axis | `Insulation Score` (eski) | **`Insulation Score v34`** |

**Format:**
- Sort: `Insulation Score v34` descending
- X-axis: Min = 0, Max = 100
- Data colors → **fx → Rules:**
  - 0–55 → `#E24B4A`
  - 55–75 → `#FFC107`
  - 75–100 → `#1D9E75`

> **6 bar görmen lazım.** Eğer 3 bar varsa → Edit interactions: S5 (Building slicer) → V4 üstünde **None** seç.

---

## ADIM 8 — V5: RENOVATION PRIORITY MATRIX (scatter)

**V5 visual tıkla:**

⚠️ **Color saturation için v35 kullan!** v34'teki ALLEXCEPT bug'ı tüm bubble'ları aynı renge boyadı.

| Slot | Eski | Yeni |
|---|---|---|
| X-axis | `Insulation Score` | **`Insulation Score v34`** |
| Y-axis | `HVAC Efficiency Score` | **`HVAC Efficiency v34`** |
| Size | `Building Total Consumption kWh Annual` | **`Total Consumption kWh v34`** |
| Details | `building_name` | `silver_building_master[building_name]` |
| Color saturation | `Renovation Priority Color v34` | **`Renovation Priority Color v35`** |

**Bubble color (conditional formatting):**
- Format → Bubbles → Color → **fx → Rules:**
  - Value = 1 → `#1D9E75` (green)
  - Value = 2 → `#FFC107` (amber)
  - Value = 3 → `#E24B4A` (red)

**Reference lines:**
- Y-axis → Reference line: Y = 60, label "Efficiency target", dashed
- X-axis → Reference line: X = 70, label "Insulation target", dashed

**Bubble labels:** ON → `building_name`, font 7, white

**Beklenen scatter yerleşimi:**
```
Sağ-üst (iyi): Berliner — yeşil bubble
Sol-alt (acil): Amsterdam, Frankfurt — kırmızı bubble
Orta: Istanbul, Hamburg, Wien — amber bubble
```

---

## ADIM 9 — EDIT INTERACTIONS (5 dk)

**View → Edit interactions ON**

| Slicer | V2 (Tablo) | V4 (Insulation bar) |
|---|---|---|
| S1 Date | **None** (tablo tarih-bağımsız) | Filter (normal) |
| S2 Country | **None** | Filter |
| S3 Building Type | **None** | Filter |
| S4 System Type | **None** | Filter |
| S5 Building | **Filter** | **None** (daima 6 bar) |

---

## ADIM 10 — VALIDATION CHECKLIST

Slicer'lar **(All)** iken:

| KPI/Visual | Beklenen | ❌ Hâlâ sorunsa |
|---|---|---|
| C1 HVAC Share | **35–55 %** | v34 import edilmedi (Adım 0) |
| C2 HVAC Efficiency | **42–58** | Ölçü adı yanlış bind |
| C3 Avg Insulation | **62–78** | Ölçü adı yanlış bind |
| C4 Heat Loss | **60–110 kWh/m²** | Yıllık değil aylık bağlı |
| C5 Retrofit | **1–3** | Doğruysa dokunma |
| V1 Breakdown | 12 ay × 3 series, kış heating peak | Date ilişkisi inactive |
| V2 Sistem tipi | Berliner=HP, diğerleri=Gas | Eski ölçü hâlâ bind'lı |
| V2 Aksiyon | Her satır farklı metin | `Action Recommendation v34` değil eski |
| V3 U-Values | 4 component bar + GEG reference | Calculated table yok |
| V4 Insulation | 6 bar, Berliner en yüksek | Filter sızıntısı (Adım 9) |
| V5 Matrix | 6 bubble, 3 farklı renk | Color saturation binding yanlış |

---

## TEK BİNA SENARYO TESTİ

**S5 → "Berliner Bürogebäude" seç:**
- C1: 45–55%, C2: 50–62, C3: 85–92, C4: 35–50, C5: 0
- V2: 1 satır, System = "🔵 Heat Pump", COP = "3.xx (rated)"
- V4: 1 bar highlighted (diğerleri gri)
- V5: 1 bubble

**S5 → "Frankfurt Klinikum" seç:**
- Tüm KPI'lar sayısal değer göstermeli (v34 fallback sayesinde)
- C5: 1, System = "🟠 Gas Boiler"

---

## TAMAMLANDI KRİTERLERİ

- [ ] 5 KPI card hepsi sayısal değer gösteriyor (`--` yok)
- [ ] V1: 12 ay × 3 series görünüyor, kış heating peak var
- [ ] V2: Berliner = Heat Pump, diğerleri = Gas Boiler
- [ ] V2: Her satırda farklı Action metni
- [ ] V3: 4 component bar + GEG reference line görünüyor
- [ ] V4: 6 bar görünüyor (renk gradyanı: kırmızı-sarı-yeşil)
- [ ] V5: 6 bubble + 3 farklı renk yerleşimi doğru

**Bu 7 madde tamam → ekran kaydı paylaş → Page 9 (Battery Strategy) planına geçeriz.**
