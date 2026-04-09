# Energy Copilot Platform — Power BI Report Layout
## 6 Sayfa Rapor Tasarımı (Desktop'ta Oluştur)

---

## Genel İlkeler

- **Renk paleti:** Birincil mavi `#0F4C81`, Uyarı turuncu `#FF6B35`, Başarı yeşil `#2ECC71`, Kritik kırmızı `#E74C3C`, Nötr gri `#95A5A6`
- **Filtreler:** Tüm sayfalarda ortak slicer: `Date` (tarih aralığı) + `silver_building_master[building_type]` + `silver_building_master[country_code]`
- **Dil:** RLS açıkken müşteriler building_name görür (building_id değil)
- **Tooltip:** Her görsele ilgili measure'ın açıklaması tooltip olarak ekle

---

## Sayfa 1 — Portfolio Overview
**Amaç:** Yönetici özet — tüm binaların tek bakışta durumu

### Layout (3 satır):

**Satır 1 — KPI Kartları (5 adet, yan yana):**
```
[Total Consumption kWh] [Total Energy Cost EUR] [Active Anomalies] [Solar Coverage Pct] [Net Carbon Footprint tCO2]
```
Her kart altına `Consumption Change Pct` veya `Cost Change Pct` gibi trend oku ekle (yeşil ↓ veya kırmızı ↑).

**Satır 2 — Ana Görseller:**
- Sol (60% genişlik): **Clustered Bar Chart** — `silver_building_master[building_name]` eksen, `Total Consumption kWh` değer, `Avg EUI kWh m2` ikincil eksen (çizgi olarak). Binaları kıyaslayan ana görsel.
- Sağ (40% genişlik): **Donut Chart** — `silver_building_master[building_type]` legend, `Total Consumption kWh` değer. Bina tipi dağılımı.

**Satır 3 — Zaman Trendi + Harita:**
- Sol (55% genişlik): **Line Chart** — `Date[YearMonth]` eksen, `Total Consumption kWh` + `Total Solar Generated kWh` (2 çizgi). Aylık trend.
- Sağ (45% genişlik): **Map** — `silver_building_master[country_code]` lokasyon, `Total Consumption kWh` boyut (baloncuk haritası). Coğrafi dağılım.

**Slicerlar (sağ panel):** Tarih aralığı + Bina tipi + Ülke + Abonelik tier

---

## Sayfa 2 — Building Detail
**Amaç:** Tek bina derinlemesine analiz — operasyonel detay

### Filtre:
Sayfanın üstüne büyük bir `silver_building_master[building_name]` dropdown slicer ekle (tek seçim). Bu sayfadaki tüm görseller seçilen binaya göre filtreler.

### Layout (4 satır):

**Satır 1 — Bina KPI Kartları (6 adet):**
```
[Avg Daily Consumption kWh] [Peak Demand kW] [Avg EUI kWh m2] [Avg Solar PR Pct] [Avg Temperature C] [Battery Cycles Total]
```

**Satır 2 — Tüketim Detayı:**
- Sol (65%): **Line Chart** — `gold_kpi_daily[date]` eksen, `total_consumption_kwh` (mavi çizgi) + `avg_temperature_c` (turuncu çizgi, ikincil eksen). Sıcaklık-tüketim korelasyonu net görünür.
- Sağ (35%): **Gauge** — `Avg EUI kWh m2` değer, min=0, hedef=0.27 (iyi ofis benchmarkı), max=1.0. Yeşil/kırmızı otomatik.

**Satır 3 — Solar & Batarya:**
- Sol (50%): **Stacked Bar Chart** — `gold_kpi_daily[date]` eksen, `solar_self_consumed_kwh` + `solar_exported_kwh` yığılmış bar + `total_consumption_kwh` çizgi (ikincil eksen).
- Sağ (50%): **Area Chart** — `gold_kpi_daily[date]` eksen, `battery_soc_min_pct` alt alan, `battery_soc_max_pct` üst alan (aralık gösterimi). Batarya şarj aralığı.

**Satır 4 — HDD/CDD Analizi:**
- Sol (50%): **Scatter Chart** — X=`hdd_day`, Y=`total_consumption_kwh`, değerler=`gold_kpi_daily[date]`. Isıtma ihtiyacı ile tüketim ilişkisi.
- Sağ (50%): **Scatter Chart** — X=`cdd_day`, Y=`total_consumption_kwh`. Soğutma ihtiyacı ile tüketim ilişkisi.

