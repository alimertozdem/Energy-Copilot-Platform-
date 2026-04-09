# Energy Copilot Platform — Semantic Model Setup Guide
## Microsoft Fabric / Power BI Direct Lake

---

## 1. Semantic Model Nasıl Oluşturulur (Fabric UI)

1. Fabric workspace'te sol menüden **New item** → **Semantic model** seç
2. İsim: `EnergycopilotModel`
3. **Lakehouse** seç: `EnergyCopilotLakehouse`
4. Aşağıdaki tablolar otomatik listelenecek — sadece gerekli olanları seç (bkz. Bölüm 2)
5. **Confirm** → model Direct Lake modunda açılır

---

## 2. Eklenecek Tablolar ve Kolonlar

### FACT TABLES (ölçüm verileri)

#### `gold_kpi_daily`
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| building_id | Text | FK → silver_building_master |
| date | Date | Tarih (ilişki anahtarı) |
| year | Integer | |
| month | Integer | |
| total_consumption_kwh | Decimal | Günlük toplam tüketim |
| peak_demand_kw | Decimal | Günlük pik güç |
| avg_load_factor | Decimal | Ortalama yük faktörü |
| solar_generated_kwh | Decimal | Solar üretim |
| solar_self_consumed_kwh | Decimal | Solar self-consumption |
| solar_exported_kwh | Decimal | Şebekeye verilen solar |
| avg_solar_pr | Decimal | Solar performans oranı |
| avg_self_sufficiency_rate | Decimal | Enerji öz-yeterliliği |
| battery_charged_kwh | Decimal | Batarya şarj |
| battery_discharged_kwh | Decimal | Batarya deşarj |
| battery_cycles_day | Decimal | Günlük döngü sayısı |
| battery_soc_min_pct | Decimal | Min şarj seviyesi |
| battery_soc_max_pct | Decimal | Max şarj seviyesi |
| avg_temperature_c | Decimal | Ortalama dış sıcaklık |
| hdd_day | Decimal | Isıtma derece-gün |
| cdd_day | Decimal | Soğutma derece-gün |
| net_grid_consumption_kwh | Decimal | Net şebeke tüketimi |
| co2_emissions_kg | Decimal | CO₂ emisyonu |
| co2_savings_from_solar_kg | Decimal | Solar'dan CO₂ tasarrufu |
| eui_kwh_m2 | Decimal | Enerji kullanım yoğunluğu |
| hdd_normalized_eui | Decimal | İklim normalize EUI |
| carbon_intensity_kg_m2 | Decimal | Karbon yoğunluğu |
| estimated_cost_eur | Decimal | Tahmini enerji maliyeti |
| estimated_savings_eur | Decimal | Solar'dan tahmini tasarruf |
| floor_area_m2 | Decimal | Alan (m²) |
| has_pv | Boolean | |
| has_battery | Boolean | |
| has_heat_pump | Boolean | |
| subscription_tier | Text | |

#### `gold_anomalies`
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| anomaly_id | Text | PK |
| building_id | Text | FK |
| anomaly_type | Text | SPIKE, AFTER_HOURS, SOLAR_UNDERPERFORM... |
| severity | Text | critical / high / medium / low |
| detected_date | Text | YYYY-MM-DD formatında ⚠️ |
| metric_value | Decimal | Ölçülen değer |
| threshold_value | Decimal | Eşik değer |
| description_en | Text | İngilizce açıklama |
| description_tr | Text | Türkçe açıklama |
| recommended_action_en | Text | |
| is_resolved | Boolean | Çözüldü mü |
| detected_at | DateTime | |

> ⚠️ **Önemli:** `detected_date` kolon tipi Text'tir. Model editöründe bu kolonu seç → **Data type: Date** olarak değiştir. Fabric ISO format (YYYY-MM-DD) olduğu için otomatik dönüştürür.

#### `gold_consumption_forecast`
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| building_id | Text | FK |
| forecast_date | Date | Tahmin tarihi |
| predicted_kwh | Decimal | Prophet tahmini |
| lower_bound_kwh | Decimal | %80 alt sınır |
| upper_bound_kwh | Decimal | %80 üst sınır |
| confidence_pct | Decimal | Güven aralığı |
| model_mape_pct | Decimal | Model hata oranı |
| trained_on_days | Integer | Eğitim gün sayısı |
| model_version | Text | |
| forecasted_at | DateTime | |

