# EnergyLens — Final Rapor Kurulum Rehberi
## Power BI Desktop — Sayfa Sayfa Adım Adım
**Versiyon:** v2.0 — Düzeltilmiş  
**Tarih:** 2026-04-15  
**Hazırlayan:** Energy Copilot Platform

---

## ⚠️ KURULUMDAN ÖNCE — KRİTİK KONTROLLER

Raporu açmadan önce şu 4 adımı tamamla:

### Kontrol 1 — Date Tablosunu İşaretle
1. Model görünümünde `Date` tablosuna **sağ tıkla**
2. **"Mark as date table"** → `Date` kolonunu seç → **OK**
3. Tablonun yanında 📅 takvim ikonu görünmeli

### Kontrol 2 — Kolon Tiplerini Doğrula
| Tablo | Kolon | Doğru Tip |
|-------|-------|-----------|
| `gold_anomaly_log` | `detected_date` | Date |
| `gold_consumption_forecast` | `forecast_date` | Date |
| `gold_kpi_daily` | `date` | Date |
| `gold_occupancy_profile` | `day_of_week` | Whole Number |
| `gold_occupancy_profile` | `hour_of_day` | Whole Number |

### Kontrol 3 — % Format Kuralı (EN ÖNEMLİ)
> Tüm yüzde ölçüleri (Pct ile bitenler) DAX içinde zaten × 100 çarpılmıştır.
> 
> Kartlarda ve grafiklerde **"0.0"** formatı kullan.  
> **"0%"** formatını HİÇBİR ZAMAN kullanma — değeri tekrar × 100 çarpar.
>
> ❌ YANLIŞ: `%2587` → format olarak `0%` kullanılmış  
> ✅ DOĞRU: `25.9` → format olarak `0.0` kullanılmış

### Kontrol 4 — X Ekseni Sıralama (Aylık Grafikler)
Her aylık/tarih grafiğinde X eksenini şu şekilde sırala:
1. X eksen alanına tıkla
2. Sütun araçlarında **"Sort by column"** → `Date[Date]` veya `Date[MonthIndex]` seç
3. Artık tarihler kronolojik sırada görünür

---

## 📋 SAYFA 1 — Portföy Genel Bakış
**Başlık:** `Portföy Genel Bakış`  
**Alt başlık:** `Bina Portföyü Zekası`

### Slicer Paneli (sol — TEK kolon, 4 slicer)
| Slicer | Alan | Türü |
|--------|------|------|
| Tarih Aralığı | `Date[Date]` | Tarih aralığı |
| Bina Adı | `silver_building_master[building_name]` | Dropdown |
| Şehir | `silver_building_master[city]` | Dropdown |
| Bina Tipi | `silver_building_master[building_type]` | Dropdown |
| Ülke | `silver_building_master[country_code]` | Dropdown |

> ⚠️ Her sayfada YALNIZCA bu 4-5 slicer olmalı. Aynı alan için birden fazla slicer ekleme.

### KPI Kartları (5 adet — üst satır)

| Kart Başlığı | Ölçü | Format | Renk |
|---|---|---|---|
| `Toplam Enerji Tüketimi (kWh)` | `[Total Consumption kWh]` | `#,##0.0` | Mavi |
| `Ort. EUI (kWh/m²/gün)` | `[Avg EUI kWh m2]` | `0.000` | Mavi |
| `Aktif Anomali Sayısı` | `[Active Anomaly Count]` | `#,##0` | 🔴 Kırmızı çerçeve |
| `Toplam Enerji Maliyeti (€)` | `[Total Energy Cost EUR]` | `€#,##0.0` | Yeşil |
| `Net CO₂ Emisyonu (ton)` | `[Net Carbon Footprint tCO2]` | `#,##0.0` | Yeşil |

> ⚠️ **DÜZELTME — Sayfa 1 CO₂ Kartı:**  
> Mevcut raporda `Total CO2 Tons` kartı Energy kWh değerini gösteriyor.  
> Kartın ölçü bağlantısını `[Net Carbon Footprint tCO2]` olarak değiştir.  
> Doğru değer: ~928-1150 ton (milyonlar değil).

