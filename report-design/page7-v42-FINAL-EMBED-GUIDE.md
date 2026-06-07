# Page 7 — HVAC & Building Envelope · v42 FINAL EMBED GUIDE

**Status:** EMBED ÖNCESİ SON DÜZELTMELER — 2026-05-06  
**Active DAX:** `51_dax_v42_page7_english_labels_and_trends.dax`  
**Background:** `report-design/backgrounds/07_hvac_building_envelope_v5_FINAL.png` (değişmiyor)

---

## DURUM OZETI (Ekran görüntüsü analizi)

| Sorun | Kök Sebep | Çözüm |
|-------|-----------|-------|
| ❌ Label ölçüleri Türkçe | v40/v41 label metinleri TR | v42 Label ölçüleri import et |
| ❌ Label görünmüyor — alan yetersiz | Metin çok uzun / "Reference label" slot yanlış | v42 kısa EN metinler + rehber |
| ⚠️ Heat Loss "2 kWh/m²" (yanlış) | monthly × 12 fix (v41) uygulanmamış | v41 Callout + v42 Label rebind |
| ⚠️ Sadece 3 bina görünüyor | Notebook 11 eski versiyonda | Fabric Notebook 11 güncelle |
| ⚠️ Tüm binalar "Gas Boiler" | system_type filtresi sorun | v39 TREATAS fix + Notebook 11 |
| ❌ Zaman karşılaştırması yok | YoY/MoM ölçüleri yoktu | v42 B1–B4 ölçüleri eklendi |
| ❌ Renk uyumsuzluğu | Card renkler ile chart renkler farklı | Format ayarları rehberi (Bölüm 5) |
| ❌ "See details" kırık kart | EPC Compliance ölçüsü rebind eksik | v42 Card: EPC Compliance v42 |

---

## 🔴 BÖLÜM 1 — FABRİC PİPELİNE (3 bina → 6 bina fix)

> Bu adımı ilk yap — Power BI tarafındaki hiçbir fix, veri yoksa işe yaramaz.

### 1.1 Notebook 11 güncelleme

Fabric Workspace → `11_hvac_analytics_engine` notebook → tüm hücreleri sil → yerel dosyadan yapıştır:
```
C:\Energy Management App\Energy-copilot-platform\notebooks\gold\11_hvac_analytics_engine.py
```

### 1.2 Çalıştırma sırası

```
01_bronze_ingestion.py      → Run All
02_silver_transformation.py → Run All
11_hvac_analytics_engine.py → Run All
```

### 1.3 Doğrulama sorgusu (Notebook yeni hücre)

```python
spark.sql("""
    SELECT building_id, system_type, COUNT(*) as months
    FROM gold_hvac_analytics
    GROUP BY building_id, system_type ORDER BY building_id
""").show()
```

**Beklenen çıktı:**
```
B001 | heat_pump   | 12
B002 | gas_boiler  | 12
B003 | gas_boiler  | 12
B004 | district    | 12
B005 | gas_boiler  | 12
B006 | vrf         | 12
```

### 1.4 Power BI refresh

Power BI Desktop → Home → **Refresh**  
→ Slicer: 6 bina görünmeli; V2 tablosunda B001 Berliner = "🔵 Heat Pump (ASHP)"

---

## 🟡 BÖLÜM 2 — DAX IMPORT

### 2.1 v42 ölçülerini import et

Power BI → Modelling sekmesi → **New measure** (gold_hvac_analytics tablosunda)  
Dosya: `semantic-model/51_dax_v42_page7_english_labels_and_trends.dax`

Her ölçü bloğu için:
1. DAX editöründe ilgili ölçüyü seç (yorumlar arası)
2. `New measure` → yapıştır → **Enter / Checkmark**

