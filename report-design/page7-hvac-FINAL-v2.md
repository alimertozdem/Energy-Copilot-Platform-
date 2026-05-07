# Page 7 — HVAC & Building Envelope · FINAL v2

**Status:** READY TO APPLY · 2026-05-03
**Replaces:** `page7-hvac-final-plan.md` (v1, çok soyuttu)
**Background:** `report-design/backgrounds/07_hvac_building_envelope.png` (yeni, frames-only)
**DAX:** `semantic-model/42_dax_v33_page7_hvac_final.dax` (zaten import edildi)

---

## 0 · BU DOKÜMANI NASIL OKUYACAKSIN

Doküman 4 bölümden oluşur. **Sırayla uygula** — her bölüm bir önceki üstüne kurulur.

| Sıra | Bölüm | Süre | Çıktı |
|---|---|---|---|
| § 1 | Root cause — neden hâlâ "--" gösteriyor | 5 dk okuma | Anla |
| § 2 | Veri sağlığı kontrolü (Frankfurt B005) | 5 dk | Notebook 11 re-run kararı |
| § 3 | Görsel-by-görsel bind talimatları | 60 dk | 5 KPI + 5 visual çalışır halde |
| § 4 | Edit interactions + validation | 15 dk | Sayfa kilitli, sayılar mantıklı |

**Toplam:** ~85 dk · Hiçbir adımı atlama, ekran-by-ekran kontrol et.

---

## § 1 · KÖK SEBEP — NEDEN SAYFA HÂLÂ "--" GÖSTERIYOR

DAX v33 ölçülerini import ettin ama görseller hâlâ boş. **Üç olası sebep var, hepsini tek tek elimine edeceğiz:**

### Sebep A — Eski ölçü hâlâ Card visual'a bağlı (en sık)
Yeni ölçüyü modele eklemek **yetmez** — Card visual'ın **Field** kutusunun içindeki ölçüyü de değiştirmen gerekir.

> **Test:** C1 (HVAC Share) Card visual'a tıkla → sağdaki **Visualizations** panelinden **Fields** sekmesi → "Value" alanında ne yazıyor?  
> ❌ `HVAC Share Pct` veya `HVAC Share Pct Safe` → bu eski ölçü, hâlâ boş.  
> ✅ `Card: HVAC Share Pct Display` → yeni ölçü, doğru.

§ 3'te her Card için **eski ölçüyü kaldır + yeniyi ekle** adımları açıkça yazıyor.

### Sebep B — Frankfurt B005 satırı `gold_hvac_analytics`'te YOK
Slicer'da Frankfurt seçilince tüm HVAC görselleri boşalır çünkü ilgili satır tabloda yok. § 2'de doğrulayıp düzeltiyoruz.

### Sebep C — Slicer kombinasyonu boş kesişim üretiyor
Örn. "Country = DE" + "Building Type = Office" + "System Type = HP" üçü birleşince sadece B001 kalır; o da bir bina seçeceksen `building` slicer'ı zaten yapıyor, çift filtreleme sıfır satır verebilir.  
**Çözüm § 4'te:** edit-interactions ile slicer'lar birbiriyle çakışmayacak.

---

## § 2 · VERİ SAĞLIĞI — FRANKFURT B005 KONTROLÜ

### 2.1 — Power BI'da hızlı test (2 dk)

**Yeni boş sayfa aç (geçici):**

1. **Insert → Table** ekle. Fields: `gold_hvac_analytics[building_id]`
2. Beklenen sonuç: B001, B002, B003, B004, **B005**, B006 (6 satır).

> **B005 görünüyorsa** → Veri tamam, sorun bind'da. § 3'e geç.  
> **B005 görünmüyorsa** → Notebook 11 Fabric'te re-run lazım.

### 2.2 — Notebook 11 re-run (gerekirse, 10 dk)

Fabric workspace → `notebooks/gold/11_hvac_analytics_engine` → **Run all cells**.

Çalıştırıldıktan sonra:
- **Refresh** Power BI semantic model (Workspace → Semantic model → Refresh now)
- Yeniden 2.1 testi → B005 satırı gelmiş olmalı

> **Kod değişikliği YOK.** Notebook zaten 6 binayı işliyor; muhtemelen son full-run yapılmadı veya kaynak `silver_consumption` tablosunda B005 verisi sonradan landed oldu.