### Grafikler — Orta Satır

**Sol — Bina Bazlı Tüketim (Kümelenmiş Çubuk)**
- Başlık: `Bina Bazlı Enerji Tüketimi (kWh)`
- Y ekseni: `[Total Consumption kWh]` — Format: `#,##0.0`
- X ekseni: `silver_building_master[building_name]`
- İkincil eksen (çizgi): `[Avg EUI kWh m2]`
- Çubukları büyükten küçüğe sırala

**Sağ — Anomali Ciddiyet Dağılımı (Halka Grafik)**
- Başlık: `Anomali Ciddiyet Dağılımı`
- Legend: `gold_anomaly_log[severity]`
- Değer: `[Total Anomaly Count]`
- Renk kodları:
  - `critical` → `#E74C3C` (kırmızı)
  - `high` → `#FF6B35` (turuncu)
  - `medium` → `#F39C12` (sarı)

> ⚠️ **DÜZELTME:** Mevcut raporda critical=mor, high=yeşil, medium=cyan görünüyor. Renkleri yukarıdaki gibi düzelt.

### Grafikler — Alt Satır

**Sol — Aylık Enerji Trendi (Çizgi Grafik)**
- Başlık: `Aylık Enerji Tüketim Trendi (kWh)`
- X ekseni: `Date[YearMonth]` — **"Sort by" → `Date[MonthIndex]`** (kronolojik sıra için)
- Y ekseni: `[Total Consumption kWh]`
- İkinci çizgi: `[Total Solar Generated kWh]`

**Sağ — EUI Bina Karşılaştırması (Çubuk)**
- Başlık: `Bina EUI Performans Karşılaştırması`
- X ekseni: `silver_building_master[building_name]`
- Y ekseni: `[Avg EUI kWh m2]` — Format: `0.000`
- Koşullu renk: ≤0.27 yeşil, 0.27-0.41 sarı, >0.41 kırmızı

---

## 📋 SAYFA 2 — Bina Detay Analizi
**Başlık:** `Bina Detay Analizi`  
**Alt başlık:** `Derinlemesine Operasyonel Analiz`

### Slicer Paneli (sol — TEK kolon)

> ⚠️ **DÜZELTME:** Mevcut raporda 3 adet "Building Name" slicer var.  
> Hepsini sil. YALNIZCA 1 adet `building_name` slicer bırak.

| Slicer | Alan | Türü |
|--------|------|------|
| Tarih Aralığı | `Date[Date]` | Tarih aralığı |
| Bina Adı | `silver_building_master[building_name]` | Dropdown (tek seçim) |

### KPI Kartları (6 adet — üst satır)

| Kart Başlığı | Ölçü | Format | Not |
|---|---|---|---|
| `Günlük Ort. Tüketim (kWh)` | `[Avg Daily Consumption kWh]` | `#,##0.0` | |
| `Pik Güç Talebi (kW)` | `[Peak Demand kW]` | `#,##0.0` | |
| `EUI (kWh/m²/gün)` | `[Avg EUI kWh m2]` | `0.000` | |
| `Güneş Üretimi (kWh)` | `[Total Solar Generated kWh]` | `#,##0.0` | ☀️ |
| `Batarya Doluluk SoC (%)` | `[Avg Battery SoC Pct]` | `0.0` | ⚠️ Format: "0.0" NOT "0%" |
| `Karbon Yoğunluğu (gCO₂/kWh)` | `[Avg Carbon Intensity kg m2]` | `0.000` | |

> ⚠️ **DÜZELTME — Güneş Üretimi:**  
> Kart "862,457 kWh" gösteriyor (toplam yıllık) ama "Günlük Tüketim" 2,691 kWh gösteriyor.  
> Karşılaştırma tutarsız. Çözüm: Her iki kartı da `SUM` değeri olarak göster ve başlığa "Toplam (Dönem)" yaz.

### Grafikler — Üst Satır

