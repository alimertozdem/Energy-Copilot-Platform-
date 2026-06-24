# Continue: EnergyLens — Report Finalization, Page 9 (Battery) onward

Bu dosyayı YENİ bir konuşmanın ilk mesajı olarak yapıştır. Proje hafızası ([[report-finalization-2026-06-22-page8]], [[page9-battery-strategy]], [[report-finalization-2026-06-18]], [[feedback-edit-file-directly]], [[feedback-fabric-schema-lakehouse]], [[feedback-cowork-file-sync]]) method + verified eşikleri + gotcha'ları otomatik yükler — bu prompt seni yönlendirir.

## Neredeyiz
Embedded 10-sayfa Power BI raporunun (semantic model **EnergyCopilotModel**, DirectLake) sayfa-sayfa GATED finalizasyonu. Method Page 1-8 ile birebir aynı.

- **APPROVED:** Page 1 Portfolio · 2 Building Detail · 3 Anomalies · 4 Forecast · 5 Occupancy · 6 Sustainability · 7 HVAC · **8 IoT** (freshness=event_date MAX + REMOVEFILTERS(sensor_location) live-ready; cost=gold_iot_fdd tek-kaynak, mv_iot_fdd doğrulandı C4 €81 bire bir; CO2 800/1500).
- **Page 8 ertelenen (bloklamaz):** 3 kozmetik — `page8_v5_zonecomfort_round.csx` (matris ROUND), `page8_v6_baseline_typical.csx` (baseline=tipik yük), PBI Desktop'ta ölü slicer sil + "Active Sensors"→"Active Zones" + chart başlık/legend ("Latest Day"→"Building & HVAC Power - recent (kW)", "Baseline"→"Typical"). Bunlar bittiyse Page 8 tam kapalı.
- **SIRADAKİ: Page 9 Battery** (ROI absürt — bilinen) → 10 Solar. Biri biterken "approved" demeden sonrakine geçme.

