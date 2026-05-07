# Page 7 HVAC — v41 Fix Guide
**Tarih:** 2026-05-05  
**DAX dosyası:** `semantic-model/50_dax_v41_page7_fixes.dax`

Bu rehber 4 açık sorunu çözer:
1. Fabric'te 3 bina sorunu (system_type ve missing buildings)
2. Heat Loss kWh/m²·yr yanlış değer (monthly vs annual)
3. New Card label ölçüleri görünmüyor
4. V3/V4 görsel iyileştirmesi

---

## 🔴 SORUN 1 — 3 Bina Görünüyor (6 yerine)

### Kök sebep
Fabric'teki **Notebook 11 eski versiyondur.** Pipeline başarıyla çalıştı ama **eski kodu** çalıştırdı.  
Sonuç: `gold_hvac_analytics` tablosunda hâlâ sadece 3–4 bina var ve tüm binalar `system_type = gas_boiler` görünüyor.

### Fabric'te yapılacaklar

**Adım 1 — Notebook 11'i güncelle**

Fabric workspace'ini aç → `11_hvac_analytics_engine` notebook'una tıkla → tüm hücreleri sil → yerel dosyadan yapıştır:

```
C:\Energy Management App\Energy-copilot-platform\notebooks\gold\11_hvac_analytics_engine.py
```

> **Not:** Tüm içeriği tek bir kod hücresine yapıştır (Python notebook olarak çalıştır).

**Adım 2 — Doğrulama sorgusu**

Notebook'u çalıştırmadan önce yeni bir hücreye şunu ekle ve çalıştır:

```python
# Kaç bina var kontrol et
df_check = spark.sql("SELECT building_id, COUNT(*) as row_cnt FROM gold_hvac_analytics GROUP BY building_id ORDER BY building_id")
df_check.show()
```

**Adım 3 — Notebook 11'i çalıştır**

Tüm hücreleri çalıştır (Run all). Beklenen çıktı:
- 6 bina: B001, B002, B003, B004, B005, B006
- Her biri ~12 ay kayıt
- `system_type` kolon değerleri: B001=heat_pump, B002=gas_boiler, B003=gas_boiler, B004=district, B005=gas_boiler, B006=vrf

**Adım 4 — Sonrası doğrulama**

```python
spark.sql("""
    SELECT building_id, system_type, COUNT(*) as months
    FROM gold_hvac_analytics
    GROUP BY building_id, system_type
    ORDER BY building_id
""").show()
```

Beklenen çıktı:
| building_id | system_type | months |
|-------------|-------------|--------|
| B001        | heat_pump   | 12     |
| B002        | gas_boiler  | 12     |
| B003        | gas_boiler  | 12     |
| B004        | district    | 12     |
| B005        | gas_boiler  | 12     |
| B006        | vrf         | 12     |

**Adım 5 — Power BI refresh**

Power BI Desktop'ta → Home → Refresh  
Slicer'da artık 6 bina görünmeli.

### Power BI slicer cross-filter düzeltmesi (gerekirse)

Eğer Notebook 11 güncellendi ama slicer'da hâlâ 3–4 bina görünüyorsa:

1. Building slicer'ı seç
2. Format bölmesi → **Edit interactions** (üst menüde)
3. Her görsel için interaction tipini kontrol et:
   - V2 tablosu: **Filter** olmalı ✓
   - V1 bar chart: **Filter** olmalı ✓
   - Diğer kartlar: **None** veya **Filter** (sorun değil)
4. `Edit interactions` modunu kapat

---

## 🟡 SORUN 2 — Heat Loss Değeri Yanlış (4–5 yerine 30–150 olmalı)

### Kök sebep
`gold_hvac_analytics[heat_loss_kwh_m2]` **aylık** ortalama değer saklar (~4–5 kWh/m²/ay).  
Yıllıklaştırılmış değer = ×12 → ~48–60 kWh/m²·yr (doğru aralık ✓)

### DAX v41 ile fix

`50_dax_v41_page7_fixes.dax` dosyasını import et.  
Şu ölçüleri **v40 versiyonlarıyla değiştir**:

| Eski (v40) | Yeni (v41) |
|------------|------------|
| Card: Heat Loss v40 | Card: Heat Loss v41 |
| Card: Heat Loss Label v40 | Card: Heat Loss Label v41 |
| Card: EPC Compliance v40 | Card: EPC Compliance v41 |
| Card: EPC Label v40 | Card: EPC Label v41 |
| Card: Avg Insulation v40 | Card: Avg Insulation v41 |
| Card: Insulation Label v40 | Card: Insulation Label v41 |

**Doğrulama:** Tek bina (Hamburg B002) seçiliyken Heat Loss ~60–90 kWh/m²·yr görünmeli.

---

## 🟡 SORUN 3 — Label Ölçüleri Görünmüyor (New Card görseli)

### Kök sebep
New Card görselinde label ölçüsü "Values" veya "Fields" alanına değil, özel **"Reference label"** alanına eklenmelidir.

### Adım adım (her kart için tekrarla)

1. Kart görselini seç (tıkla)
2. Sağ panelde **Visualizations** → **Build visual** sekmesi
3. Field bölümünde iki alan görürsün:
   - **Callout value** → Ana ölçü burada (örn. `Card: Heat Loss v41`)
   - **Reference label** → Label ölçüsü BURAYA gelecek (örn. `Card: Heat Loss Label v41`)