**Sol — Tüketim & Sıcaklık (Çizgi)**
- Başlık: `Tüketim ve Dış Sıcaklık Korelasyonu`
- X ekseni: `Date[YearMonth]` → **"Sort by" → `Date[MonthIndex]`**
- Sol Y: `[Total Consumption kWh]` (mavi çizgi)
- Sağ Y (ikincil): `[Avg Temperature C]` (turuncu kesikli çizgi)

**Sağ — EUI Göstergesi (Gauge)**
- Başlık: `EUI Performans Göstergesi (kWh/m²/gün)`
- Değer: `[Avg EUI kWh m2]`
- Min: `0`
- Hedef: `0.27` (iyi ofis benchmark)
- Max: `0.70`
- Renk: ≤0.27 yeşil → >0.55 kırmızı

### Grafikler — Orta Satır

**Sol — Güneş vs Tüketim (Yığılmış Çubuk)**
- Başlık: `Güneş Enerjisi ve Tüketim Kırılımı (kWh)`
- X ekseni: `Date[YearMonth]` → **"Sort by" → `Date[MonthIndex]`**
- Çubuk 1: `SUM(gold_kpi_daily[solar_self_consumed_kwh])` — sarı
- Çubuk 2: `SUM(gold_kpi_daily[solar_exported_kwh])` — turuncu
- Çizgi (ikincil): `[Total Grid Consumption kWh]` — gri

**Sağ — Batarya SoC Trendi (Alan Grafik)**
- Başlık: `Batarya Doluluk Oranı Trendi (%)`
- X ekseni: `gold_kpi_daily[date]`
- Alt alan: `SUM(gold_kpi_daily[battery_soc_min_pct])` — açık mavi
- Üst alan: `SUM(gold_kpi_daily[battery_soc_max_pct])` — koyu mavi
- Y ekseni format: `0.0` — **ASLA "0%" kullanma**

> ⚠️ **DÜZELTME — Batarya SoC "0.0K" görünümü:**  
> Y ekseni "Thousands" formatında görünüyor. Ekseni düzenle:  
> Format → "0.0" seç, "Display units" → "None" yap.

### Grafikler — Alt Satır (Saçılım)

**Sol — Isıtma Derecesi & Tüketim İlişkisi (Scatter)**
- Başlık: `Isıtma Derecesi (HDD) — Tüketim Korelasyonu`
- X ekseni: `SUM(gold_kpi_daily[hdd_day])` — Format: `0.0`
- Y ekseni: `[Total Consumption kWh]`
- Detaylar: `gold_kpi_daily[date]`

**Sağ — Soğutma Derecesi & Tüketim İlişkisi (Scatter)**
- Başlık: `Soğutma Derecesi (CDD) — Tüketim Korelasyonu`
- X ekseni: `SUM(gold_kpi_daily[cdd_day])` — Format: `0.0`
- Y ekseni: `[Total Consumption kWh]`

---

## 📋 SAYFA 3 — Anomali Takip & Uyarılar
**Başlık:** `Anomali Takip & Uyarılar`  
**Alt başlık:** `Arıza Tespiti ve Müdahale`

### Slicer Paneli

| Slicer | Alan | Türü |
|--------|------|------|
| Tarih Aralığı | `Date[Date]` | Tarih aralığı |
| Bina Adı | `silver_building_master[building_name]` | Dropdown |
| Ciddiyet | `gold_anomaly_log[severity]` | Çoklu seçim |
| Anomali Türü | `gold_anomaly_log[anomaly_type]` | Dropdown |
| Durum | `gold_anomaly_log[is_resolved]` | Açılır (Aktif / Çözüldü) |

### KPI Kartları (5 adet — üst satır)

| Kart Başlığı | Ölçü | Format | Renk |
|---|---|---|---|
| `Toplam Anomali` | `[Total Anomaly Count]` | `#,##0` | Turuncu |
| `Kritik Anomali` | `[Critical Anomaly Count]` | `#,##0` | 🔴 Kırmızı |
| `Yüksek Öncelikli Anomali` | `[High Anomaly Count]` | `#,##0` | Turuncu |
| `Çözülmemiş Anomali` | `[Unresolved Count]` | `#,##0` | Sarı |
| `Aktif Anomali Oranı (%)` | `[Active Anomaly Rate Pct]` | `0.0` | Gri |

