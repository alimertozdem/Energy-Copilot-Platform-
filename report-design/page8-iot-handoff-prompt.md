Continue: EnergyLens — Report Finalization, Page 8 (IoT) onward

Bu dosyayı YENİ bir konuşmanın ilk mesajı olarak yapıştır. Proje hafızası
([[report-finalization-2026-06-21-page7]], [[page8-eventstream-architecture]],
[[report-finalization-2026-06-18]], [[feedback-edit-file-directly]],
[[feedback-fabric-schema-lakehouse]]) method + verified eşikleri + gotcha'ları
otomatik yükler — bu prompt seni yönlendirir.

## Neredeyiz
Embedded 10-sayfa Power BI raporunun (semantic model EnergyCopilotModel, DirectLake)
sayfa-sayfa GATED finalizasyonu. Method Page 1-7 ile birebir aynı.
* APPROVED: Page 1 Portfolio · 2 Building Detail · 3 Anomalies · 4 Forecast ·
  5 Occupancy · 6 Sustainability · **7 HVAC** (gold G1 rated-COP + G2 insulation
  recalib + G3 2023-drop · R1 CO₂ annualize 16.5k→7.1k · R2 heat-loss badge
  EPC→transmission-loss). Page 7 ertelenen opsiyonel: insulation "EPC D" prefix
  (kategori hatası), D1 V3 ekseni (heat-loss 138 clip).
* SIRADAKİ: **Page 8 IoT** (görseller KIRIK — bilinen) → 9 Battery (ROI absürt) → 10 Solar.
  Biri biterken "approved" demeden sonrakine geçme.

## Method (Page 1-7 ile aynı)
1. Mert her sayfanın ekran görüntüsünü atar (Claude PBI render edemez).
2. Claude semantic-model/measures_dump.txt + DAX + web-app/frontend/lib/config/
   reportPages.ts'i okur ve HER sayıyı Supabase mv_* (proje vuiqfaklvlbushkiapnp)
   ile doğrular — "probably" YOK.
3. Fix yeri:
   * MODEL measure → Tabular Editor C# script (semantic-model/scripts/, NO LINQ, foreach upsert).
   * REPORT-LEVEL measure (dump'ta YOK; hata mesajı "report measure" der) → **TE DEĞİL**
     (TE deploy hatasız geçer ama report measure'ı değiştirmez), **PBI Desktop report-view
     formül çubuğu**. DAX'ı yorumsuz / `=`-ayıraçsız ver — yorum başlığındaki ilk `=`
     measure-adı ayıracı sanılır, ad bozulur, görsel kopar.
4. Gold değişirse: Fabric notebook (catalog-first spark.table! flat Tables/ = bayat kopya)
   → değişikliği DOĞRUDAN repo dosyasına göm (heredoc + assert count==1 + py_compile +
   null-check), Mert Fabric'e kopyalar (notebook tek-hücre olabilir → en sona yeni hücre).
   MERGE absent-row SİLMEZ → satır kaldırmak için explicit DeltaTable.delete().
   Sonra 50_materialize loop'u → mv_ tazelenir → Claude SQL doğrular.

## Veri durumu (Page 8 = IoT)
* Kaynak: gold_iot_realtime (Delta) + iot_hot_readings (KQL/Kusto) — diğer sayfalardan
  farklı, KQL+Delta hibrit. İşleme notebook: 11b_iot_processing / 11c_iot_fdd.
* mv_ mirror: **mv_iot_daily_summary (1076 satır)** Postgres'te. Realtime/KQL tarafı
  mv_'de OLMAYABİLİR → SQL doğrulama günlük-özetle sınırlı; gerekirse gold_iot_realtime'ı
  materialize (50_materialize loop'a satır ekle).
* **sensor_type DİMENSİON** (hardcoded değil) — her bina yalnız bağlı sensör tiplerini
  gösterir, görseller dinamik adapte olur. Min set: HVAC_temp/humidity/CO2/building_kwh/
  hvac_kwh. Genişletilmiş: supply/return temp, lighting/plug sub-metering, chiller_cop vb.
* IoT yalnız BAZI binalarda; IoT'suz binalarda Page 8 LOCKED (3-kat app access model).
* Companion eşikleri: CO₂ 800/1500 ppm (good/fair/poor) · comfort 20-24°C · real-time
  power baseline'a karşı green/amber/red · zone setpoint compliance · sensor uptime.
* Anomali maliyet (CLAUDE.md, HEP "Est." göster): cost_eur = duration_h × power_waste_kW
  × grid_price (DE €0.20 / TR €0.14/kWh). HVAC_temp sapması 2-5 kW/°C; CO2>1500ppm 1-3 kW;
  power spike >%120 baseline = fiili fazla kW.

## Roster (verified): B001 Berliner Office DE · B002 Istanbul Retail TR · B003 Hamburg
Logistics DE · B004 Wien Hotel AT · B005 Frankfurt Klinikum DE · B006 Amsterdam Education
NL · B007 Copenhagen Office DK · B008 Leipzig Plattenbau DE · B009 Frankfurt Datacenter DE ·
B010 Stockholm Lab SE. B011-B015 test (master'da YOK → (Blank) riski her grafikte kontrol).

## Bilinen tuzaklar (her sayfada kontrol)
* Flat-vs-dbo silver/gold: notebook Tables/<t> flat okursa bayat kopya; catalog-first şart.
* Kısmi-yıl 2026 (4 ay) → trend görselleri son yılda çöker → annualize/guard (measure-level).
* Report-level "Display"/badge measure'lar dump'ta YOK; PBI Desktop'ta düzenlenir, TE'de DEĞİL.
* IoT-spesifik: KQL tablosu (iot_hot_readings) Postgres'te YOK → SQL doğrulama
  mv_iot_daily_summary / gold_iot_realtime ile sınırlı. Realtime "şu an" sayıları
  doğrulanamayabilir → günlük agregada sanity-check.
* SUMX context-transition bu modelde sessizce BLANK dönebilir → bina-bazlı non-SUMX tercih.

## Çalışma kuralları
* Chat TR, app/docs EN. Danışman tonu, rahatsız gerçeği önce, [Kesin]/[Muhtemel]/[Tahmin]
  etiketleri, övgü dolgusu yok.
* Kod değişikliğini DOĞRUDAN repo dosyasına göm (heredoc + py_compile + null-check); Mert
  dosyadan Fabric'e/PBI'a kopyalar — find/replace talimatı VERME. .csx/.dax için Write +
  bash quote/paren balance doğrula. YENİ dosya Write temiz; Edit/Write-overwrite mount'ta truncate.
* Nerede: Fabric=notebook · Tabular Editor=.csx MODEL measure · PBI Desktop=görsel +
  report-level measure · Supabase=Claude doğrular.

Başla: Mert'ten Page 8 (IoT) ekran görüntüsünü iste (tüm binalar + bir IoT'lu bina seçili),
measure'larını measures_dump.txt'ten oku, gold_iot_realtime / mv_iot_daily_summary'i mv_'den
doğrula, kırık görselleri 4-eksende (enerji/veri/tasarım/app↔rapor) teşhis et, fix öner.
/energy-insight-generator /energy-kpi-designer
