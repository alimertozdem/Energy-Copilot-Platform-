# Bölüm 8 DAX — Zaman Karşılaştırma Hatası ve Çözümü

## Sorun

`PREVIOUSMONTH`, `DATESYTD`, `DATEADD` gibi **Time Intelligence** fonksiyonları hata veriyor.

Olası hata mesajları:
```
A function 'PREVIOUSMONTH' has been used in a True/False expression...
The column 'Date[Date]' does not contain unique values...
Time intelligence functions cannot be used with Date...
```

---

## Kök Neden

Power BI / Fabric Semantic Model'de Time Intelligence fonksiyonları çalışabilmek için **Date tablosunun "Mark as date table" yapılmış olması gerekir.**

Bu adım atlanırsa tüm `PREVIOUSMONTH`, `DATESYTD`, `SAMEPERIODLASTYEAR` gibi fonksiyonlar hata verir.

---

## Çözüm — Adım 1: Date Tablosunu İşaretle

Model editöründe şu adımları izle:

1. Sol panelde `Date` tablosuna **sağ tıkla**
2. **"Mark as date table"** seç
3. Açılan pencerede **Date** kolonunu seç (tip: Date)
4. **OK** → Onayla

> ✅ Bundan sonra tablonun yanında küçük bir takvim ikonu çıkar — bu işin yapıldığının göstergesidir.

---

## Çözüm — Adım 2: detected_date Kolon Tipini Değiştir (İlişki #4)

`gold_anomalies[detected_date]` kolonu TEXT olarak geliyor ama Date tablosuyla ilişki kurmak için Date tipinde olmalı.

Model editöründe:
1. `gold_anomalies` tablosunu seç
2. `detected_date` kolonuna tıkla
3. Sağ tarafta **"Data type"** → **Date** seç
4. Kaydet

> Fabric ISO 8601 formatını (YYYY-MM-DD) otomatik olarak Date'e çevirir.

---

## Çözüm — Adım 3: DAX'ı Düzelt (Opsiyonel)

Eğer "Mark as date table" sonrası hala hata alıyorsan, 02_dax_measures.dax dosyasındaki Bölüm 8 kodlarını aşağıdaki güncel versiyonlarla değiştir:

```dax
// ── DÜZELTILMIŞ BÖLÜM 8 ──────────────────────────────────────

// Önceki ay tüketimi
Previous Period Consumption kWh =
CALCULATE(
    [Total Consumption kWh],
    PREVIOUSMONTH('Date'[Date])     -- 'Date' şeklinde tırnak içinde yaz
)

// Tüketim değişimi (%)
Consumption Change Pct =
VAR _current  = [Total Consumption kWh]
VAR _previous = [Previous Period Consumption kWh]
RETURN
DIVIDE(_current - _previous, _previous, 0) * 100

// Önceki ay maliyet
Previous Period Cost EUR =
CALCULATE(
    [Total Energy Cost EUR],
    PREVIOUSMONTH('Date'[Date])
)

// Maliyet değişimi (%)
Cost Change Pct =
VAR _current  = [Total Energy Cost EUR]
VAR _previous = [Previous Period Cost EUR]
RETURN
DIVIDE(_current - _previous, _previous, 0) * 100

// YTD tüketim
YTD Consumption kWh =
CALCULATE(
    [Total Consumption kWh],
    DATESYTD('Date'[Date])
)

// YTD CO2
YTD CO2 Emissions tCO2 =
CALCULATE(
    [Total CO2 Emissions tCO2],
    DATESYTD('Date'[Date])
)
```

---

## Önemli Not: Tablo adı `Date` mi, `'Date'` mi?

Fabric DAX'ta tablo adı rezerve kelimelerle çakışıyorsa (örn. `Date` bir rezerve kelime değil ama boşluklu isimlerde sorun çıkabilir) tablo adını tek tırnak içine almak her zaman güvenlidir:

```dax
-- Güvenli yazım:
PREVIOUSMONTH('Date'[Date])

-- Aynı anlama gelir ama bazen hata verebilir:
PREVIOUSMONTH(Date[Date])
```

---

## Özet Checklist

- [ ] Date tablosu → **Mark as date table** yapıldı mı?
- [ ] `detected_date` kolonu → **Date** tipine çevrildi mi?
- [ ] Tablo adı DAX'ta `'Date'` şeklinde tırnaklı mı?
- [ ] 08_occupancy_prediction notebook'u pipeline'da yeniden çalıştırıldı mı?
- [ ] `gold_occupancy_profile` tablosu modele eklendi mi?
