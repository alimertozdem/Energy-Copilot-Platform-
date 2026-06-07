# Hourly / Daily / Monthly Granularity — Build Guide

**Amaç:** Sayfa 1-4 + 7'deki zaman-serisi görsellerine **Saatlik / Günlük / Aylık** toggle eklemek ve öksüz kalan `gold_kpi_hourly` fact'ini devreye sokmak.
**DAX:** `semantic-model/70_dax_v58_hourly_granularity.dax`
**Süre:** ~45-60 dk (mekanizma) + sayfa başına ~15 dk.

> **Neden gerekli:** Denetimde `gold_kpi_hourly` hiçbir ölçüde kullanılmıyordu — saatlik veri üretiliyor ama rapora bağlı değildi. Date tablosu gün-grain; saat ekseni yoktu. Bu rehber ikisini de çözer.

---

## ADIM 1 — `gold_kpi_hourly`'yi modele bağla

1. **Model'de var mı kontrol et:** Power BI Desktop → **Model view** → tablo ara: `gold_kpi_hourly`.
   - **Varsa** → Adım 2'ye geç.
   - **Yoksa** → Home → **Get data** → Lakehouse (OneLake) → semantic model'in Lakehouse'u → `gold_kpi_hourly` tablosunu seç → Load (DirectLake).
2. **İlişki kur:** Model view → `gold_kpi_hourly[date]` kolonunu sürükle → `'Date'[Date]` üzerine bırak.
   - Cardinality: **Many-to-One** (gold_kpi_hourly çok taraf, Date tek taraf).
   - Cross-filter: **Single** (Date → hourly).
   - ✅ Active.
3. **Doğrula:** Yeni bir tabloya `gold_kpi_hourly[hour_utc]` + ölçü `TS Consumption kWh` koy → saat-saat değerler gelmeli. Date slicer'ı bir aya daraltınca tablo o aya inmeli.

> **tr:** Saatlik fact büyük (bina × yıl × 8760 saat). Demo'da birkaç bina × ~2 yıl ≈ 50-100K satır — DirectLake rahat taşır. Production'da partition (building_id/year/month) zaten var (03 motoru yazıyor).

---

## ADIM 2 — Time Grain field parameter'ını oluştur

1. **Modeling** sekmesi → **New parameter** → **Fields**.
2. Adı: `Time Grain`. **"Add slicer to this page" işaretini KALDIR** (slicer'ı sonra elle ekleyeceğiz).
3. Şu üç alanı ekle (sırayla — sıra önemli):
   - `gold_kpi_hourly[hour_utc]`  → satırı **"⏱ Saatlik"** olarak yeniden adlandır
   - `'Date'[Date]`               → **"📅 Günlük"**
   - `'Date'[YearMonth]`          → **"🗓 Aylık"**
4. Create. Power BI bir `Time Grain` tablosu üretir (3 satır + sıra sütunu).

> ⚠️ **Aylık = `Date[YearMonth]` ("2024-01"), `Date[Month]` DEĞİL.** Senin Date tablonda `Month` sayısal ay (1-12) — onu kullanırsan tüm yılların Ocak'ı birleşir. `YearMonth` zaten var ve YYYY-MM formatı kronolojik sıralandığı için ekstra sort gerekmez. (Bu yüzden eski Adım 2b'ye gerek kalmadı — Date tablon zaten zengin: YearMonth, Quarter, Year, IsLastWeek vb. mevcut.)

---

## ADIM 3 — v58 ölçülerini ekle

`70_dax_v58_hourly_granularity.dax` dosyasındaki ölçüleri **New Measure** ile ekle (BÖLÜM 1-3). Tümü `gold_kpi_hourly`'den okur → her grain'de doğru toplar.

Çekirdek olanlar: `TS Consumption kWh`, `TS Avg Demand kW`, `TS Peak Demand kW`, `TS Solar Generated kWh`, `TS Net Grid kWh`, `TS CO2 kg`, `TS Avg Temperature C`. 24h profili için: `Profile Avg Demand by Hour kW`, `Profile Avg Consumption by Hour kWh`, `Base Load Ratio Pct`.

> `Selected Grain Label` içindeki `'Time Grain'[Time Grain Order]` ismi, Power BI'ın ürettiği sıra-sütununun gerçek adıyla eşleşmeli (New Parameter sonrası kontrol et, gerekirse düzelt).

---

## ADIM 4 — Toggle'lı görsel kalıbı (her sayfada aynı)

Her zaman-serisi görseli için:

1. **Line chart** (veya Line+Column) ekle.
2. **X-axis** = `Time Grain` (field parameter). ← toggle buradan gelir.
3. **Y / Values** = ilgili `TS ...` ölçüsü/ölçüleri.
4. **Slicer ekle:** Insert → Slicer → field = `Time Grain` → style **Tile** (yatay 3 buton) veya Dropdown, **single-select**, default **📅 Günlük**.
5. Görsel başlığını dinamik yap (opsiyonel): başlık → fx → `Selected Grain Label`.