> ⚠️ **DÜZELTME — "Avg Resolution Time" kartı:**  
> Mevcut raporda bu kart "1/1/2024 12:0" gösteriyor (yanlış alan).  
> Kart başlığını `Ort. Çözüm Süresi (saat)` yap ve  
> ölçüyü `[Avg Resolution Hours]` bağla → "—" gösterir (placeholder).  
> resolved_at kolonu eklenince otomatik çalışır.

### Orta Alan

**Sol — Bina Anomali Tablosu (Tablo)**
- Başlık: `Aktif Anomali Listesi`
- Sütunlar (bu sırayla):
  1. `silver_building_master[building_name]` → **Başlık: "Bina"**
  2. `gold_anomaly_log[severity]` → **Başlık: "Ciddiyet"**
  3. `gold_anomaly_log[anomaly_type]` → **Başlık: "Anomali Türü"**
  4. `gold_anomaly_log[detected_date]` → **Başlık: "Tespit Tarihi"**
  5. `gold_anomaly_log[metric_value]` → **Başlık: "Ölçüm Değeri"**
  6. `gold_anomaly_log[is_resolved]` → **Başlık: "Çözüldü mü?"**
- Koşullu biçimlendirme: `severity = "critical"` → satır arka planı `#E74C3C`
- Sırala: `detected_date` azalan

> ⚠️ **DÜZELTME:** Tablonun başlık satırında "building_name" ham kolon adı görünüyor.  
> Yukarıdaki Türkçe başlıkları elle gir (Rename column).

**Sağ — Anomali Türü Dağılımı (Halka)**
- Başlık: `Anomali Türü Dağılımı`
- Legend: `gold_anomaly_log[anomaly_type]`
- Değer: `[Total Anomaly Count]`

### Alt Satır

**Sol — Aylık Anomali Trendi (Yığılmış Sütun)**
- Başlık: `Aylık Anomali Trendi — Ciddiyet Kırılımlı`
- X ekseni: `Date[YearMonth]` → **"Sort by" → `Date[MonthIndex]`**
- Y ekseni: `[Total Anomaly Count]`
- Legend: `gold_anomaly_log[severity]`
- Ciddiyet renkleri: critical=kırmızı, high=turuncu, medium=sarı

**Sağ — Bina Bazlı Anomali Dağılımı (100% Yığılmış Çubuk)**
- Başlık: `Bina Bazlı Anomali Dağılımı`
- X ekseni: `silver_building_master[building_name]`
- Y ekseni: `[Active Anomaly Rate Pct]` — Format: `0.0` (NOT "0%")
- Legend: `gold_anomaly_log[severity]`

---

## 📋 SAYFA 4 — Tahmin & Verimlilik Önerileri
**Başlık:** `Tahmin & Verimlilik Önerileri`  
**Alt başlık:** `Öngörüsel Enerji Zekası`

### Slicer Paneli

| Slicer | Alan | Türü |
|--------|------|------|
| Tarih Aralığı | `Date[Date]` | Tarih aralığı |
| Bina Adı | `silver_building_master[building_name]` | Dropdown |
| Eylem Türü | `gold_recommendations[action_type]` | Çoklu seçim |

> ⚠️ **DÜZELTME:** Mevcut raporda 2 adet "Select or drag fields" boş slicer var.  
> Bunları sil. Yerine yukarıdaki 3 slicer'ı ekle.

### Tahmin KPI Kartları (3 adet)

| Kart Başlığı | Ölçü | Format | Not |
|---|---|---|---|
| `7 Günlük Tüketim Tahmini (kWh)` | `[Forecast 7Day kWh]` | `#,##0.0` | |
| `30 Günlük Tüketim Tahmini (kWh)` | `[Forecast 30Day kWh]` | `#,##0.0` | ⚠️ Bkz. not |
| `Yenilenebilir Tasarruf Potansiyeli (€)` | `[Total Savings Potential EUR]` | `€#,##0.0` | |