---

## § 3 · GÖRSEL-BY-GÖRSEL BİND TALİMATLARI

> Her blok şu üç bölümü içerir: **(a) Eski ölçüyü kaldır**, **(b) Yeni ölçüyü ekle**, **(c) Format string'i ayarla**.  
> Pozisyonlar (X, Y, W, H) yeni `07_hvac_building_envelope.png` çerçevesiyle birebir.

---

### § 3.0 — TITLE BAR + LOGO (DEĞİŞMİYOR)
Background'taki yeri korundu. Slicer/Card pozisyonları altta yeniden hizalandı.

---

### § 3.1 — ROW 1: 5 SLICER (y=92–130)

| # | Position (X, Y, W, H) | Slicer Field | Type | Default selection |
|---|---|---|---|---|
| S1 | 30, 92, 216, 38 | `Date[Date]` | **Between** (slider) | Tüm yıl |
| S2 | 281, 92, 216, 38 | `silver_building_master[country]` | **Dropdown** | (All) |
| S3 | 532, 92, 216, 38 | `silver_building_master[building_type]` | **Dropdown** | (All) |
| S4 | 783, 92, 216, 38 | `silver_building_master[system_type_label]` | **Dropdown** | (All) |
| S5 | 1034, 92, 216, 38 | `silver_building_master[building_name]` | **Dropdown** | (All) |

> **NOT — S4 kaynak alanı:** Eğer `silver_building_master[system_type_label]` yoksa, calculated column ekle:  
> `system_type_label = SWITCH(TRUE(), silver_building_master[has_heat_pump]=TRUE() && silver_building_master[has_gas]=FALSE(), "Heat Pump", silver_building_master[has_heat_pump]=TRUE() && silver_building_master[has_gas]=TRUE(), "Hybrid", "Gas")`

---

### § 3.2 — ROW 2: 5 KPI CARDS (y=152–246)

#### C1 — HVAC SHARE (Position: 30, 152, 216, 94 · Border: ORANGE)

**Visual type:** Card (new)

**(a) Eski ölçüyü kaldır:**
1. C1 Card visual'a tıkla.
2. **Fields** panelinden `Value` slot'una bak.
3. Eğer `HVAC Share Pct` / `HVAC Share Pct Safe` / başka bir şey varsa → **X** ile kaldır.

**(b) Yeni ölçüyü ekle:**
- Drag → **`Card: HVAC Share Pct Display`** → `Value` slot.

**(c) Format ayarı:**
- Card visual → **Format pane (Format your visual)** → **Callout value** → **Display units = None**
- **Value decimal places = 1**
- **Format your visual** → **Callout value** → expand format options → **Format → Custom: `0.0 "%"`**
- Beklenen: `42.3 %`

**(d) Conditional formatting (opsiyonel ama önerilen):**
- **Format → Callout value → Color** → **fx (conditional)**
- Rule: `if value < 30 → Red (#E24B4A) ; if 30–55 → Yellow (#FFC107) ; if > 55 → Orange (#FF6B35)`

---

#### C2 — HVAC EFFICIENCY (Position: 281, 152, 216, 94 · Border: YELLOW)

**(a) Kaldır:** `HVAC Efficiency Score` (eğer doğrudan bağlıysa).
**(b) Ekle:** **`Card: HVAC Efficiency Display`** → `Value`.
**(c) Format:** `0.0` · Display units = None.
**(d) Reference line (opsiyonel):** Format → Reference line → 60 (target).

---

#### C3 — AVG INSULATION (Position: 532, 152, 216, 94 · Border: GREEN)

**(a) Kaldır:** `Card: Avg Portfolio Insulation Score` (varsa).
**(b) Ekle:** **`Card: Avg Insulation Score`** → `Value`.

> **DİKKAT:** Bu ölçü v33'te `[Card: Avg Portfolio Insulation Score]` ölçüsünün alias'ı. Eğer **`Card: Avg Portfolio Insulation Score`** modelinde yoksa hata verir. Bu durumda § 3.2 sonundaki **fallback ölçü**ye geç.

**(c) Format:** `0.0` · Display units = None.
**(d) Reference line:** 75 (Berliner-class).

