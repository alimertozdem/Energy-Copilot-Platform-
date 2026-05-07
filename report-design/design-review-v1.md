# Energy Copilot — Dashboard Tasarım Review v1
## Sayfa 1-3 için Energy Manager bakış açısı ile denetim + Sayfa 4-6 için final plan

> **Amaç:** Mevcut 3 sayfanın gerçekçilik, doğruluk ve karar-alıcı kullanışlılığı açısından düzeltilmesi + 4-6. sayfalar için hazır spec.
> **Bakış açısı:** Bir commercial portfolio energy manager'ın "sabah kahvesiyle açtığı dashboard'da nelere bakmak isteyeceği".

---

## 🔴 KRİTİK HATALAR (önce bunları düzelt)

### Bug #1 — Battery SoC = %7450 gösteriyor (Sayfa 2)
**Kök neden:** `Avg Battery SoC Pct` measure değeri 0–100 arasında sayı (örn. 74.5) döndürüyor. Power BI Card'da **Format as Percentage** açık kalınca 74.5 × 100 = 7450% oluyor.

**Düzeltme seçenekleri (biri yeterli):**
- **A (önerilen):** Card format paneli → **Percentage format kapat**, yanına manuel `"%"` suffix ekle. Model görünümünde measure üzerinde `Format string → #,##0.0"%"` seç.
- **B:** DAX'ı değiştir — ölçüyü `/100` ile böl ve format'ı `0.0%` olarak tut.

> Biz **A seçeneğini** uyguluyoruz çünkü DAX'ı sade tutmak daha iyi. Tüm diğer `*_Pct` ölçülerinde aynı kural: değer 0–100, Format string `#,##0.0"%"`.

### Bug #2 — Card'larda `K` suffix / binlik kısaltma (Sayfa 1, 3)
**Örnek:** Active Anomaly Count `26K` gösteriyor ama aslında 26. Peak Demand `2.3K kW` (olması gereken 2,3 kW vs 2300 kW ayrımı belirsiz).

**Düzeltme:** Her Count/Integer card'da:
- Format tab → **Display units = None**
- Thousand separator = **On**
- Value decimals = **0** (count için) veya gerektiği kadar (metrik için)

Genel kural: **Count tipi ölçülerde asla Auto/K/M kısaltması kullanma.**

### Bug #3 — Total CO2 Tons = 2.96M (Sayfa 1)
**Anomali:** Consumption 2.96M kWh iken CO2 = 2.96M ton → 1000 kgCO₂/kWh emisyon faktörü anlamına gelir. Gerçek grid faktörü 0.3–0.5 kgCO₂/kWh, yani portfolio için beklenti **~1000–1500 ton**.

**Notebook doğrulandı:** Emisyon faktörleri doğru (DE: 0.380 UBA 2024, TR: 0.442 TEİAŞ 2024). Sorun notebook'ta değil, **Power BI kartında**.

**Gerçek kök neden (yüksek ihtimal):**
Kart yanlış measure'a bağlanmış — muhtemelen `Total CO2 Emissions kg` (kg cinsinden) kullanılıyor ama label "ton" yazıyor. Ya da Display Units "Millions" olarak ayarlı ve iki measure'ı karıştırıyorsun.