> ⚠️ **DÜZELTME — 30-Gün Tahmin BLANK:**  
> Önceki DAX TODAY() kullanıyordu ama veri 2024'e ait.  
> Yeni `[Forecast 30Day kWh]` ölçüsü son tahmin tarihinden hesaplar.  
> Semantic model'i yeniden yükleyince değer gelir.

### Tahmin Grafikler

**Sol — Tüketim Tahmin Çizgisi (Çizgi Grafik)**
- Başlık: `Tüketim Tahmini — Güven Aralığıyla`
- X ekseni: `gold_consumption_forecast[forecast_date]`
- Değerler (3 çizgi):
  1. `predicted_kwh` — Mavi kalın çizgi — "Tahmin"
  2. `lower_bound_kwh` — Açık mavi kesikli — "Alt Sınır"
  3. `upper_bound_kwh` — Açık mavi kesikli — "Üst Sınır"
- Format: `#,##0.0`

> ⚠️ **DÜZELTME:** Mevcut raporda bu alan "Select or drag fields" gösteriyor.  
> Yukarıdaki 3 alanı `gold_consumption_forecast` tablosundan ekle.

**Sağ — Model Doğruluk Skoru (Çubuk)**
- Başlık: `Model Doğruluk Skoru — Bina Bazlı MAPE (%)`
- X ekseni: `silver_building_master[building_name]`
- Y ekseni: `[Avg Model MAPE Pct]`
- Y ekseni format: `0.0` — **ASLA "0%" kullanma** (500% hatası olur)
- Koşullu renk: <10 yeşil, 10-20 sarı, >20 kırmızı
- Kart alt yazısı: `[MAPE Bucket]`

### Öneri KPI Kartları (4 adet)

| Kart Başlığı | Ölçü | Format |
|---|---|---|
| `Toplam Öneri Sayısı` | `[Total Recommendation Count]` | `#,##0` |
| `Kritik Öneri` | `[Critical Recommendation Count]` | `#,##0` |
| `Beklenen Yıllık Tasarruf (€)` | `[Expected Annual Savings EUR]` | `€#,##0.0` |
| `Toplam Yatırım Maliyeti (€)` | `[Total Net Investment EUR]` | `€#,##0.0` |

> ⚠️ **DÜZELTME — Kritik Öneri "--":**  
> Mevcut veri MEDIUM/LOW öneri içeriyor, CRITICAL yok.  
> Yeni DAX `0` döndürür (BLANK yerine). Kart "0" göstermeli.

### Öneri Grafikler

**Sol — Verimlilik Önerileri Tablosu (Tablo)**
- Başlık: `Bina Verimlilik Önerileri`
- Sütunlar:
  1. `silver_building_master[building_name]` → "Bina"
  2. `gold_recommendations[action_type]` → "Eylem Türü"
  3. `gold_recommendations[priority_label]` → "Öncelik"
  4. `gold_recommendations[annual_saving_eur]` → "Yıllık Tasarruf (€)" → Format: `€#,##0.0`
  5. `gold_recommendations[payback_years]` → "Geri Ödeme (yıl)" → Format: `0.0`
  6. `gold_recommendations[capex_eur]` → "Yatırım Maliyeti (€)" → Format: `€#,##0.0`
- Sırala: `priority_score` azalan

**Sağ — Geri Ödeme & Tasarruf Analizi (Scatter)**
- Başlık: `Geri Ödeme Süresi & Yıllık Tasarruf (ROI Analizi)`
- X ekseni: `gold_recommendations[payback_years]` → "Geri Ödeme (yıl)"
- Y ekseni: `gold_recommendations[annual_saving_eur]` → "Yıllık Tasarruf (€)"
- Boyut: `gold_recommendations[capex_eur]`
- Renk: `gold_recommendations[action_type]`
- Sol üst köşe = en iyi yatırım

---

## 📋 SAYFA 5 — Doluluk & Enerji Verimliliği
**Başlık:** `Doluluk & Enerji Verimliliği`  
**Alt başlık:** `Mekan-Enerji Korelasyonu`

