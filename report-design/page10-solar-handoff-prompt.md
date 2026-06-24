# Continue: EnergyLens — Report Finalization, Page 10 (Solar) onward

Bu dosyayı YENİ bir konuşmanın ilk mesajı olarak yapıştır. Proje hafızası
([[report-finalization-2026-06-22-page9]], [[session-2026-06-16-solar-scada]],
[[solar-initiative]], [[report-finalization-2026-06-18]], [[feedback-edit-file-directly]],
[[feedback-fabric-schema-lakehouse]], [[feedback-cowork-file-sync]]) method + verified
eşikleri + gotcha'ları otomatik yükler — bu prompt seni yönlendirir.

## Neredeyiz
Embedded 10-sayfa Power BI raporunun (semantic model `EnergyCopilotModel`, DirectLake)
sayfa-sayfa GATED finalizasyonu. Method Page 1–9 ile birebir aynı.

* **APPROVED:** Page 1 Portfolio · 2 Building Detail · 3 Anomalies · 4 Forecast ·
  5 Occupancy · 6 Sustainability · 7 HVAC · 8 IoT · **9 Battery**.
  - Page 9 kök defekt çözüldü: sim savings = `anchor×heuristik faktör` (dispatch'ten
    kopuk) + 25yr/35% cap lipstick → **nb16 `16_gold_battery_simulation_v3_honest.py`**
    honest rebuild (Measured = 3 kurulu bina gerçek dispatch / Modeled = bina-bazı fizik /
    Prospect = bataryasız), `data_basis` kolonu, cap YOK, enerji-param review-surface.
    EU 2023/1670→**1542**. Arbitrage paneli 3.3yr-kümülatif→**yıllık €61k**. Payback kartı
    MINX cherry-pick (sahte 1.5)→**installed-strategy avg 4.1**. Doğrulandı: model measured
    B003 peak'i ~%4 ile yeniden üretti; reframe için legacy `pv_sc_adjustment`+`strategy_factor`
    kolonları geri eklendi (yoksa DirectLake "cannot access source column" verir).
* **Page 9 KALAN (bloklamaz, kozmetik):**
  1. **`data_basis` rozeti tabloda yok** — Wien + Amsterdam PROSPECT (batarya YOK), B007 Modeled.
     Rozet olmadan tablo 6 binanın da bataryası varmış gibi görünüyor (dürüstlük boşluğu).
     Kolon Delta'da var; Data panelinde görünmezse DirectLake yeni kolonu almamış → Service'te
     model refresh, gerekirse kolonu modele manuel ekle. Koşullu biçim: Measured yeşil / Modeled
     amber / Prospect gri.
  2. B001 adı raporda ASCII "Buerogebaeude" görünüyor — nb16 düzeltildi (umlaut), **yeniden
     çalıştırınca** "Bürogebäude" gelir.
* **SIRADAKİ: Page 10 Solar.** Bitince → **dokümantasyon** (aşağıda SON İŞ).

## Method (Page 1–9 ile aynı)
1. Mert her sayfanın ekran görüntüsünü atar (Claude PBI render edemez).
2. Claude `semantic-model/measures_dump.txt` + DAX + `web-app/frontend/lib/config/reportPages.ts`
   okur ve HER sayıyı Supabase mv_* (proje `vuiqfaklvlbushkiapnp`) ile doğrular — "probably" YOK.