**Doğru kart konfigürasyonu:**
- Field: **`[Total CO2 Tons]`** (= `[Total CO2 Emissions tCO2]` alias'ı)
- Format string: `#,##0.0 "ton"`
- Display units: **None**
- Value decimals: 1

**Sanity check:** 2.96M kWh × 0.4 kgCO₂/kWh = 1,184,000 kg = **~1,184 ton** beklenmeli. 2.96M ton değeri 2500× yüksek → kg/ton birim karışıklığı veya Auto-scaling kazası.

- [x] Notebook emisyon faktörü doğrulandı (DE: 0.380, TR: 0.442).
- [ ] Sayfa 1 & Sayfa 6'daki CO2 kartlarına field selector'dan `Total CO2 Tons` seç, Display Units = None yap.

### Bug #4 — Avg Resolution Time card tarih gösteriyor (Sayfa 3)
**Kök neden:** `Avg Resolution Hours` measure `BLANK()` döndürüyor (tabloda `resolved_at` sütunu yok). Power BI BLANK'i tarih formatıyla render edince "01.01.1900" tipi şey çıkıyor.

**Düzeltme (iki yol):**

**Yol A (kısa):** Şimdilik kartı değiştir — yerine **"Active Anomaly Rate"** (% unresolved) koy. Ölçü hazır: `[Active Anomaly Rate Pct]`.

**Yol B (doğru, sonra):** `gold_anomaly_log` tablosuna `resolved_at` sütunu ekle (simulation: çözülenler için `detected_at + random(2h–72h)`). Sonra measure'ı:
```dax
Avg Resolution Hours =
AVERAGEX(
    FILTER(gold_anomaly_log, gold_anomaly_log[is_resolved] = TRUE),
    DATEDIFF(gold_anomaly_log[detected_at], gold_anomaly_log[resolved_at], HOUR)
)
```

> **Şimdilik Yol A uygulanacak.** Yol B "v2 backlog"a gidiyor.

### Bug #5 — Carbon Intensity etiketi yanlış (Sayfa 2)
**Mevcut:** Kartta `#,##0 "gCO2/kWh"` yazıyor ama measure `Avg Carbon Intensity kg m2` → değer **kg CO₂ / m² / gün**.

**Düzeltme:** Format string → `#,##0.00 "kg CO₂/m²·gün"` yap. Anlam değişiyor — "Bu binanın her m²'si günde ortalama X kg CO₂ üretiyor". ASHRAE 90.1 referansı: modern ofis ≤ 0.10 kg/m²/gün.

---

## 🟡 İYİLEŞTİRMELER — Energy Manager bakış açısı

### Sayfa 1 (Portfolio Overview) — eklenmesi gerekenler

| Slot | Neden lazım | Yeni measure | Kart/Görsel |
|------|------------|-------------|-------------|
| **YoY Consumption %** | Bir enerji yöneticisi ilk baktığı şey "geçen yıla göre ne oldu?" | `Consumption YoY Pct` | Card'ın alt satırında ↑/↓ göstergesi |
| **Solar Coverage %** | Portfolio yeşil hedefi — "tükettiğimin yüzde kaçı güneş?" | Zaten var: `Solar Coverage Pct` | Yeni card ekleyelim |
| **Top Consumer Building** | "Enerjinin yarısı tek bir binada mı?" — sorun olursa anında odaklanır | `Top Consumer Building` | Küçük text card |
| **EUI Benchmark Status (🟢🟡🟠🔴)** | Sayısal EUI'nin yanında renkli durum etiketi | `EUI Benchmark Status` | Card'da text |

**Donut "Building Type"** — kullanılmıyor artık, zaten Anomaly Severity donutuyla doldurulmuş. Sayfa 6'ya taşındı — doğru karar.

**Harita (map)** — Kullanıcı sol alta almış, iyi karar. Portfolio dağılımı için değerli.

**Monthly Energy Trend** — sadece tek çizgi. Yanına **previous year çizgisi** (dashed) eklemek YoY görsel için kritik → `Previous Year Consumption kWh` ile.

### Sayfa 2 (Building Detail) — eklenmesi gerekenler

| Slot | Neden lazım | Measure |
|------|------------|---------|
| **Load Factor %** | Peak vs ortalama oranı — yüksek = kötü (sivri tüketim) | `[Avg Load Factor Pct]` — zaten `avg_load_factor` kolonu var, yeni ölçü gerek |
| **Self-Consumption Rate** | Sadece PV binaları için — ürettiğinin % kaçını tükettiğin | Zaten var: `Avg Self Consumption Rate Pct` |
| **Cost vs Previous Period** | Aynı kart üzerine ↑€123 ↓€45 | Zaten var: `Cost Change Pct` |

**Solar vs Grid chart (mevcut)** — karışık, ölçüler farklı birim. **Ayır:**
- Chart A: **Solar Mix Donut** → Self-Consumed + Exported + Grid Import (3 dilim)
- Chart B: **Daily Solar vs Consumption** → 2 çizgili line chart (kWh, kWh)

**Battery SoC Trend** — ref line'lar doğru (%20, %80) ama daily grain'de SoC min/max range göstermek için **ribbon/area chart between min-max** kullan (single AVG yerine).

**HDD/CDD Scatter** — iki ayrı scatter yerine **tek scatter + conditional color** (noktaları HDD>0 mavi, CDD>0 turuncu) sayfayı sadeleştirir. Veya şimdiki gibi iki chart kalsın ama **R² label ekle** trend anlamı için.

### Sayfa 3 (Anomalies & Alerts) — eklenmesi gerekenler

| Slot | Neden lazım |
|------|------------|
| **MTTR (Mean Time To Resolve)** | Yol B tamamlandığında |
| **Anomaly Trend sparkline** (each building) | Hangi bina kötüleşiyor? |
| **Top Anomaly Type** | "Gece over-consumption en sık" → aksiyon ipucu |

**Monthly Anomalies chart** şu an count + rate karıştırıyor. Sadece **stacked column count (severity legend)** kalsın. Rate istiyorsak ayrı chart.

**Detail Table** — şu kolonlar olmalı:
`building_name | anomaly_type | severity | detected_at | metric_value | threshold_value | % breach | is_resolved`

`% breach` için yeni measure gerekmez, hesaplanmış `[Avg Threshold Breach Pct]` row context'te çalışır ama satır-bazlı **calculated column** olarak eklemek daha temiz:
```dax
-- gold_anomaly_log calculated column
breach_pct =
DIVIDE(
    gold_anomaly_log[metric_value] - gold_anomaly_log[threshold_value],
    gold_anomaly_log[threshold_value],
    0
) * 100
```

---

## 🟢 SAYFA 4, 5, 6 — FİNAL SPECLER

### Sayfa 4 — Forecast & Recommendations

**Üst şerit (Forecast zone):**
1. 7-Day Forecast kWh
2. 30-Day Forecast kWh
3. Model MAPE % — card (doğruluk rozeti: <10% 🟢, 10-20% 🟡, >20% 🔴)
4. Forecast + Confidence Interval Band (Line + Shaded area)
5. MAPE per Building (Horizontal bar)

**Alt şerit (Recommendations zone):**
6. Total Recommendations count
7. Critical Recommendations count
8. Expected Annual Savings € (card)
9. Total Net Capex € (subvansiyon sonrası — Total Investment yerine)
10. **Recommendations Table** — kolonlar:
    `rank | action_type | building_name | priority_label | annual_saving_eur | payback_years | net_capex_eur`
11. **Payback vs Savings Scatter** — X: payback_years, Y: annual_saving_eur, bubble size: capex, color: priority_label
    → "Sol-üst köşe en iyi yatırım (hızlı geri dönüş + yüksek tasarruf)"

**Yeni measure:**
- `MAPE Bucket` — text measure: 🟢 Excellent / 🟡 Good / 🔴 Poor.

### Sayfa 5 — Occupancy Analysis

**Üst kartlar:**
1. Avg Occupancy % (business hours only — `Avg Business Hours Occupancy Pct`)
2. Peak Occupancy Hour (zaten var)
3. After-Hours Occupancy % — **yeni kart**: 20:00-07:00 arası tüketim demek → enerji israfı sinyali
4. Calibrated Buildings Count (kalibrasyon coverage — zaten var)

**Ana görsel:**
5. **7×24 Heatmap** (Matrix, CF background) — mevcut spec iyi, dokunma

**Alt şerit:**
6. **Weekday vs Weekend line** (mevcut plan iyi)
7. **Building occupancy bar** (ref line %80 LEED)
8. **PHANTOM LOAD indicator table** — yeni görsel:
   → Bu bir scatter: X: `Avg After Hours Occupancy Pct`, Y: consumption'ın gece saatlerindeki payı. Sağ-üst = normal (çalışan bina). Sol-üst = fantom yük (boş ama yiyor).

### Sayfa 6 — Sustainability & Compliance

**Üst kartlar:**
1. Total CO₂ (ton) — CO2 Bug #3 düzeltildikten sonra
2. CO₂ Savings from Solar (ton)
3. **Net Carbon Footprint** (= gross - solar) — yeni, measure zaten var: `Net Carbon Footprint tCO2`
4. Carbon Intensity avg (kg/m²/gün) — Bug #5 etiketi düzeltilmiş hali
5. Renewable % (self-sufficiency)

**Grafikler:**
6. Monthly CO₂ Trend (line + hedef ref line: EU Taxonomy -50% by 2030)
7. **Country-Based Emissions** (bar) — emissions factor ülkeye göre farklı olduğu için anlamlı
8. **HDD / CDD Climate** (column) — 2024 vs 2025 karşılaştırmalı → iklim şiddeti artıyor mu?
9. **Building Type Donut** (Sayfa 1'den taşınan) — portföy kompozisyonu
10. **ESG Scorecard Table** — building × (EUI, CO2/m², Solar coverage %, Active anomaly count) → CSRD raporlaması için hazır matris

> `emission_source` alanı datasette yok → **Emission Sources Treemap** yerine **Building Type Donut** koyduk.
> `certification` tablosu yok → **Certificate Count card** yerine **Active Building Count** (portfolio boyutu) koyuldu.

---

## 🎨 UNIVERSAL FORMATTING RULES (her sayfada)

Her card'a uygulanacak standart:

| Alan | Değer |
|------|-------|
| Title | **OFF** |
| Background | **Transparent 100%** |
| Border | **OFF** |
| Shadow | **OFF** |
| Callout value font | Segoe UI Semibold |
| Callout value size | 24-28pt |
| Callout value color | `#FFFFFF` (veya renk mesaja uysun: red=alert, green=good) |
| Category label color | `#7DB4DC` |
| **Display units** | **None** |
| **Thousand separator** | **On** |
| **Value decimals** | 0 (count) / 1 (oran, %) / 2 (para, EUI) |

Tüm chart'larda:
- Title **OFF** (arka plan görselinde başlık var)
- Gridlines: `#0E1E38`
- Axis color: `#4A6E96`
- Legend color: `#7DB4DC`

---

## 📋 UYGULAMA SIRASI (Power BI tarafında)

1. **Önce DAX:** yeni measure'ları modele ekle (sonraki step'te vereceğim)
2. **Sayfa 1:** Bug #2 format düzeltmeleri, YoY/Solar Coverage/Top Consumer card'ları ekle
3. **Sayfa 2:** Bug #1 (SoC %7450) düzelt, Bug #5 (Carbon label) düzelt, Solar vs Grid ayır
4. **Sayfa 3:** Bug #2 format, Bug #4 Resolution Time yerine Active Anomaly Rate
5. **Notebook gözden geçir:** Bug #3 CO2 emission factor
6. **Sayfa 4-6:** Yeni spec'lere göre başlat

---

**Review tarihi:** 2026-04-14
**Sonraki revizyon:** Sayfa 4-6 tamamlandıktan sonra end-to-end UX review + accessibility check (renk kontrastı, screen reader labels).