---

## Sayfa 3 — Anomalies & Alerts
**Amaç:** Aktif sorunlar ve geçmiş anomali analizi

### Layout (3 satır):

**Satır 1 — Alert KPI Kartları (5 adet):**
```
[Active Anomalies]🔴  [Critical Anomalies]🔴  [High Anomalies]🟠  [Resolved Anomalies]✅  [Active Anomaly Rate Pct]
```
`Active Anomalies` ve `Critical Anomalies` kartlarına kırmızı arka plan kondisyonel format ekle (değer > 0 ise).

**Satır 2 — Ana Anomali Tablosu + Dağılım:**
- Sol (60%): **Table** — Kolonlar: `silver_building_master[building_name]`, `gold_anomalies[anomaly_type]`, `gold_anomalies[severity]`, `gold_anomalies[detected_date]`, `gold_anomalies[description_en]`, `gold_anomalies[metric_value]`, `gold_anomalies[is_resolved]`. Koşullu biçimlendirme: severity = "critical" → kırmızı satır.
- Sağ (40%): **Donut Chart** — `gold_anomalies[anomaly_type]` legend, `Total Anomalies` değer. Hangi tip anomali en çok.

**Satır 3 — Zaman Trendi + Severity Analizi:**
- Sol (50%): **Stacked Column Chart** — `Date[YearMonth]` eksen, `gold_anomalies[severity]` legend, `Total Anomalies` değer. Aylık anomali trendi severity kırılımlı.
- Sağ (50%): **100% Stacked Bar** — `silver_building_master[building_name]` eksen, `gold_anomalies[severity]` legend. Bina başına anomali severity dağılımı.

**Slicerlar:** Tarih + Severity (multi-select) + Anomali tipi + Is_resolved (Aktif/Çözüldü)

---

## Sayfa 4 — Forecast & Recommendations
**Amaç:** Gelecek tüketim tahmini + enerji verimliliği önerileri

### Layout (2 bölüm — üst Forecast / alt Recommendations):