### Slicer Paneli

> ⚠️ **DÜZELTME:** Mevcut raporda 3 adet "Building Name" ve 1 "Select or drag fields" var.  
> Hepsini sil. Aşağıdaki 3 slicer'ı ekle.

| Slicer | Alan | Türü |
|--------|------|------|
| Tarih Aralığı | `Date[Date]` | Tarih aralığı |
| Bina Adı | `silver_building_master[building_name]` | Dropdown |
| Profil Kaynağı | `gold_occupancy_profile[profile_source]` | Açılır (calibrated/base_only) |

### KPI Kartları (4 adet)

| Kart Başlığı | Ölçü | Format | Not |
|---|---|---|---|
| `Mesai Saati Doluluk Oranı (%)` | `[Avg Business Hours Occupancy Pct]` | `0.0` | ⚠️ ASLA "0%" |
| `Mesai Dışı Doluluk Oranı (%)` | `[Avg After Hours Occupancy Pct]` | `0.0` | ⚠️ ASLA "0%" |
| `Pik Doluluk Saati` | `[Peak Occupancy Hour]` | `0` (saat) | |
| `Hayalet Yük Riski (%)` | `[Phantom Load Risk Pct]` | `0.0` | ⚠️ ASLA "0%" |

> ⚠️ **DÜZELTME — Tüm % Kartları:**  
> "Avg Occupancy (%)" kartı %2587, "Vacancy Rate" %4350 gösteriyor.  
> Nedeni: Kart format string olarak "0%" kullanılmış → çift çarpım.  
> Çözüm: Her kartın format string'ini **"0.0"** olarak değiştir.

### Heatmap (Tam Genişlik)

**Ana Görsel — Haftalık Doluluk Isı Haritası (Matris)**
- Başlık: `Haftalık & Saatlik Doluluk Profili`
- Satır: `gold_occupancy_profile[day_of_week]`  
  → Değer eşlemesi: 0=Pazartesi, 1=Salı, 2=Çarşamba, 3=Perşembe, 4=Cuma, 5=Cumartesi, 6=Pazar
- Sütun: `gold_occupancy_profile[hour_of_day]`
- Değer: `AVERAGE(gold_occupancy_profile[occupancy_probability])`
- Koşullu biçimlendirme: Düşük=beyaz → Yüksek=koyu mavi

### Alt Satır Grafikler

**Sol — Bina Bazlı Doluluk Karşılaştırması (Kümelenmiş Çubuk)**
- Başlık: `Bina Bazlı Doluluk Karşılaştırması (%)`
- X ekseni: `silver_building_master[building_name]`
- Çubuk 1: `[Avg Business Hours Occupancy Pct]` → "Mesai Saati" — mavi
- Çubuk 2: `[Avg After Hours Occupancy Pct]` → "Mesai Dışı" — turuncu
- Y ekseni format: `0.0` (ASLA "0%")

**Sağ — Saatlik Doluluk Profili (Çizgi)**
- Başlık: `Gün İçi Doluluk Eğrisi — Bina Türü Karşılaştırması`
- X ekseni: `gold_occupancy_profile[hour_of_day]` → 0-23 saat
- Y ekseni: `AVERAGE(gold_occupancy_profile[occupancy_probability])` → Format: `0.00`
- Legend: `silver_building_master[building_type]`

> ⚠️ **DÜZELTME — Gün Bazlı Tablo:**  
> Mevcut tabloda tüm günler aynı değeri (25.87) gösteriyor.  
> Bu görsel faydasız — kaldır. Yerine saatlik profil çizgisini ekle.

---

## 📋 SAYFA 6 — Sürdürülebilirlik & ESG Raporlaması
**Başlık:** `Sürdürülebilirlik & ESG Raporlaması`  
**Alt başlık:** `Karbon Yönetimi & Uyumluluk`

### Slicer Paneli