#### `gold_recommendations`
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| building_id | Text | FK |
| building_name | Text | |
| rank | Integer | Öncelik sırası (1=en önemli) |
| action_type | Text | INSTALL_HEAT_PUMP, ADD_SOLAR... |
| priority_label | Text | Critical / High / Medium / Low |
| priority_score | Decimal | 0-100 |
| compliance_driver | Text | |
| annual_saving_eur | Decimal | Yıllık tasarruf (€) |
| co2_saving_kg | Decimal | Yıllık CO₂ azalması |
| capex_eur | Decimal | Yatırım maliyeti |
| net_capex_eur | Decimal | Sübvansiyon sonrası maliyet |
| grant_eur | Decimal | Hibe/teşvik tutarı |
| payback_years | Decimal | Geri ödeme süresi |
| npv_eur | Decimal | Net bugünkü değer |
| title_en | Text | |
| description_en | Text | |
| assessed_at | DateTime | |

#### `gold_occupancy_profile`
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| building_id | Text | FK |
| day_of_week | Integer | 0=Pzt … 6=Paz |
| hour_of_day | Integer | 0-23 |
| occupancy_probability | Decimal | 0.0–1.0 |
| profile_source | Text | calibrated / base_only |
| calibration_weeks | Integer | |
| confidence_score | Decimal | 0.0–1.0 |

### DIMENSION TABLE

#### `silver_building_master`
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| building_id | Text | PK |
| building_name | Text | Görünen bina adı |
| building_type | Text | office / retail / hotel... |
| country_code | Text | DE / TR / AT... |
| conditioned_area_m2 | Decimal | |
| subscription_tier | Text | basic / premium / enterprise |
| has_pv | Boolean | |
| has_battery | Boolean | |
| has_heat_pump | Boolean | |
| pv_capacity_kwp | Decimal | |
| battery_capacity_kwh | Decimal | |
| heat_pump_cop_rated | Decimal | |

### CALCULATED TABLE (DAX ile oluştur)

#### `Date` — Zaman Boyutu
Model editöründe **New table** → aşağıdaki DAX'ı yapıştır:

```dax
Date =
VAR _start = DATE(2024, 1, 1)
VAR _end   = DATE(2027, 12, 31)
RETURN
ADDCOLUMNS(
    CALENDAR(_start, _end),
    "Year",        YEAR([Date]),
    "Month",       MONTH([Date]),
    "MonthName",   FORMAT([Date], "MMMM"),
    "MonthShort",  FORMAT([Date], "MMM"),
    "Quarter",     "Q" & QUARTER([Date]),
    "WeekNumber",  WEEKNUM([Date], 2),
    "DayOfWeek",   WEEKDAY([Date], 2),
    "DayName",     FORMAT([Date], "dddd"),
    "IsWeekend",   IF(WEEKDAY([Date], 2) >= 6, TRUE, FALSE),
    "YearMonth",   FORMAT([Date], "YYYY-MM"),
    "YearQuarter", YEAR([Date]) & " Q" & QUARTER([Date])
)
```

---

## 3. İlişkiler (Relationships)

Model editöründe **Manage relationships** → şu ilişkileri kur:

| From (Many) | To (One) | Kolon | Tür | Yön |
|-------------|----------|-------|-----|-----|
| gold_kpi_daily[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |
| gold_kpi_daily[date] | Date[Date] | date | Many→One | Single |
| gold_anomalies[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |
| gold_anomalies[detected_date] | Date[Date] | date | Many→One | Single |
| gold_consumption_forecast[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |
| gold_consumption_forecast[forecast_date] | Date[Date] | date | Many→One | Single |
| gold_recommendations[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |
| gold_occupancy_profile[building_id] | silver_building_master[building_id] | building_id | Many→One | Single |

> **Not:** Date tablosu ile gold_anomalies arasında ilişki kurarken detected_date kolonunun tipini önce Date'e çevirdiğinden emin ol (Bölüm 2'deki uyarı).

---

## 4. Kolon Gizleme (İsteğe Bağlı ama Önerilir)

Raporda görünmesine gerek olmayan teknik kolonları gizle:
- Tüm tablolardaki `_id` kolonları (building_id hariç — filtre için gerekli)
- `processed_at`, `detected_at`, `forecasted_at`, `assessed_at`, `computed_at`
- `model_version`, `profile_source`, `calibration_weeks`
- `floor_area_m2` (gold_kpi_daily'deki — silver_building_master'dakini kullan)

Gizlemek için: kolona sağ tıkla → **Hide in report view**

---

## 5. Sonraki Adım

Model kaydedildikten sonra:
1. `02_dax_measures.dax` dosyasındaki measure'ları ekle
2. `03_rls_definition.md` ile RLS rollerini tanımla
3. Power BI Desktop'ta bu modele **Live Connection** kur → rapor tasarımına geç