**Import listesi:**
| Ölçü Adı | Bölüm | Kullanım yeri |
|---|---|---|
| `Card: HVAC Share Label v42` | A1 | C1 Reference label |
| `Card: COP Label v42` | A2 | C2 Reference label |
| `Card: Insulation Label v42` | A3 | C3 Reference label |
| `Card: Heat Loss Label v42` | A4 | C4 Reference label |
| `Card: Retrofit Label v42` | A5 | C5 Reference label |
| `Card: CO2 Label v42` | A6 | C6 Reference label |
| `Card: Gas Exposure Label v42` | A7 | C7 Reference label |
| `Card: EPC Compliance v42` | A8b | C8 Callout |
| `Card: EPC Label v42` | A8 | C8 Reference label |
| `Card: CO2 YoY v42` | B1 | C6 Tooltip |
| `Card: HVAC Share MoM v42` | B2 | C1 Tooltip |
| `Card: Heat Loss YoY v42` | B3 | C4 Tooltip |
| `Card: Insulation YoY v42` | B4 | C3 Tooltip |
| `Heating Prior Year v42` | C1 | V1 (isteğe bağlı) |

---

## 🟡 BÖLÜM 3 — KARTI REBIND (Reference Label Fix)

> Bu adım **her kart** için uygulanmalı. Label ölçülerinin görünmemesinin sebebi budur.

### 3.1 Adım adım (tüm kartlar için tekrarla)

```
1. Kartı seç (tıkla)
2. Sağ panel → Visualizations → "Build visual" sekmesi
3. Fields bölmesinde 2 alan göreceksin:
   ┌─────────────────────────────┐
   │ Callout value               │  ← Sayısal ölçü burada (değiştirilmiyor)
   │ Reference label             │  ← LABEL ölçüsü BURAYA gelecek
   └─────────────────────────────┘
4. v42 Label ölçüsünü "Reference label" alanına sürükle
5. Format bölmesi → "Reference label" → Toggle: ON
6. Font size: 10  |  Color: #7DB4DC
```

> ⚠️ "Reference label" alanı görmüyorsan görsel tipi klasik Card'dır.  
> Çözüm: Görseli sil → Insert → Visual → Search: **"Card (new)"** → ekle

### 3.2 Kart rebind tablosu

| Kart | Callout (değişmez) | Reference label (v42 ile güncelle) | Tooltip |
|------|-------------------|-----------------------------------|---------|
| C1 HVAC Share | `HVAC Share Pct Display v39` | `Card: HVAC Share Label v42` | `Card: HVAC Share MoM v42` |
| C2 Avg COP | `Card: Avg COP v40` | `Card: COP Label v42` | — |
| C3 Insulation | `Card: Avg Insulation v41` | `Card: Insulation Label v42` | `Card: Insulation YoY v42` |
| C4 Heat Loss | `Card: Heat Loss v41` | `Card: Heat Loss Label v42` | `Card: Heat Loss YoY v42` |
| C5 Retrofit | `Card: Buildings For Retrofit v40` | `Card: Retrofit Label v42` | — |
| C6 CO₂ | `Card: HVAC CO2 v40` | `Card: CO2 Label v42` | `Card: CO2 YoY v42` |
| C7 Gas Exposure | `Card: Gas Exposure v40` | `Card: Gas Exposure Label v42` | — |
| C8 EPC | `Card: EPC Compliance v42` | `Card: EPC Label v42` | — |

---

## 🟡 BÖLÜM 4 — DEĞER DOĞRULUĞU (Validation)

### 4.1 C4 Heat Loss fix (×12)

Eğer C4 hâlâ ~2 kWh/m² gösteriyorsa Callout ölçüsü henüz v41'e güncellenmemiş demektir:

```
Callout value'yu değiştir:
  Eski: (herhangi bir v34/v36 heat loss ölçüsü)
  Yeni: Card: Heat Loss v41
```

### 4.2 Beklenen değer aralıkları (All binalar seçili, tüm tarihler)