## Method (Page 1-8 ile aynı)
1. Mert her sayfanın ekran görüntüsünü atar (Claude PBI render edemez).
2. Claude `semantic-model/measures_dump.txt` + DAX + `web-app/frontend/lib/config/reportPages.ts`'i okur ve HER sayıyı Supabase mv_* (proje **vuiqfaklvlbushkiapnp**) ile doğrular — "probably" YOK.
3. Fix yeri:
   - **MODEL measure** → Tabular Editor C# script (`semantic-model/scripts/`, NO LINQ, foreach upsert, idempotent). F5 **+ Ctrl+S** (F5 tek başına yazmaz!) → PBI Desktop Refresh.
   - **REPORT-LEVEL measure** (dump'ta YOK; "report measure" der) → TE DEĞİL, PBI Desktop report-view formül çubuğu.
4. Gold değişirse: Fabric notebook (catalog-first `spark.table`! flat `Tables/` = bayat kopya) → değişikliği DOĞRUDAN repo dosyasına göm (heredoc + assert + py_compile + null-check), Mert Fabric'e kopyalar. MERGE absent-row SİLMEZ → `DeltaTable.delete()`. Sonra **mv_ tazele** → Claude SQL doğrular.

## Veri durumu (Page 9 = Battery)
- **Kaynak:** `gold_battery_dispatch` (charge_kwh, discharge_kwh, SoC, hourly/24h) + `gold_battery_simulation` (total_capex_eur, annual_savings_eur, payback, IRR). Muhtemelen `gold_battery_technologies` (EU 2023/1542 specs) + `gold_electricity_pricing` (EPEX, ülke-bazlı) de var. İşleme notebook'larını bul (`*battery*`).
- **Measure folder'ları:** "Battery 24h (V6)", "Page 9 / V2 Daily Flow", "Page 9 / V3". Örn. `V3 Payback Years Clean = DIVIDE(SUM(total_capex_eur), SUM(annual_savings_eur))` + cap `<=25`.
- **mv_ mirror:** Battery gold'ları Postgres'te muhtemelen YOK (Page 8'de mv_iot_fdd'yi sonradan ekledik). Doğrulamak için **canlı `50_materialize` notebook'unun `TABLES` sözlüğüne 1 satır ekle** (`"gold_battery_simulation":"mv_battery_simulation"` vb.) + `_pw` (.env DB şifresi) doldur → Run all → `_pgtype` tabloyu otomatik kurar. (Ayrı hücre/`materialize()` YAZMA — bu notebook TABLES-dict + _pgtype tabanlı; repo kopyası BAYAT.)
- **BİLİNEN ASIL DEFEKT:** ROI sanity bozuk — **payback ~230 yıl** ve aynı anda **IRR ~%450** (çelişkili: biri çok uzun, biri imkânsız kısa). Kök muhtemelen: annual_savings çok küçük/yanlış birim (günlük↔yıllık), ya da capex↔savings uyuşmazlığı, ya da battery-only ekonomisi (solar olmadan arbitraj zayıf). Önce `gold_battery_simulation`'dan capex/annual_savings/IRR'i mv ile doğrula, fiziksel mantığı kontrol et (€/kWh kurulum 140-180 DE; arbitraj kârı = günlük spread × döngü × 365).
- Battery yalnız BAZI binalarda (battery_soc verisi ~2 binada vardı); battery'siz binalarda Page 9 LOCKED (3-kat app access). Tek-bina screenshot'ı için battery'li bina seç.
- Companion eşikleri (reportPages.ts): charge off-peak/solar-fazla, discharge peak (fiyat eğrisine sarıl) · self-consumption (asıl değer arbitrajdan değil bunu yükseltmekten) · SoC sınırlar arası sağlıklı döngü · payback "indikatif, teklif değil".

## Roster (verified)
B001 Berliner Office DE · B002 Istanbul Retail TR · B003 Hamburg Logistics DE · B004 Wien Hotel AT · B005 Frankfurt Klinikum DE · B006 Amsterdam Education NL · B007 Copenhagen Office DK · B008 Leipzig Plattenbau DE · B009 Frankfurt Datacenter DE · B010 Stockholm Lab SE. **B011-B015 test (master'da YOK → (Blank) riski her grafikte kontrol).**

## Bilinen tuzaklar (her sayfada kontrol)
- **Canlı `50_materialize` ≠ repo kopyası:** canlı = `TABLES={...}` sözlüğü + `_pgtype` auto-create + `_pw` .env-hash gate (`assert _h=="80769b4860"`). Mirror eklemek = TABLES'a 1 satır + `_pw` doldur + Run all. Repo .ipynb eski per-cell pattern (bayat).
- **DirectLake datetime eşitliği (`col = MAX(timestamp)`) sessizce BLANK eder** → tarih eşitliği (`event_date = MAX(event_date)`) kullan. Bina-seviyesi kart = `REMOVEFILTERS(sensor_location/dim)`.
- **Supabase MCP READ-ONLY** (apply_migration çalışmaz) → tablo yaratmak = Supabase SQL Editor veya notebook _pgtype.
- **Edit/Write-overwrite mount'ta truncate/null-pad** → YENİ dosya Write temiz; düzeltme = bash heredoc + `wc`/`tail`/null-check.
- Flat-vs-dbo gold: catalog-first şart. Kısmi-yıl 2026 → trend annualize/guard. Report-level "Display"/badge measure'lar dump'ta YOK → PBI Desktop. SUMX context-transition sessiz BLANK → bina-bazlı non-SUMX tercih.
- Battery-spesifik: ROI/IRR/payback fiziksel sanity (negatif/absürd payback → BLANK/clamp veya kök düzelt, lipstick değil). Solar-battery etkileşimi (self-consumption).

## Çalışma kuralları
- Chat TR, app/docs EN. Danışman tonu, rahatsız gerçeği önce, [Kesin]/[Muhtemel]/[Tahmin] etiketleri, övgü dolgusu yok.
- Kod değişikliğini DOĞRUDAN repo dosyasına göm (heredoc/Write + py_compile/quote-paren-balance + null-check); Mert dosyadan Fabric/PBI'a kopyalar — find/replace talimatı VERME.
- Nerede: Fabric=notebook · Tabular Editor=.csx MODEL measure · PBI Desktop=görsel + report-level measure · Supabase=Claude doğrular.

## Başla
Mert'ten Page 9 (Battery) ekran görüntüsünü iste (tüm binalar + bir battery'li bina seçili). measures_dump.txt'ten battery measure'larını oku (folder: Battery 24h V6 / Page 9 V2 / V3), `gold_battery_simulation` + `gold_battery_dispatch`'i (gerekirse TABLES-dict ile mv'ye aynalayıp) doğrula, **ROI/payback/IRR absürtlüğünü** 4-eksende (enerji/veri/tasarım/app↔rapor) teşhis et, fiziksel-doğru fix öner (kök çözüm; lipstick clamp değil). /energy-insight-generator /energy-kpi-designer
