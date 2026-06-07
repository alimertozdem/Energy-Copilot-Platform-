---
title: "EnergyLens — Dashboard Finalization Plan & Working Reference"
subtitle: "Raporu satılabilir 'CSRD-grade' hale getirme yol haritası + öğrenme dokümanı"
author: "Ali Mert Özdemir"
date: "2026-05-30"
---

# 0. Bu doküman nedir / nasıl kullanılır

İki işi tek dosyada birleştirir:

1. **PLAN** — Dashboard'u "final, satılabilir" hale getirme yol haritası (hangi sayfa, hangi sırayla, ne yapılacak, "bitti" tanımı).
2. **ÇALIŞMA REFERANSI** — Düzeltilmiş metodolojinin doğru anlatımı (her görsel: *nasıl okunur, nasıl hesaplanır, neden önemli*) + TR ipuçları. Müşteri toplantısında her soruya hazır olman için.

> **tr:** Bu dosya `docs/audit/2026-05-30_gap_register.md` (denetim — *neyin yanlış olduğu*) ile birlikte okunur. Register = teşhis. Bu doküman = tedavi planı + öğrenme. Düzeltmeler tamamlandıkça Bölüm 4 büyür ve sonunda **Phase-3 PDF** (her görsel için tam anlatım) buradan üretilir.

Kaynak gerçeği: tüm faktörler/fiyatlar artık `ref_grid_emission_factors`, `ref_electricity_tariffs`, `ref_fuel_factors` tablolarından gelir (kaynak + URL + yıl taşır). Tek değer her sayfaya akar.

---

# 1. Durum anlık görüntüsü (2026-05-30)

| Katman | Durum | Not |
|---|---|---|
| **Denetim (9 sayfa)** | ✅ Bitti | Gap register, ~30 bulgu, severity + kanıt |
| **Referans katmanı** (`03_ref_factors_tariffs_loader.py`) | ✅ Bitti + py_compile | Yıl-indeksli, kaynaklı tek-doğru-kaynak |
| **Sayfa 6 — GHG motoru** (`09_ghg_scope_engine.py`) | ✅ Refactor + py_compile | A1/A2/F2/D1/D2 kapandı |
| **Sayfa 6 — DAX** (`69_dax_v57_page6_audit_fixes.dax`) | ✅ Yazıldı | L2 (EPC ağırlık), L3 (CRREM S1+2), F1 (relabel) |
| `03_gold_kpi_engine` ref-wiring | ⏳ Sıradaki | EF/tarife ref'ten; Scope-2 intensity kaynağı |
| `05 / 06 / 12` tarife ref-wiring | ⏳ Sıradaki | F3/I2 — fiyat çoğullaması biter |
| Sayfa 3 anomali tek motor | ⏳ Planlı | C1 — iki motor çakışması |
| DAX konsolidasyon (68→1 TMDL) | ⏳ Planlı | L1 |
| Sayfa 1-2 / 4 / 5 polish | ⏳ Planlı | B1, E1, A3 |
| Sayfa 7-9 polish | ⏳ Planlı | G1-G2, I3-I4 |
| Demo data tek kayıt | ⏳ Planlı | A4/I1 — B003/B005 kimlik çakışması |

**Özet:** İlk modül (referans) + asıl niş sayfasının (Sayfa 6) çekirdeği bitti. Kalan iş tanımlı ve sıralı.

---

# 2. Her sayfa için "Final" tanımı (Definition of Done)

Her sayfa: **okuyucu**, **görseller**, **doğru metodoloji**, **DoD checklist**. Bu bölüm aynı zamanda çalışma referansının iskeletidir.