| Kart | Beklenen aralık | Sorunsa |
|------|----------------|---------|
| C1 HVAC Share | 35–55 % | Notebook 11 re-run |
| C2 Avg COP | N/A (gaz ağırlıklı) / 3.4–3.8 (HP seçiliyken) | COP bind yanlış |
| C3 Insulation | 60–78 / 100 | ALLSELECTED fix (v41) |
| C4 Heat Loss | 30–110 kWh/m²·yr | v41 Callout uygulanmamış |
| C5 Retrofit | 2–3 | Notebook 11 re-run |
| C6 CO₂ | 240–350 tCO₂ | has_gas pipeline bug |
| C7 Gas Exposure | 50–67% | Veri doğru |
| C8 EPC Compliance | 1–2 / 3 buildings | EPC eşik fix (v41) |

### 4.3 Tek bina testi — Berliner Bürogebäude (B001, Heat Pump)

```
C1: 45–55%    C2: 3.4–3.8    C3: 85–95     C4: 35–55 kWh/m²·yr
C5: 0          C6: ~18–25 tCO₂   C7: 0%    C8: 1/1 buildings
V2: "🔵 Heat Pump (ASHP)" · "🟢 Low" · "🟢 Monitor SCOP monthly"
```

---

## 🎨 BÖLÜM 5 — RENK UYUMU

Sayfadaki renkler birbiriyle çelişiyor. Bu bölüm standartlaştırır.

### 5.1 Kart aksan renkleri (değişmiyor — v37 planından geliyor)

| Kart | Aksan Renk | Hex |
|------|-----------|-----|
| C1 HVAC Share | Turuncu | `#FF6B35` |
| C2 Avg COP | Amber | `#FFC107` |
| C3 Insulation | Yeşil | `#1D9E75` |
| C4 Heat Loss | Mavi | `#00D4FF` |
| C5 Retrofit | Kırmızı | `#E24B4A` |
| C6 CO₂ | Mor | `#9B59B6` |
| C7 Gas Exposure | Kırmızı-turuncu | `#E84040` |
| C8 EPC | Mavi-gri | `#4A6E96` |

### 5.2 V1 HVAC Breakdown — renk düzeltme

Kış ısıtma = kırmızı, yaz soğutma = mavi, havalandırma = amber olmalı:

```
Heating Energy kWh v34  → #E24B4A  (kırmızı-sıcak)
Cooling Energy kWh v34  → #00D4FF  (mavi-soğuk)
Ventilation Energy kWh  → #FFC107  (amber)
```

**Seri adını da güncelle:** Field well'de sağ tık → Rename:
- "Heating Energy kWh v34" → "Heating"
- "Cooling Energy kWh v34" → "Cooling"
- "Ventilation Energy kWh v34" → "Ventilation"

### 5.3 V3 CO₂ Scope chart — renk standardı

```
V3: CO2 Scope1 kgCO2 v41  → #E24B4A  (kırmızı — C5 ile tutarlı)
V3: CO2 Scope2 kgCO2 v41  → #1D9E75  (yeşil — C3 ile tutarlı)
```

Başlık İngilizce olsun:  
`"HVAC CO₂ Emissions — Scope 1 (Fossil) vs Scope 2 (Electric)"`

### 5.4 V4 Heat Loss bar — renk koşulu (C4 mavi ile tutarlı)

```
Data colors → Conditional formatting → Rules:
  ≤ 55  kWh/m²·yr → #1D9E75  (yeşil)
  56–90 kWh/m²·yr → #F2A93B  (amber)
  > 90  kWh/m²·yr → #E24B4A  (kırmızı — C5 ile tutarlı)
```

Başlık: `"Annual Heat Loss Density (kWh/m²·yr)"`

### 5.5 V5 Renovation Matrix — renk standardı

```
Scatter → Bubbles → Color → fx → Rules:
  Renovation Priority Color v39 = 1 → #1D9E75  (Low — yeşil)
  Renovation Priority Color v39 = 2 → #FFC107  (Medium — amber)
  Renovation Priority Color v39 = 3 → #E24B4A  (High — kırmızı)
```

Reference lines:
```
X-axis: 60 — Label "Insulation Target" — #7DB4DC dashed
Y-axis: 60 — Label "Efficiency Target" — #7DB4DC dashed
```

---

## ⏱️ BÖLÜM 6 — ZAMAN KARŞILAŞTIRMALI ANALİZ