| Slicer | Alan | Türü |
|--------|------|------|
| Tarih Aralığı | `Date[Date]` | Tarih aralığı |
| Bina Adı | `silver_building_master[building_name]` | Dropdown |
| Ülke | `silver_building_master[country_code]` | Dropdown |

### KPI Kartları (5 adet)

| Kart Başlığı | Ölçü | Format | Not |
|---|---|---|---|
| `CO₂ Emisyonu (ton)` | `[Total CO2 Emissions tCO2]` | `#,##0.0` | |
| `Güneş CO₂ Tasarrufu (ton)` | `[CO2 Savings Tons]` | `#,##0.0` | |
| `Net Karbon Ayak İzi (ton)` | `[Net Carbon Footprint tCO2]` | `#,##0.0` | |
| `Yenilenebilir Enerji Oranı (%)` | `[Renewable Energy Rate Pct]` | `0.0` | ⚠️ ASLA "0%" |
| `Enerji Yoğunluğu (kWh/m²/gün)` | `[Avg EUI kWh m2]` | `0.000` | |

> ⚠️ **DÜZELTME — "Select or drag fields" kartı:**  
> 3. kart konumunda boş visual var. Bunu `[Net Carbon Footprint tCO2]` ile doldur.
>
> ⚠️ **DÜZELTME — Yenilenebilir Oran %2016:**  
> Yeni `[Renewable Energy Rate Pct]` ölçüsü doğru hesap yapar.  
> Kart formatı **"0.0"** olmalı — "0%" kullanma.

### Grafikler — Üst Satır

**Sol — Aylık CO₂ Trendi (3 Çizgi)**
- Başlık: `Aylık CO₂ Emisyon Trendi`
- X ekseni: `Date[YearMonth]` → **"Sort by" → `Date[MonthIndex]`**
- Çizgi 1: `[Total CO2 Emissions tCO2]` — kırmızı "Brüt Emisyon"
- Çizgi 2: `[CO2 Savings Tons]` — yeşil "Güneş Tasarrufu"
- Çizgi 3: `[Net Carbon Footprint tCO2]` — gri "Net Ayak İzi"
- Y format: `0.0`

**Sağ — Ülke Bazlı Emisyon Karşılaştırması (Kümelenmiş Çubuk)**
- Başlık: `Ülke Bazlı Emisyon & Tasarruf Karşılaştırması`
- X ekseni: `silver_building_master[country_code]`
- Çubuk 1: `[Total CO2 Emissions tCO2]` — kırmızı
- Çubuk 2: `[CO2 Savings Tons]` — yeşil
- Y format: `0.0`

### Grafikler — Alt Satır

**Sol — İklim Yükü Analizi (Kümelenmiş Sütun)**
- Başlık: `Aylık Isıtma & Soğutma Yükü Analizi (HDD/CDD)`
- X ekseni: `Date[MonthShort]` → **"Sort by" → `Date[MonthIndex]`**
- Çubuk 1: `[Total HDD]` — mavi "Isıtma Yükü"
- Çubuk 2: `[Total CDD]` — turuncu "Soğutma Yükü"
- İkincil eksen (çizgi): `[Avg HDD Normalized EUI]` — yeşil

**Sağ — Emisyon Kaynakları (Treemap/Ağaç Haritası)**
- Başlık: `Bina Bazlı CO₂ Emisyon Dağılımı`
- Grup: `silver_building_master[building_name]`
- Boyut: `[Total CO2 Emissions tCO2]`
- Açıklama: `[Avg EUI kWh m2]`
- Renk: koşullu — yüksek emisyon = kırmızı

> ⚠️ **DÜZELTME — "Emission Sources" büyük cyan kutuc:**  
> Mevcut visual bir treemap değil, düz alan chart.  
> Visual tipini **Treemap** olarak değiştir ve yukarıdaki alanları ekle.

---

## 🔧 GENEL DÜZELTMELER (Tüm Sayfalar)

### X Eksen Tarih Sıralaması
Tüm aylık grafiklerde X eksenini kronolojik sıraya al:
1. Grafik → X eksen alanına tıkla
2. Model → `Date` tablosuna bir `MonthIndex` kolonu ekle (örn: `YYYYMM` formatında tam sayı)
3. `YearMonth` kolonunu `MonthIndex`'e göre sırala → **"Sort by column" → `MonthIndex`**