4. `_Label` ölçüsünü **Reference label** alanına sürükle
5. Format bölmesi → **Reference label** → **Font size: 10** → **Color: #aaaaaa**

> **Önemli:** Eğer Reference label alanı görünmüyorsa görsel tipi klasik "Card"dır.  
> Çözüm: Görseli sil → Yeni ekle → Search: "Card (new)" → Seç

### Hızlı kontrol
Format bölmesi → **Reference label** → Toggle **ON** olmalı.  
Toggle OFF ise label her zaman gizlidir.

---

## 🟢 SORUN 4 — V3/V4 Görsel İyileştirmesi

### V3: "Envelope U-Values" → "HVAC CO₂ Scope 1 vs Scope 2"

**Neden değişiyor:** U-Values pasif bir mühendislik bilgisidir. CO₂ scope ayrımı ise direkt CSRD raporlama aksiyonu doğurur — hangi binayı önce heat pump'a geçireceğini gösterir.

**Adımlar:**
1. Mevcut U-Values görselini sil
2. Aynı konuma **Stacked bar chart** ekle
3. Alanları doldur:
   - Y axis: `silver_building_master[building_name]`
   - Values seri 1: `V3: CO2 Scope1 kgCO2 v41` — Renk: `#E84040` (kırmızı)
   - Values seri 2: `V3: CO2 Scope2 kgCO2 v41` — Renk: `#1D9E75` (yeşil)
   - Tooltip: `Scope Badge v40`
4. Format → Data labels → **ON**
5. Başlık: `"HVAC CO₂ Emisyonu — Scope 1 (Fosil) vs Scope 2 (Elektrik)"`

**Beklenen görünüm:**
- B002 Hamburg, B003 München, B005 Frankfurt → büyük kırmızı bar (gas)
- B001 Berliner → sadece yeşil bar (heat pump, no scope 1)
- B004 Wien → orta büyüklükte mavi/yeşil (district heating)
- B006 Amsterdam → sadece yeşil (VRF)

### V4: "Insulation by Building" → "Yıllık Isı Kayıp Yoğunluğu"

**Neden değişiyor:** Insulation score tek başına context vermez. Yıllık heat loss kWh/m²·yr değeri + referans çizgileri hangi binanın acil yatırım gerektirdiğini hemen gösterir.

**Adımlar:**
1. Mevcut "Insulation by Building" görselini sil
2. Aynı konuma **Clustered bar chart** ekle
3. Alanları doldur:
   - Y axis: `silver_building_master[building_name]`
   - X axis: `V4: Heat Loss Annual kWh m2 v41`
   - Tooltip: `V4: EPC Class Label v41` + `V4: Insulation Score by Bldg v41`
4. Analytics bölmesi (Σ simgesi) → **X-axis constant line**:
   - Çizgi 1: Value `90`  Label `"GEG/EPBD Sınırı"` Color `#E84040` Style `Dashed`
   - Çizgi 2: Value `55`  Label `"EPC A Hedefi"` Color `#1D9E75` Style `Dotted`
5. Format → Data colors → **Conditional formatting** → Rules:
   - ≤ 55 → `#1D9E75` (yeşil)
   - 56–90 → `#F2A93B` (sarı)
   - > 90 → `#E84040` (kırmızı)
6. Başlık: `"Yıllık Isı Kayıp Yoğunluğu (kWh/m²·yr)"`

**Beklenen görünüm:**
- B001 Berliner → kısa yeşil bar (~40–55 kWh/m²·yr)
- B005 Frankfurt → uzun kırmızı bar (~100–140 kWh/m²·yr), sınır çizgisini aşıyor
- Retrofit önceliği görsel olarak açık: kırmızı bar = acil

---

## Özet Kontrol Listesi

| # | Sorun | Durum | Aksiyon |
|---|-------|-------|---------|
| 1a | 3 bina görünüyor | ⏳ | Fabric'te Notebook 11 güncelle + re-run |
| 1b | Tüm binalar Gas Boiler | ⏳ | Notebook 11 güncelleme ile otomatik düzelir |
| 2 | Heat Loss 4–5 (monthly) | ✅ | v41 DAX import + ölçüleri değiştir |
| 3 | Label görünmüyor | ✅ | New Card → Reference label alanı kullan |
| 4a | V3 U-Values → CO₂ Scope | ✅ | v41 DAX + görsel yeniden kur |
| 4b | V4 Insulation → Heat Loss bar | ✅ | v41 DAX + görsel yeniden kur |

---

## Sonraki Adım

Tüm fixler tamamlandıktan sonra Page 7 validation checklist:
- [ ] C2 COP: Berliner HP → 3.4–3.8, gaz binalar → "N/A"
- [ ] C4 Heat Loss: 30–150 kWh/m²·yr aralığında
- [ ] V3: 3 kırmızı bar (gaz), 3 yeşil bar (HP/VRF/district)
- [ ] V4: Frankfurt/Amsterdam/Hamburg sınır çizgisini aşıyor
- [ ] Slicer: 6 bina görünüyor, tek bina seçimde kartlar güncelleniyor