**Sonuç:** Kullanıcı slicer'dan Saatlik'i seçince X-ekseni `hour_utc`'ye döner ve aynı ölçü saat-saat değer gösterir; Aylık'ta aya toplanır. Tek görsel, üç grain.

---

## ADIM 5 — Sayfa-sayfa uygulama (kapsam: 1, 2, 3, 4, 7)

### Sayfa 1 — Portfolio Overview
- **Toggle ekle:** "Portfolio consumption trend" çizgisine (`TS Consumption kWh`). Yönetici Saatlik'e basınca bugünün saat-saat profilini görür; Aylık'ta yıllık seyir.
- **Not:** KPI kartları (toplamlar) günlük ölçülerde kalabilir — toggle sadece trend görselinde.

### Sayfa 2 — Building Deep-Dive  ⭐ (saatlik en kritik burada)
- **Toggle ekle:** ana tüketim/talep çizgisi → `TS Avg Demand kW` + `TS Net Grid kWh`. Solar binası ise `TS Solar Generated kWh` ikinci seri.
- **24h profil görseli EKLE (ayrı, her zaman saatlik):** Line chart, X = `gold_kpi_hourly[hour]` (0-23), Y = `Profile Avg Demand by Hour kW`. Bu, eksik olan "klasik yük eğrisi". Base load kartı: `Base Load Ratio Pct`.
- **Okuma:** Sabah rampası (07-09), öğle platosu, akşam tepesi (17-19). Gece dip yüksekse (Base Load Ratio > %35) → "uyumayan bina" = standby israfı (A2 anomalisi).

### Sayfa 3 — Anomaly Detection
- **Toggle ekle:** "consumption vs baseline" trend görseline. Saatlik'te bir spike'ın HANGİ SAATTE olduğu görünür (gündüz mü, gece mi → kök neden ipucu).
- **Not:** Anomali tablosu kendi grain'inde kalır; toggle bağlam görseli içindir.

### Sayfa 4 — Forecasting  ◑ (kısmi)
- **Toggle ekle:** sadece **gerçekleşen** tüketim serisine (`TS Consumption kWh`).
- **Forecast** serisi günlük kalır (Prophet günlük üretiyor — `gold_consumption_forecast`). Saatlik forecast Phase-2 işidir.
- **Okuma:** Actuals saatlik, forecast günlük bandı → görselde grain karışmasın diye forecast'i ayrı (daha açık renk) çiz.

### Sayfa 7 — HVAC & Envelope  ◑ (kısmi)
- **Toggle ekle:** tüketim + sıcaklık görseline (`TS Consumption kWh`, `TS Avg Temperature C`). Sıcaklık-tüketim korelasyonu saat-saat çok öğretici.
- **COP / HVAC-split görselleri AYLIK kalır** (`gold_hvac_analytics` aylık; saatlik COP yok). Saatlik COP isteniyorsa kaynak Sayfa 8 IoT (`gold_iot_realtime`, 15-dk sensör).
- **Okuma:** Dış sıcaklık düşerken tüketim artıyorsa ısıtma; yazın artıyorsa soğutma yükü. Delta-T saatlik HVAC verimi proxy'si.

---

## ADIM 6 — Performans & doğrulama
- **Test:** Building slicer = bir bina, Time Grain = Saatlik → görsel ~24-168 nokta (1-7 gün). Yıllık saatlik (8760) tek görselde ağır → Saatlik modda Date slicer'ı makul aralığa (≤1 ay) daralt; rehber notu olarak görsele "Saatlik görünümde tarih aralığını daraltın" ipucu ekle.
- **DirectLake:** import değil → refresh derdi yok, anlık.
- **Doğrulama ölçüsü:** `TS Consumption kWh` (Aylık grain) ≈ mevcut `Total Consumption kWh` (gold_kpi_daily) olmalı. Sapma varsa hourly→daily toplama tutarsızlığı demektir (03 motorunda saatlik→günlük zaten SUM, eşleşmeli).

---

## Bilinen rafine noktalar (sonraya)
- **Local saat:** `gold_kpi_hourly[hour]` UTC saatidir. DE/TR için yerel saat ≠ UTC. 24h profilin kesin doğru olması için 03 motoruna `hour_local` (utc_offset ile) eklenebilir — demo için UTC kabul edilebilir, ama müşteri sunumunda not düş.
- **Hour label:** Eksen `hour` (0-23) tamsayı; "00:00" formatı istenirse `hour_label` calculated column eklenir, `hour`'a göre sırala.
- **Saatlik forecast & saatlik COP:** Phase-2 (Prophet saatlik + IoT COP bridge).

---
*2026-05-30 — gold_kpi_hourly artık devrede. DAX: 70_dax_v58. Kapsam: Sayfa 1/2/3/4/7.*