3. Fix yeri:
   * MODEL measure → Tabular Editor C# script (`semantic-model/scripts/`, NO LINQ, foreach
     upsert, idempotent). F5 + Ctrl+S (F5 tek başına YAZMAZ) → PBI Desktop Refresh.
   * REPORT-LEVEL measure (dump'ta YOK; "report measure") → TE DEĞİL, PBI Desktop report-view
     formül çubuğu.
4. Gold değişirse: Fabric notebook (catalog-first `spark.table`! flat `Tables/` = bayat kopya) →
   değişikliği DOĞRUDAN repo dosyasına göm (heredoc + assert + py_compile + null-check), Mert
   Fabric'e kopyalar. MERGE absent-row SİLMEZ → `DeltaTable.delete()`. Sonra mv tazele → SQL doğrula.
5. **DirectLake reframe gotcha (Page 9'da yaşandı):** yeni Delta kolonu + `overwriteSchema`,
   modelin SİLDİĞİN bir kolonu hâlâ referans ettiği durumda reframe'i kırar → eski frame'e düşer.
   Notebook'tan kolon çıkarırken modelin o kolonu referans etmediğinden emin ol; live-connected
   rapor "Refresh" sadece görseli tazeler, **modeli reframe etmez** → Service'te
   `EnergyCopilotModel → Refresh now`.

## Veri durumu (Page 10 = Solar)
* **Kaynak:** `gold_solar_daily` (gerçek telemetri rollup — Supabase'de mv mevcut, ~720 satır) +
  `gold_kpi_daily`/`mv_kpi_daily` (solar kolonları: generation_kwh, PR, self-consumption, export) +
  `gold_kpi`/solar PR measure'ları. İşleme: `*solar*` notebook'ları, `03_gold_kpi_engine` solar
  bölümü, `solar_telemetry_rollup` / `run_solar_rollup`. Measure folder'ları: measures_dump'ta
  "Solar" / "Page 10" ara; reportPages slug **"solar"**.
* **Companion eşikleri (reportPages.ts, ÜRÜN-ONAYLI):** PR sağlıklı **0.75–0.85** · <0.70 fault
  (gölge/kir/inverter) · **>1.0 = sensör/veri hatası, gerçek üretim DEĞİL** · self-consumption
  export'tan değerli · specific yield DE **900–1050 kWh/kWp** · generation irradiance'ı takip etmeli.
* **BİLİNEN gotcha'lar — mutlaka kontrol et:**
  - **PR>1 artefakt:** gold'da `PR_MAX_PLAUSIBLE` clamp uygulandı ama notebook 03 re-run
    gerekebilir; canlıda hâlâ PR>1 satır var mı SQL ile bak (`mv_kpi_daily`/`gold_solar_daily`).
    Geçici backend guard mevcut. PR>1 = ENERJİ-imkânsız → kök düzelt, görsel clamp değil.
  - **mv scope orphan:** master 10 bina vs kpi 14 (B012–B015 test) → her solar görselinde
    (Blank) riski; building filtresi / REMOVEFILTERS kontrol.
  - **gen-weighted PR:** portföy PR'ı düz ortalama DEĞİL, üretim-ağırlıklı olmalı (küçük sistemler
    PR'ı şişirmesin).
  - **yield-gating:** düşük irradiance günlerinde PR güvenilmez → düşük üretim günlerini ele/işaretle.
  - **kısmi-yıl 2026:** trend annualize/guard (Page 6/7/8'de yaşandı).
* **Roster:** B001–B010 (B011–B015 test, master'da YOK → (Blank) kontrol). Hangi binalarda PV var
  `gold_kpi`/`silver_building_master`'dan doğrula (solar olmayan bina = (Blank) riski).

## 4-eksen teşhis (her sayfa)
Enerji (PR/yield fiziksel sanity, >1 imkânsız, yield bandı) · Veri (mv scope 10-vs-14,
flat-vs-dbo catalog-first, kısmi-yıl) · Tasarım (agregasyon/cross-filter, "Annual" etiketi,
gen-weighted) · App↔Rapor (reportPages companion hizası + /solar sayfasıyla tutarlılık).

## Çalışma kuralları
Chat TR, app/docs EN. Danışman tonu, rahatsız gerçeği önce, [Kesin]/[Muhtemel]/[Tahmin]
etiketleri, övgü dolgusu yok. Kod değişikliğini DOĞRUDAN repo dosyasına göm (heredoc/Write +
py_compile + null-check); Mert dosyadan Fabric/PBI'a kopyalar — find/replace talimatı VERME.
Edit/Write-overwrite mount'ta truncate/null-pad → YENİ dosya Write temiz; düzeltme = bash heredoc +
`wc`/`tail`/null-check. Supabase MCP READ-ONLY (proje `vuiqfaklvlbushkiapnp`). Nerede:
Fabric=notebook · Tabular Editor=.cs MODEL measure · PBI Desktop=görsel + report-level measure ·
Supabase=Claude doğrular.

## Başla
Mert'ten Page 10 (Solar) ekran görüntüsünü iste (tüm binalar + bir solar'lı bina seçili).
measures_dump'tan solar measure'larını + reportPages "solar"ı oku, `gold_solar_daily` +
`mv_kpi_daily`'i SQL ile doğrula, PR>1 / yield bandı / self-consumption vs export / mv-scope /
gen-weighted PR'ı 4-eksende teşhis et, fiziksel-doğru fix öner (kök çözüm; lipstick clamp değil).
`/energy-insight-generator`  `/energy-kpi-designer`

---

## SON İŞ — Teknik Dokümantasyon (Page 10 + TÜM rapor finalizasyonu BİTTİKTEN sonra)
**Mert'in isteği (2026-06-22):** Tüm 10 sayfa + her görsel için **İngilizce teknik dokümantasyon**.
- **İçerik:** her sayfa/görselin (a) hesaplama yöntemi/formülü, (b) varsayımlar + eşikler,
  (c) veri kaynağı (gold tablo + measure adı), (d) enerji mantığı — "this report is built on X,
  the calculation logic is Y". "Bu rapor neye göre hazırlandı" sorusuna tek referans.
- **Amaç:** (1) Mert'in kendi bilgisini tazelemesi, (2) app hakkında soru gelince gösterilecek
  decision-grade referans doküman.
- **Dil:** İngilizce. **Format:** profesyonel `.docx` (skill: `docx`) — istenirse `.md` özet de.
- **Kaynak:** her sayfanın `report_finalization_*` memory'leri + `measures_dump.txt` +
  notebook header'ları + reportPages companion eşikleri + onaylı varsayımlar (battery enerji
  params, residential ΔU×area×Gradtag÷η, GHG faktörleri DE 0.363 location/0.725 residual,
  EUI bantları Office 120–220 vs., MEPS EPC G 2030/F 2033, vb.).
- **Kapsam notu:** "Measured vs Modeled vs Prospect / synthetic vs real" dürüstlük katmanını
  açıkça yaz (reality-gap memory) — hangi sayılar gerçek-veri, hangileri tahmin/sentetik.