##### Fallback (eğer alias kaynağı yoksa)
DAX editor → New Measure:
```dax
Card: Avg Insulation Score =
AVERAGEX (
    VALUES ( silver_building_master[building_id] ),
    [Insulation Score]
)
```

---

#### C4 — HEAT LOSS kWh/m²·yr (Position: 783, 152, 216, 94 · Border: BLUE)

**(a) Kaldır:** `Heat Loss kWh m2 Month` veya `Heat Loss kWh m2 Display`.
**(b) Ekle:** **`Heat Loss kWh m2 Annual`** (DAX v8'de var) → `Value`.
**(c) Format:** Custom: `0.0 " kWh/m²"` · Display units = None.
**(d) Reference line:** 50 (good envelope target).

> **Not:** Annual değeri tek-bina seçimde 30–150 aralığında olmalı. Portföy ortalaması ~70–110 bekleniyor.

---

#### C5 — RETROFIT NEEDED (Position: 1034, 152, 216, 94 · Border: RED)

**(a) Kaldır:** `High Priority Building Count` (varsa).
**(b) Ekle:** **`Card: Buildings For Retrofit`** → `Value`.
**(c) Format:** `0` (whole number).
**(d) Conditional formatting:**
- Color rule: `if value > 0 → #E24B4A ; else → default white`.
- Optional ikon: Format → Callout value → expand → bir Unicode ikon ekle (örn. 🔴) **prefix** alanına.

---

### § 3.3 — ROW 3: WIDE VISUALS (y=268–478)

#### V1 — HVAC ENERGY BREAKDOWN (Position: 30, 268, 605, 210 · Border: ORANGE)

**Visual type:** Line and stacked column chart **VEYA** Stacked area chart

**Field bindings:**

| Slot | Field/Measure | Format |
|---|---|---|
| **X-axis** | `Date[year_month]` (sort by `MonthIndex`) | – |
| **Y-axis (Stack)** | `Heating Energy kWh` | 0 |
| **Y-axis (Stack)** | `Cooling Energy kWh` | 0 |
| **Y-axis (Stack)** | `Ventilation Energy kWh` | 0 |
| **Legend (auto)** | (3 series görünecek) | – |

**Format:**
- Title: hide (background'ta var)
- Background: transparent ON, **Background color = white, transparency = 100%**
- Data colors:
  - Heating → **`#E24B4A`** (red)
  - Cooling → **`#00D4FF`** (blue)
  - Ventilation → **`#FFC107`** (yellow)
- X-axis title: hide
- Legend: bottom, font 8

> **Beklenen:** 12 ay, kış aylarında heating %70+, yaz aylarında cooling %50+, ventilation tüm yıl ~10–15%.

---

#### V2 — BUILDING HVAC SYSTEM SUMMARY (Position: 645, 268, 605, 210 · Border: GREEN)

**Visual type:** Table

**Columns (sıra önemli):**

| # | Column | Source | Format / Width |
|---|---|---|---|
| 1 | Building | `silver_building_master[building_name]` | width 110 |
| 2 | System | **`System Type Display Robust`** | width 130 |
| 3 | Priority | **`Renovation Priority Icon Robust`** | width 90 |
| 4 | COP | **`COP Display Robust`** | width 80 |
| 5 | Insulation | **`Insulation Rating Label`** | width 80 |
| 6 | Heat Loss | **`Heat Loss kWh m2 Annual`** | format `0.0`, width 80 |
| 7 | Action | **`Action Recommendation Short`** | width 200 |

**Önemli:** Eski tabloda `System Type Label` veya `System Type Display` (CALCULATE+ALLEXCEPT bug'lı) kolonu varsa **MUTLAKA kaldır** ve yerine `System Type Display Robust` ekle. Bu seninkinde "hepsi Heat Pump" görünmesinin sebebi.

**Format:**
- Title: hide
- Background: transparent
- Header: navy bold, font 9
- Values: 8.5 pt, padding 4
- Grid: row separator 1px, color `#1A2A44`

---

### § 3.4 — ROW 4: DETAIL VISUALS (y=498–706)

#### V3 — ENVELOPE U-VALUES (Position: 30, 498, 400, 208 · Border: BLUE)

**Visual type:** Clustered bar chart

**Bindings:**

| Slot | Field/Measure |
|---|---|
| Y-axis (categories) | Hard-coded 4 satır: Wall, Roof, Floor, Window |
| X-axis (bar) | (her biri için actual value) |
| Reference line | (GEG 2023 reference per category) |

**En basit yaklaşım — Switcher table kur:**

DAX editor → New table:
```dax
U-Value Categories =
DATATABLE (
    "Component", STRING,
    "SortIdx", INTEGER,
    "Reference (GEG 2023)", DOUBLE,
    {
        { "Wall",   1, 0.24 },
        { "Roof",   2, 0.20 },
        { "Floor",  3, 0.30 },
        { "Window", 4, 1.30 }
    }
)
```

Sonra measure:
```dax
U-Value Actual =
VAR _comp = MAX('U-Value Categories'[Component])
RETURN
    SWITCH(
        _comp,
        "Wall",   AVERAGE(silver_building_master[u_value_wall]),
        "Roof",   AVERAGE(silver_building_master[u_value_roof]),
        "Floor",  AVERAGE(silver_building_master[u_value_floor]),
        "Window", AVERAGE(silver_building_master[u_value_window])
    )
```

**Visual fields:**
- **Y-axis:** `'U-Value Categories'[Component]` (sort by `SortIdx`)
- **X-axis (bar):** `U-Value Actual`
- **X-axis (line):** `'U-Value Categories'[Reference (GEG 2023)]`

> Beklenen: Berliner seçimde Wall ~0.18, Window ~0.95 (referansın altında ✅). Amsterdam seçimde Wall ~0.40+ (referansı aşıyor ❌).

---

#### V4 — INSULATION SCORE BY BUILDING (Position: 440, 498, 400, 208 · Border: YELLOW)

**Visual type:** Clustered bar chart (horizontal)

**Bindings:**

| Slot | Field/Measure |
|---|---|
| Y-axis | `silver_building_master[building_name]` |
| X-axis | `Insulation Score` |
| Sort by | `Insulation Score` descending |

**Format:**
- Data colors → conditional formatting:
  - **fx → Rules** → `0–55: #E24B4A · 55–75: #FFC107 · 75–100: #1D9E75`
- X-axis range: 0–100 (Format → X-axis → Range → Min 0, Max 100)
- Y-axis title: hide

> **Bu görselde 6 bar görmen lazım** (B001–B006). Eğer 3 bar görüyorsan → V4 visual'a slicer filter'ı sızıyor (§ 4 edit interactions ile çözeceğiz).

---

#### V5 — RENOVATION PRIORITY MATRIX (Position: 850, 498, 400, 208 · Border: RED)

**Visual type:** Scatter chart

**Bindings:**

| Slot | Field/Measure |
|---|---|
| **X-axis** | `Insulation Score` |
| **Y-axis** | `HVAC Efficiency Score` |
| **Values (Size)** | `Building Total Consumption kWh Annual` |
| **Details (legend)** | `silver_building_master[building_name]` |
| **Color (saturation)** | `Renovation Priority Color` |

**Format:**
- Title: hide
- X-axis range: 0–100, title "Insulation →"
- Y-axis range: 0–100, title "HVAC Efficiency →"
- **Bubble color saturation:**
  - Format → Bubbles → Colors → **fx (conditional)** → Rules:
    - `1 → #1D9E75 (green)`
    - `2 → #FFC107 (amber)`
    - `3 → #E24B4A (red)`
- **Quadrant guidelines (Reference Lines):**
  - Format → Y-axis → Reference Line → Y=60 (Efficiency target)
  - Format → X-axis → Reference Line → X=70 (Insulation target)
- Bubble label: ON, "Building name", font 7, white

> **Beklenen yerleşim (slicer'lar (All) iken):**
> - **Sağ-üst (efficient + insulated):** B001 Berliner — yeşil bubble
> - **Sol-alt (retrofit-now):** B006 Amsterdam, B005 Frankfurt — kırmızı bubble
> - **Orta:** B002 Istanbul, B003 Hamburg, B004 Wien — amber bubble

---

## § 4 · EDIT INTERACTIONS + VALIDATION

### 4.1 — Edit Interactions (5 dk)

**Kural:** S5 (Building) **HARİÇ** hiçbir slicer V2 (Building HVAC Summary) tablosunu filtrelememelidir — table portföy genelini göstermeli.

**Adımlar:**

1. **View** sekmesi → **Edit interactions** ON.
2. **S2 (Country)** slicer'ı seç → V2 üstündeki ikondan **"None"** seç.
3. Aynısını **S3 (Building Type)**, **S4 (System Type)** için tekrarla.
4. **S5 (Building)** slicer'ı seç → V2 üstündeki ikon **"Filter"** olarak kalsın (V2 tek bina seçimi destekleyecek).
5. **S1 (Date)** → V2 ile **None** (tablo "şu anki" durum gösterir, tarih bağımsız).

**V4 (Insulation Score by Building) için:**
- S5 (Building) → V4 üstünde **"None"** olmalı (her zaman 6 bar göstermeli).

### 4.2 — Field-by-field validation checklist

Slicer'lar `(All)` iken şu değerleri görmen lazım:

| KPI / Visual | Beklenen değer | Kontrol et |
|---|---|---|
| C1 HVAC Share | **35–55 %** | Eğer `2.78` → format string yanlış (§3.2 C1) |
| C2 HVAC Efficiency | **42–58** | Eğer `—` → ölçü hâlâ eski |
| C3 Avg Insulation | **65–78** | Eğer `—` → fallback ölçüyü ekle |
| C4 Heat Loss | **60–110 kWh/m²·yr** | – |
| C5 Retrofit Needed | **1–3** binadan biri | – |
| V1 Heating peak | Aralık-Şubat = pikme noktası | – |
| V2 6 satır | B001=HP, B002–B006=Gas | Hepsi HP ise § 3.3 V2 talimatı atlandı |
| V3 Wall U-value | **0.20–0.45** | – |
| V4 6 bar | Berliner en yüksek (~85), Amsterdam en düşük (~45) | 3 bar varsa § 4.1 atlandı |
| V5 6 bubble | Berliner sağ-üst yeşil, Amsterdam sol-alt kırmızı | – |

### 4.3 — Tek-bina senaryo testi

**Slicer S5 → "B001 Berliner" seç:**
- C1: 45–55%
- C2: 50–62
- C3: 85–92
- C4: 35–50 kWh/m²·yr
- C5: 0 (yeni v33 sayesinde "—" değil "0" görünmeli)
- V2: 1 satır kalmalı

**Slicer S5 → "B005 Frankfurt" seç:**
- Tüm KPI'lar **artık değer dönmeli** (notebook 11 re-run sonrası)
- COP: `n/a (non-HP)` (gas binası)
- C5: 1 (kendisi retrofit gerekiyor)

---

## § 5 · TAMAMLANDI KRİTERLERİ

Bu sayfa şu 7 kriteri sağladığında "DONE":

- [ ] Yeni background uygulanmış (`07_hvac_building_envelope.png`)
- [ ] 5 KPI card hepsi sayısal değer gösteriyor (slicer (All) iken)
- [ ] V2 tablosunda Berliner=HP, diğerleri=Gas (System Type Display Robust)
- [ ] V2 tablosunda her bina farklı Action (Action Recommendation Short)
- [ ] V4 6 bar gösteriyor (filter sızıntısı yok)
- [ ] V5 6 bubble + 4 farklı renk (priority color binding ✓)
- [ ] Edit interactions kuralları uygulandı (§ 4.1)

Bu 7 maddeyi işaretlediğinde ekran-kaydı paylaş — son onayı veririm, sonra Page 9 (Battery Strategy) planına geçeriz.

---

## EK A · DAX v33 hızlı referans

11 ölçü, hangi visual'a:

| Ölçü | Visual | Slot |
|---|---|---|
| `Card: HVAC Share Pct Display` | C1 | Value |
| `Card: HVAC Efficiency Display` | C2 | Value |
| `Card: Avg Insulation Score` | C3 | Value |
| `Card: Buildings For Retrofit` | C5 | Value |
| `COP Display Robust` | V2 | Column |
| `System Type Display Robust` | V2 | Column |
| `Renovation Priority Icon Robust` | V2 | Column |
| `Action Recommendation Short` | V2 | Column |
| `Renovation Priority Color` | V5 | Color saturation |
| `Building Total Consumption kWh Annual` | V5 | Size |
| `Card: Avg HP COP Robust` | (rezerve) | tooltip / V5 detail |

---

**SON.** Sorunu yaşadığın anda hangi adımda olduğunu söyle, oradan devam edelim.