**ÜST BÖLÜM — Forecast (sayfa yüksekliğinin %45'i):**

Forecast KPI satırı (3 kart):
```
[7 Day Forecast Total kWh]   [Avg Model MAPE Pct]   [Avg Trained On Days]
```

- Sol (60%): **Line Chart with Error Bars** — `gold_consumption_forecast[forecast_date]` eksen, `predicted_kwh` çizgi + `lower_bound_kwh` ve `upper_bound_kwh` ile oluşturulan gölgeli alan (güven aralığı). Renk: mavi çizgi + açık mavi alan.
  > Not: Power BI'da error bar görselini elde etmek için: `predicted_kwh` + `lower_bound_kwh` + `upper_bound_kwh` üç ölçüm olarak ekle, görsel tipi olarak Line Chart kullan.
- Sağ (40%): **Bar Chart** — `silver_building_master[building_name]` eksen, `Avg Model MAPE Pct` değer. Koşullu format: MAPE < 10 yeşil, 10-20 sarı, > 20 kırmızı.

**ALT BÖLÜM — Recommendations (sayfa yüksekliğinin %55'i):**

Öneri KPI satırı (4 kart):
```
[Total Annual Saving EUR]   [Total CO2 Saving tCO2]   [Total Net Capex EUR]   [Avg Payback Years]
```

- Sol (50%): **Table** — Kolonlar: `silver_building_master[building_name]`, `gold_recommendations[rank]`, `gold_recommendations[title_en]`, `gold_recommendations[priority_label]`, `annual_saving_eur`, `payback_years`, `grant_eur`. Sırala: rank ascending. Koşullu format: `priority_label` = "Critical" → kırmızı, "High" → turuncu.
- Sağ (50%): **Scatter Chart** — X=`payback_years`, Y=`annual_saving_eur`, Boyut=`capex_eur`, Renk=`gold_recommendations[action_type]`. "Hızlı kazanç" görsel analizi — sol üst köşe = en iyi yatırım.

---

## Sayfa 5 — Occupancy Analysis
**Amaç:** Bina kullanım profili + mesai dışı enerji israfı

### Layout (3 satır):

**Satır 1 — Occupancy KPI Kartları (4 adet):**
```
[Avg Business Hours Occupancy Pct]   [Avg After Hours Occupancy Pct]   [Calibrated Buildings Count]   [Avg Profile Confidence]
```
`Avg After Hours Occupancy Pct` kartına: değer > 20% ise sarı uyarı, > 40% ise kırmızı.

**Satır 2 — Haftalık Heatmap (ana görsel):**
- Tüm genişlik: **Matrix** — Satır=`gold_occupancy_profile[day_of_week]` (0=Pzt...6=Paz olarak yeniden etiketle), Sütun=`gold_occupancy_profile[hour_of_day]`, Değer=`AVERAGE(gold_occupancy_profile[occupancy_probability])`. Koşullu biçimlendirme: Düşük=beyaz, Orta=açık mavi, Yüksek=koyu mavi.
  > Bu, 7×24 saatlik doluluk ısı haritasını gösterir. Hangi saatlerde boş, hangisinde dolu.

**Satır 3 — Karşılaştırma:**
- Sol (50%): **Clustered Bar** — `silver_building_master[building_name]` eksen, `Avg Business Hours Occupancy Pct` + `Avg After Hours Occupancy Pct` (2 seri). Bina bazında karşılaştırma.
- Sağ (50%): **Line Chart** — `gold_occupancy_profile[hour_of_day]` eksen, `AVERAGE(gold_occupancy_profile[occupancy_probability])` değer, `silver_building_master[building_type]` legend. Bina tipine göre günlük doluluk eğrisi (ofis vs retail vs otel farkı görünür).

**Slicerlar:** Bina seçimi + Profil kaynağı (calibrated / base_only) + Gün tipi (hafta içi / hafta sonu)

---

## Sayfa 6 — Sustainability & Compliance
**Amaç:** ESG raporlama metrikleri + karbon ayak izi analizi

### Layout (3 satır):

**Satır 1 — Sürdürülebilirlik KPI Kartları (5 adet):**
```
[Total CO2 Emissions tCO2]   [Total CO2 Savings from Solar tCO2]   [Net Carbon Footprint tCO2]   [Carbon Reduction from Solar Pct]   [Avg Carbon Intensity kg m2]
```

**Satır 2 — Karbon Trend + Ülke Kırılımı:**
- Sol (55%): **Line Chart** — `Date[YearMonth]` eksen, `Total CO2 Emissions tCO2` (kırmızı çizgi) + `Total CO2 Savings from Solar tCO2` (yeşil çizgi) + `Net Carbon Footprint tCO2` (gri çizgi). 3 çizgili karbon trend.
- Sağ (45%): **Clustered Bar** — `silver_building_master[country_code]` eksen, `Total CO2 Emissions tCO2` + `Total CO2 Savings from Solar tCO2` (2 seri). Ülke bazında emisyon ve tasarruf karşılaştırması.

**Satır 3 — HDD/CDD İklim Analizi + Karbon Yoğunluğu:**
- Sol (50%): **Clustered Column** — `Date[MonthShort]` eksen, `Total HDD` + `Total CDD` (2 seri). Yıl boyunca iklim sertliği — ısıtma vs soğutma yükü dağılımı.
- Sağ (50%): **Treemap** — `silver_building_master[building_name]` grup, `Total CO2 Emissions tCO2` boyut. En fazla emisyon üreten binalar görsel olarak öne çıkar.

**Slicerlar:** Yıl + Ülke + Bina tipi

---

## Desktop'ta Live Connection Kurulumu

1. Power BI Desktop'ta: **Get Data → Power BI semantic models**
2. Fabric workspace'ini seç → `EnergycopilotModel`'i seç → **Connect**
3. **Live Connection** modunda açılır — tabloları göremezsin ama measure'ları kullanabilirsin
4. Yukarıdaki layout'a göre sayfaları oluştur
5. **Publish** → Fabric workspace'ini seç
6. Fabric'te raporu semantic model'e bağla

> Live Connection'da model değişikliği yapılamaz (yeni measure eklenemez).
> Yeni measure eklemek istersen Fabric'teki semantic model editörüne dön.