> Veri aralığı 2024-06 → 2026-02 (~20 ay). YoY karşılaştırması mümkün.

### 6.1 YoY/MoM ölçülerini Tooltip olarak ekle

Her kart için:
```
Kart seçili → Format bölmesi → Tooltip → + Add a field
→ v42 YoY/MoM ölçüsünü ekle
```

Örnek: C6 CO₂ kartında mouse-over → "▼ 8.2% YoY ✅" görünür

### 6.2 V1 Chart — Prior Year Heating serisi (isteğe bağlı, test et)

```
V1 Stacked bar seçili → Y-axis → + Add a measure:
  Heating Prior Year v42
  Renk: #FF6B35  (turuncu)  |  Line style: dashed
  Legend label: "Prior Year Heating"
```

> ⚠️ Eğer chart karmaşık görünüyorsa bu adımı atla — V1 temel haliyle yeterli.

### 6.3 Date Slicer kullanım testi

Kullanıcı perspektifinden zaman karşılaştırması:
1. Date Range: Jun 2024 – Dec 2024 seç → CO₂ değer X
2. Date Range: Jun 2025 – Dec 2025 seç → CO₂ değer Y
3. Kart tooltip'te "▼/▲ %Z YoY" otomatik gösterir

> Bu pattern kullanıcıların "karşılaştırmalı analiz" ihtiyacını karşılar.

---

## 🏁 BÖLÜM 7 — EMBED ÖNCESİ FINAL CHECKLİST

Bu 12 madde tamam → embed aşamasına geç:

### Veri
- [ ] Notebook 11 güncellendi ve Fabric'te re-run edildi
- [ ] gold_hvac_analytics'te 6 bina × 12 ay var
- [ ] Power BI semantic model refresh edildi

### Kartlar
- [ ] C1–C8 tüm kartlar sayısal değer gösteriyor (— veya "No data" değil)
- [ ] C4 Heat Loss: 30–110 kWh/m²·yr aralığında (2 değil)
- [ ] Her kart Reference label alanında İngilizce kısa metin gösteriyor
- [ ] C8 EPC: "X / Y buildings" formatında (Türkçe "bina" değil)

### Görseller
- [ ] V1: 12 ay × 3 seri — kış heating bar dominant
- [ ] V2: Berliner = "🔵 Heat Pump", diğerleri = "🟠 Gas Boiler"
- [ ] V3: Kırmızı (Scope 1) + yeşil (Scope 2) bar, 6 bina
- [ ] V4: 6 bar — kırmızı/sarı/yeşil — referans çizgileri görünür
- [ ] V5: 6 bubble, 3 renk, Berliner sağ-üst köşede

### Dil / Renk
- [ ] Tüm görsel başlıkları İngilizce
- [ ] V1/V3/V4/V5 renkleri C3/C4/C5 kart renkleriyle tutarlı
- [ ] Hiçbir Türkçe metin kullanıcıya görünmüyor

### Zaman analizi
- [ ] C6 CO₂ kartı tooltip'te YoY değişim gösteriyor
- [ ] Date slicer ile farklı dönem seçiminde kartlar/görseller güncelleniyor

---

## BACKGROUND — DEĞİŞMİYOR

Mevcut arka plan `07_hvac_building_envelope_v5_FINAL.png` bu layout ile uyumlu.  
Değişiklik gerekmez:
- 6 KPI kart zonu üstte ✓
- Sol sidebar slicer bölgesi ✓
- Alt 3 görsel zonu ✓

Eğer gelecekte layout değişirse (örn. YoY trend chart eklenmesi) yeni background gerekecek.

---

## PHASE 2 NOTU

Aşağıdakiler embed sonrası Phase 2'ye bırakıldı:
- Gerçek zamanlı COP izleme (BMS/IoT connector)
- ASHRAE 90.1 / EN 15232 benchmark karşılaştırma görseli
- Ülke bazlı elektrik emisyon faktörü (şu an EU ort. 0.350 kullanılıyor)
- V1'e prior year line chart (test edilmesi gerekiyor)