## Sayfa 1 — Portfolio Overview
- **Okuyucu:** Energy Manager / C-suite — "portföy bu ay nasıl?"
- **Görseller:** bina bazında kWh bar; kWh/m² (EUI) ısı haritası; toplam € maliyet; toplam CO₂; en kötü 3 bina (tip-benchmark'a göre).
- **Doğru metodoloji:** EUI **yıllıklandırılmış** karşılaştırılmalı (benchmark <80/130/200 yıllıktır). CO₂ = ref yıl-indeksli faktör. Maliyet = ref tarife (ülke bazlı).
- **DoD:** ☐ EUI annual-normalize ☐ CO₂ ref'ten ☐ maliyet ref tarife ☐ top-3 doğru benchmark'a göre.

## Sayfa 2 — Building Deep-Dive
- **Okuyucu:** Facility Manager — "binam şu an ne yapıyor?"
- **Görseller:** 24-saat tüketim profili (kW); günün peak'i vs baseline; ay-içi maliyet; iklim-düzeltilmiş EUI.
- **Doğru metodoloji:** **B1 fix** — climate-adjusted EUI = `EUI × (ref HDD+CDD / gerçek HDD+CDD)`, hem HDD hem CDD. (Mevcut kod sadece HDD'ye bölüyor — düzeltilecek.) Peak kW = gerçek aralık (15-dk varsa ×4, saatlikse ×1 — **B3 fix**).
- **DoD:** ☐ climate-adj EUI ratio yöntemi + CDD ☐ peak interval-aware.

## Sayfa 3 — Anomaly Detection
- **Okuyucu:** Facility + Energy Manager.
- **Görseller:** severity dağılımı; tip kırılımı; anomali tablosu (zaman, tip, severity, sistem, aksiyon, € kayıp); çözüm durumu.
- **Doğru metodoloji:** **C1 fix** — TEK motor (`anomaly_detection.py` öneriliyor), TEK taksonomi, TEK severity casing (UPPERCASE). `03`'ün §8 anomali bloğu kaldırılır. Spike kuralı hava-guard'lı (doc 1.5× ile uyum). Karbon eşiği `gold_crrem_pathway`'den (hardcoded dict değil).
- **DoD:** ☐ tek motor ☐ tek taksonomi ☐ severity tek-case ☐ boolean `== True` (string değil, **C4**).

## Sayfa 4 — Forecasting
- **Okuyucu:** Energy / Sustainability Manager — "gelecek ay ne tutar?"
- **Görseller:** 7/30/90-gün tüketim tahmini (Prophet); tahmin € + CO₂; **güven bandı**.
- **Doğru metodoloji:** **E1 fix** — `F` import'u veri okumadan ÖNCE (occupancy regressor şu an sessizce devre dışı). Güven bandı zaten hesaplanıyor → görselde göster (**E3**). MAPE in-sample → "in-sample fit" diye etiketle veya Prophet cross_validation (**E2**).
- **DoD:** ☐ F-import bug ☐ band görselde ☐ MAPE dürüst etiket.

## Sayfa 5 — Decision Support
- **Okuyucu:** Energy / Sustainability Manager.
- **Görseller:** önceliklendirilmiş aksiyonlar; € / kWh / CO₂ tasarruf; effort; payback; teşvik eşleşmesi (KfW/BAFA/YEKA/SDE++).
- **Doğru metodoloji:** Çok-ülke uyumluluk motoru (`05`) **zaten güçlü — koru**. Sadece: tarife ref'ten (**F3**), `csrd_score` → `eu_taxonomy_carbon_score` yeniden adlandır (**F1**), gaz CO₂ tek baz (**F2**), `gold_simulation_results` üretildiğini doğrula (**F4**).
- **DoD:** ☐ tarife ref ☐ CSRD relabel ☐ simulation tablosu canlı.

## Sayfa 6 — Sustainability / ESG  ⭐ (asıl niş — çekirdek BİTTİ)
- **Okuyucu:** Sustainability Manager, ESG danışmanı, **denetçi**.
- **Görseller:** Scope 1/2/3 donut; YoY Scope bar; **EPC alan-ağırlıklı** ısı haritası; CRREM stranding; ESG skor; karbon kredi €.
- **Doğru metodoloji (DÜZELTİLDİ):**
  - Faktörler yıl-indeksli ref'ten (A1/A2). ✅
  - Scope 2: **location + market ayrı** (D2). Market = location yalnızca kontraktüel araç yoksa (GHG Protocol doğrusu). ✅
  - Scope 3: `%8` bir **screening** tahmini — `scope3_disclosure_grade=False` ile dürüstçe işaretli (D1). ✅ Gerçek ESRS için kategori-bazlı veri gerekir.
  - EPC: **alan-ağırlıklı** (L2). ✅
  - CRREM: bina **Scope 1+2** yoğunluğu vs Scope 1+2 pathway (L3). ✅
  - "CSRD score" → **EU Taxonomy Carbon Score** + ayrı **CSRD Disclosure Readiness %** (F1). ✅
- **DoD (kalan):** ☐ refrigerant Scope 1 opsiyonu (D4) ☐ 09'u çalıştır + gold_ghg_scope yeni kolonları model'e ekle ☐ v57 ölçülerini Tabular Editor ile yükle ☐ görsellere "modeled/estimate" etiketleri.

## Sayfa 7 — HVAC & Building Envelope
- **Okuyucu:** Facility Manager / bina sahibi.
- **Görseller:** saatlik COP; supply/return delta-T; HVAC runtime; **HVAC payı**; yalıtım skoru; renovasyon önceliği.
- **Doğru metodoloji:** **G1** — ısıtma/soğutma/havalandırma ayrışması TİP-katsayılı bir MODEL'dir (sub-metre değil) → görselde "modeled (HDD/CDD method)" etiketi şart. **G2** — `system_label` + `renovation_reason` Türkçe → İngilizce/trilingual yap (İngilizce-UI kuralı).
- **DoD:** ☐ "modeled" etiketi ☐ etiketler İngilizce.

## Sayfa 8 — Real-Time IoT
- **Okuyucu:** Facility (ops) + Energy (strateji).
- **Görseller:** real-time kW; zone comfort %; CO₂; aktif alarm + günlük € tahmin; 24h trend; sensör uptime matrisi; zone uyum; alarm tablosu.
- **Doğru metodoloji:** **H1** — € maliyet mantığı simülatöre değil silver IoT'ye taşınmalı (gerçek BACnet'te €0 göstermemesi için), merkezi grid-fiyatından. Demo için **statik IoT snapshot** gerekir (trial sonrası EventStream kapalı).
- **DoD:** ☐ cost logic silver'da ☐ demo snapshot ☐ severity tek-case.

## Sayfa 9 — Battery Dispatch & ROI
- **Okuyucu:** Energy Manager, CFO, yatırımcı.
- **Görseller:** teknoloji×ülke matrisi; strateji karşılaştırma; ülke fiyatı; € yatırım; payback/NPV/IRR; EU 2023/1542 uyum.
- **Doğru metodoloji:** **I3** — `cost_avoided` her deşarjı PEAK fiyatla değerliyor (abartı) → saat-bazlı tarife; demand-saving peak-kW bazlı olmalı. **I2** — grid CO₂ ref'ten (450≠430≠442 biter). **I4** — tek otoriter batarya pipeline (v56), gerisi arşiv.
- **DoD:** ☐ ROI gerçekçi ☐ CO₂ ref ☐ tek pipeline ☐ EU uyum bayrağı görünür.

---

# 3. Finalleştirme yol haritası (sıralı, dosya-spesifik)

> Sıra BMAD + "tek modül, büyük kararda onay". Her adım bağımsız test edilebilir.

**Adım 0 — Referans katmanı.** ✅ BİTTİ (`03_ref_factors_tariffs_loader.py`).

**Adım 1 — Sayfa 6 (asıl niş).** ✅ Çekirdek bitti (09 + DAX v57). Kalan: 09'u Fabric'te çalıştır, gold_ghg_scope yeni kolonlarını model'e ekle, v57 ölçülerini yükle, refrigerant opsiyonu (D4).

**Adım 2 — Çekirdek KPI ref-wiring (`03_gold_kpi_engine`).** *Sıradaki.*
- `df_bld_lookup`'tan `emission_factor_kg_kwh` yerine `ref_grid_emission_factors` JOIN (country, YEAR). Hourly CO₂ artık yıl-indeksli.
- `ELECTRICITY_TARIFF_EUR_KWH = 0.30` → `ref_electricity_tariffs` JOIN (country). Maliyet ülke-doğru.
- B1: `hdd_normalized_eui` → ratio yöntemi (`× ref(HDD+CDD)/actual(HDD+CDD)`), CDD dahil; kolon adı `climate_adjusted_eui`.
- B3: peak kW reading-interval-aware.

**Adım 3 — Sayfa 5 motorları ref-wiring (`05`, `06`).**
- `RATE_*` sabitleri → `ref_electricity_tariffs`. Gaz CO₂ → `ref_fuel_factors`. `csrd_score` kolonunu yeniden adlandır.

**Adım 4 — Sayfa 9 batarya (`12`/`14`/`15`).**
- `pricing_data` inline → `ref_electricity_tariffs` + `ref_grid_emission_factors`. ROI gerçekçileştir (I3). Tek pipeline seç (I4).

**Adım 5 — Sayfa 3 anomali konsolidasyon.**
- Tek motor; `03` §8 anomali bloğunu çıkar; taksonomi + severity dondur; C4 boolean fix; karbon eşiği CRREM tablosundan.

**Adım 6 — DAX konsolidasyon (L1).**
- 68 `.dax` patch → tek TMDL/semantic model (Git'te). v57 bu konsolidasyonun Sayfa-6 dilimidir.

**Adım 7 — Sayfa 7-8 polish + demo data.**
- G1/G2 (HVAC etiket + "modeled"), H1 (IoT cost), A4/I1 (tek bina kayıt defteri: B003/B005 kimliğini sabitle).

**Adım 8 — Phase 3: per-visual PDF.** Bütün sayfalar final olunca, Bölüm 2+4'ten tam çalışma PDF'i üretilir.

---

# 4. Düzeltilmiş metodoloji referansı (çalışma çekirdeği)

> Her başlık: **Formül/Nasıl hesaplanır** · **Neden önemli** · **Görsel nasıl okunur** · **tr ipucu**. Denetimde düzelttiğimiz metodolojilere odaklı — KPI formüllerinin tamamı `EnergyLens_Master_Study_Guide`'da; burası *değişen/satışı taşıyan* kısımlar.

## 4.1 Referans katmanı — yıl-indeksli emisyon faktörü
- **Nasıl:** `ref_grid_emission_factors(country, year, factor, source, url)`. Motor JOIN'le (ülke, raporlama-yılı) → o yılın faktörü. DE = UBA serisi (2022=0.433, 2023=0.386, 2024=0.363), TR = 0.442 (TEİAŞ).
- **Neden:** Binanın 2023 Scope 2'si 2023 faktörüyle, 2024'ü 2024'le hesaplanmalı. Tek-düz faktör, "şebeke temizlendi"yi "bina iyileşti" sanır → YoY karbon trendi yanlış olur. Denetçi faktörün yılla eşleşmesini bekler.
- **Görsel nasıl okunur:** YoY Scope bar düşüyorsa, faktör-düşüşü mü yoksa tüketim-düşüşü mü? Tooltip ikisini ayırmalı.
- **tr ipucu:** "Hangi yılın grid faktörünü kullanıyorsun?" sorusuna cevap: *"Reporting-year matched — each year's emissions use that year's published national factor, sourced from UBA/TEİAŞ."* Bu cümle seni 100 freelancer'dan ayırır.

## 4.2 Scope 1/2/3 (GHG Protocol) — düzeltilmiş
- **Nasıl:**
  - **Scope 1** (doğrudan): gaz = ısıtma_kWh / kazan_verimi × `0.201 kg/kWh` (ref_fuel). (Gaz sayacı verisi gelince proxy kalkar.)
  - **Scope 2 location**: net_grid × ülke-yıl faktörü.
  - **Scope 2 market**: net_grid × *supplier_ef* (yeşil kontrat/PPA varsa); yoksa = location (GHG Protocol kuralı, hata değil).
  - **Scope 3**: `(S1+S2)×%8` — **screening**, `disclosure_grade=False`. ESRS için kategori-bazlı (Cat 1/6/7/13) veri gerekir.
- **Neden:** ESRS E1-6 Scope 2'yi **iki yöntemle** ister; çoğu firma market-based'i unutur → denetimde takılır. Scope 3 binalarda genelde EN BÜYÜK kalemdir; %8'i ESRS-ready diye sunmak kredibiliteyi yıkar.
- **Görsel nasıl okunur:** Donut'ta Scope 2 location vs market FARKLI olmalı (yeşil kontratlı binada). Scope 3 dilimi "est." etiketli.
- **tr ipucu:** "Market-based Scope 2 yapıyor musun?" → *"Yes — both location and market-based, separately, per E1-6. Market uses contractual instruments where the client has GoOs or a PPA; otherwise it equals location, as the Protocol requires."*

## 4.3 EPC — alan-ağırlıklı portföy skoru
- **Nasıl:** `Σ(epc_score × conditioned_area) / Σ(conditioned_area)` (DAX v57). Düz `AVERAGE` DEĞİL.
- **Neden:** 200 m² depo ile 20.000 m² kule eşit ağırlık alamaz. Düz ortalama = "average of building averages" = klasik denetim hatası. Taxonomy alignment % de EPC'ye bağlı → ağırlık yanlışsa yatırımcı raporu yanlış.
- **Görsel nasıl okunur:** Isı haritasında küçük-iyi binalar portföy rengini yeşile çekmemeli; ağırlıklı skor büyük-kötü binaları yansıtır.
- **tr ipucu:** *"Area-weighted, not building-count — by conditioned floor area."* Tek cümle, ESG danışmanı güvenir.

## 4.4 CRREM stranding — Scope 1+2
- **Nasıl:** Bina yoğunluğu = (Σ scope1 + Σ scope2_location) tCO₂ ×1000 / Σ alan = kg/m²/yıl. Vs `gold_crrem_pathway` (zaten Scope 1+2). Gap>0 = pathway üstünde = stranded.
- **Neden:** Eski ölçü Scope-2-only'di → Scope 1'i (gaz) dışlıyor → stranding'i AZ gösteriyordu. CRREM Scope 1+2 tanımlı; karşılaştırma elma-elmaya olmalı. (Scope 3 CRREM'e DAHİL DEĞİL — onu katma.)
- **Görsel nasıl okunur:** Bina çizgisi pathway eğrisini hangi yıl keser = "stranding year". Çizgi pathway'in üstündeyse bina BUGÜN stranded.
- **tr ipucu:** "Stranding'i nasıl hesaplıyorsun?" → *"Scope 1+2 carbon intensity against the CRREM 1.5°C decarbonisation pathway for that asset type and country; the cross-over year is the stranding year."*

## 4.5 EUI & iklim düzeltmesi (B1 — uygulanacak)
- **Nasıl (doğru):** `EUI_adj = EUI × (referans(HDD+CDD) / gerçek(HDD+CDD))`. Hem ısıtma hem soğutma derece-günü. Yıllık birim (kWh/m²/yıl) ile benchmark.
- **Neden:** Mevcut kod sadece `EUI/HDD` yapıyor (CDD yok, ratio değil) → soğutma-ağırlıklı bina (DC, güney) yanlış normalize. EnPI/ISO 50001'in tam sorduğu şey bu.
- **Görsel nasıl okunur:** İklim-düzeltilmiş EUI, soğuk ve ılıman binaları ADİL kıyaslar; ham EUI yerine bunu benchmark'la.
- **tr ipucu:** *"EnPI normalised for HDD and CDD per EN ISO 15927-6 — so a Berlin and an Istanbul building are comparable."*

## 4.6 Batarya ROI — payback / NPV / IRR (okuma rehberi)
- **Nasıl:** NPV = enflasyon-düzeltilmiş yıllık tasarruf + salvage, %5 iskonto, 10 yıl. IRR = NPV'yi sıfırlayan oran (Newton-Raphson). Payback = net CAPEX / yıllık tasarruf.
- **Düzeltilecek (I3):** tasarruf her deşarjı PEAK fiyatla değerlememeli; demand-saving peak-kW bazlı olmalı — yoksa NPV/IRR şişer, diligence'ta düşer.
- **Görsel nasıl okunur:** IRR > iskonto (%5) ise yatırım değer üretir. Payback < garanti süresi (10 yıl) olmalı. EU 2023/1542 bayrağı kırmızıysa o batarya AB'de satılamaz → senaryodan çıkar.
- **tr ipucu:** CFO'ya *"IRR above your hurdle rate, payback inside warranty, and only EU-2023/1542-compliant chemistries in scope."*

---

# 5. Paketleme & fiyatlandırma — sayfa hazırlığına bağlı

> İlke: sadece denetimi geçecek şeyi sat; Sayfa 6 düzelmeden "auditable/ESRS-ready" deme.

| Paket | Hangi sayfalar | Durum | Açılış fiyatı → sonra |
|---|---|---|---|
| **P2 — Building Energy KPI** | 1-5 (özellikle uyumluluk motoru) | Ref-wiring + anomali sonrası **satılabilir** | €1.800 → €2.500 |
| **P1 — CSRD Scope 1/2/3 Quickstart** | 6 | Çekirdek bitti; D4 + Fabric deploy sonrası **"CSRD-grade"** denebilir. Önce "Scope 1/2 screening" olarak sat | €3.200 → €4.500 |
| **P3 — Fabric Audit & Roadmap** | — | **Şimdi hazır** (saf danışmanlık) | €1.200 → €1.800 |
| **P4 — Power BI Tune-up** | — | **Şimdi hazır** | €800 → €1.200 |

- **Tier eşlemesi (uygulamadaki gibi):** Tier 1 *Insight* → P2 sayfaları; Tier 2 *Monitor* → +Sayfa 7/8 (Sayfa 8'i "live" demek için statik IoT snapshot şart); Tier 3 *Copilot* → +Sayfa 9 (batarya pipeline I4 netleşince).
- **Saatlik/günlük:** Malt €450/gün, €60/saat açılış — piyasanın hafif altı, freelance planıyla uyumlu. **Kısıtlayan fiyat değil, iddia:** Sayfa 6 düzelmeden "auditable" deme.
- **Farklılaştırıcı cümle (her proposal):** *"Fabric + EU energy regulation + auditable Scope 1/2/3 with year-matched, sourced emission factors and row-level lineage."* Artık bu cümle GERÇEK (ref katmanı + 09 refactor).

---

# 6. Phase-3 PDF'e giden yol

Tüm sayfalar "Final" (Bölüm 2 DoD ✓) olduğunda:
1. Bölüm 2 (DoD) + Bölüm 4 (metodoloji) birleştirilir.
2. Her sayfa için TÜM görsellerin tam anlatımı eklenir (Sayfa 6 şablonu Bölüm 4'te hazır).
3. `pandoc + xelatex` ile tek PDF üretilir (Master Study Guide gibi).
4. Çıktı: müşteriye verilebilir metodoloji eki + senin ezber referansın.

> **tr:** Bu doküman o PDF'in iskeleti. Her düzeltme indikçe buraya "✅ + nasıl okunur" ekliyoruz; sonunda PDF tek komutla çıkıyor. Yanlış (yarı-düzeltilmiş) durumu PDF'lemek yerine, doğru duruma göre üretiyoruz.

---
# 7. Oturum kapanışı (2026-05-30) — kod tarafı bitti + kalan manuel

## 7.1 Bu oturumda KOD tarafında biten (hepsi grep/py_compile teyitli)
- **Referans katmanı** `notebooks/reference/03_ref_factors_tariffs_loader.py` — yıl-indeksli, kaynaklı (UBA/IEA/Eurostat/DEFRA).
- **Motorlar ref'e bağlandı:** `09` (GHG: Scope1/2/3, market-based S2, screening S3), `03` (EF yıl-indeksli + ülke-tarife + climate_adjusted_eui B1), `05` (gaz F2), `06` (tarife F3), `12` (fiyat+CO₂ I2 → battery TR=450 bitti).
- **Sayfa 6 DAX** `69_dax_v57_page6_audit_fixes.dax` — EPC area-weighted (L2), CRREM Scope1+2 (L3), EU Taxonomy Carbon Score + CSRD Disclosure Readiness % (F1).
- **Anomali tek-motor** (C1) — `03` §8 artık `gold_anomaly_log_kpibuiltin_legacy`'ye; `gold_anomaly_log` = `anomaly_detection.py` (tek otorite).
- **Sayfa 7 G2** — `11` system_label + renovation_reason TR→EN (İngilizce-UI).
- **Sayfa 9 I3** — `12` ROI gerçekçi: strateji-farkında displaced-rate + peak-kW bazlı demand saving.
- **Saatlik mekanizma** `70_dax_v58_hourly_granularity.dax` + `report-design/hourly-granularity-build-guide.md` — öksüz `gold_kpi_hourly` devreye, Time Grain toggle (AYLIK=Date[YearMonth]) + 24h profil, Sayfa 1/2/3/4/7.
- **Açık-kaynak API loader'ları:** `ingestion/02_openmeteo_weather_loader.py` (anahtarsız hava→HDD/CDD), `03_entsoe_price_loader.py` (resmi AB fiyat→ref, token gerek), `05_electricitymaps_co2_loader.py` (canlı grid CO₂, operasyonel-only, token gerek).

## 7.2 Senin Fabric/PBI tarafında ÇALIŞTIRMAN gerekenler (kod hazır, run lazım)
1. Fabric'te sırayla: `03_ref_factors_tariffs_loader` → `09` → `03` → `05/06/12` → `11`.
2. `02_openmeteo_weather_loader` (hava). Token alınca: `03_entsoe` (fiyat), `05_electricitymaps` (CO₂).
3. PBI: **`gold_kpi_hourly[date]→Date[Date]` ilişkisini kur** (saatlik toggle anahtarı); `v57`+`v58` ölçülerini yükle; toggle/24h görselleri ekle (build guide).
4. `gold_kpi_daily`: `hdd_normalized_eui`→`climate_adjusted_eui` — eski adı kullanan DAX varsa güncelle.

## 7.3 Kalan MANUEL / karar gerektiren (kod değil)
- **DAX konsolidasyon (L1):** 68 `.dax` patch → tek otoriter TMDL/semantic model (Git). PBI/Tabular Editor işi. `v57`/`v58` bu konsolidasyonun çekirdeği; base `02_dax_measures`'ın bozuk CRREM kolon refleri (`pathway_kgco2_m2_yr`) silinmeli.
- **Demo-data tekleştirme (A4/I1):** B003 (Vienna Hotel? Hamburg Logistics?) ve B005 (Berlin Healthcare? Frankfurt Klinikum?) notebook'lar arası çelişiyor. **Karar senin:** tek kanonik bina kayıt defteri belirle → `sample-data/generators` + notebook yorumları + `02_openmeteo` CITY_COORDS hizalansın.
- **D4 refrigerant Scope 1 (opsiyonel):** veri yok (silver_refrigerant_log). Hazır kalıp: `09`'a ekle →
  `scope1_refrigerant_tco2 = kg_recharged × GWP / 1000` (R-410A GWP≈2088, R-32≈675), `scope1_total`'a ekle. Study guide'ın "refrigerant leaks are Scope 1" hamlesini gerçek kılar.

## 7.4 Live-API stack durumu
- Hava (Open-Meteo): ✅ anahtarsız, çalışır. Satışta DWD (resmi) swap.
- Fiyat (ENTSO-E): ✅ loader hazır, **ücretsiz token** (transparency.entsoe.eu) sende. TR için EPİAŞ ayrı (`04_exist_price_loader` — sıradaki).
- Canlı CO₂ (ElectricityMaps): ✅ loader hazır, **ücretsiz token** (electricitymaps.com). Sadece operasyonel; disclosure faktörü yıllık-resmi kalır.

---
*Güncelleme: 2026-05-30 (oturum 2) — Tüm motor ref-wiring + Page6 DAX + C1 + G2 + I3 + saatlik mekanizma + 3 API loader BİTTİ. Sıra: Mert Fabric'te çalıştırıp test → birlikte uygulama planı. Kalan manuel: DAX konsolidasyon, demo-data, D4.*