```dax
// Date tablosuna ekle — MonthIndex hesaplanmış kolon
MonthIndex = YEAR('Date'[Date]) * 100 + MONTH('Date'[Date])
// Örn: 2024-01 → 202401, 2024-12 → 202412
```

### Anomali Ciddiyet Renkleri
Tüm sayfalarda şu renk kodlarını kullan:
| Ciddiyet | Hex Renk |
|----------|----------|
| critical | `#E74C3C` |
| high | `#FF6B35` |
| medium | `#F39C12` |
| low | `#95A5A6` |

---

## ✅ KONTROL LİSTESİ — Yayınlamadan Önce

### Sayfa 1
- [ ] CO₂ kartı `[Net Carbon Footprint tCO2]` ölçüsüne bağlı mı? (~928 ton gösteriyor mu?)
- [ ] Anomali halka grafiği renkleri doğru mu? (critical=kırmızı)
- [ ] Aylık trend X ekseni kronolojik sırada mı?

### Sayfa 2
- [ ] Yalnızca 1 adet "Building Name" slicer var mı?
- [ ] Batarya SoC ekseni "0%" değil "0.0" formatında mı?
- [ ] Solar vs Grid grafik X ekseni kronolojik mı?

### Sayfa 3
- [ ] "Avg Resolution Time" kartı yerine `[Avg Resolution Hours]` bağlı mı?
- [ ] Bina tablosu başlıkları Türkçe mi? ("building_name" yok)
- [ ] Anomali türü renkleri doğru mu?
- [ ] Aylık anomali X ekseni kronolojik mı?

### Sayfa 4
- [ ] Forecast ana görsel doldurulmuş mu? (3 çizgi var mı?)
- [ ] `[Forecast 30Day kWh]` değer gösteriyor mu? (BLANK değil)
- [ ] MAPE grafiği Y ekseni "0.0" formatında mı? ("0%" değil)
- [ ] Action Type slicer dolu mu? (boş değil)
- [ ] `[Critical Recommendation Count]` "0" gösteriyor mu? ("--" değil)

### Sayfa 5
- [ ] Yalnızca 1 adet Building Name slicer var mı?
- [ ] Tüm % kartları "0.0" formatında mı? (2587% yok)
- [ ] Gün tablosu (tüm günler aynı değer) kaldırıldı mı?
- [ ] Haftalık heatmap matris doğru çalışıyor mu?

### Sayfa 6
- [ ] "Select or drag fields" boş kartı `[Net Carbon Footprint tCO2]` ile dolduruldu mu?
- [ ] Yenilenebilir Oran "0.0" formatında mı? (2016% yok)
- [ ] Emission Sources treemap olarak değiştirildi mi?
- [ ] Aylık CO₂ X ekseni kronolojik mı?

---

## 📊 BEKLENEN DEĞERLER (Doğrulama Referansı)

Raporu açtığında "All Buildings / 2024" filtresiyle şu değerleri görmelisin:

| Ölçü | Beklenen Değer | Not |
|------|----------------|-----|
| Total Consumption kWh | ~2,955,169 | Toplam 3 bina 2024 |
| Total Energy Cost EUR | ~681,060 € | 0.30 €/kWh tarife |
| Active Anomaly Count | ~4,067 | Tümü aktif (simüle veri) |
| Net Carbon Footprint tCO2 | ~928 ton | Sayfa 6 ile eşleşmeli |
| Avg EUI kWh m2 | ~0.35 kWh/m²/gün | Günlük değer |
| Avg Business Hours Occupancy | ~50-65 | Ofis + retail mix |
| Vacancy Rate | ~35-50 | Boşluk oranı |
| Renewable Energy Rate | ~20-30 | Hamburg güçlü güneş |
| Forecast 7Day kWh | ~58,000-60,000 | Son 7 tahmin günü |
| Total Annual Saving EUR | ~46,565 € | 3 öneri toplamı |
