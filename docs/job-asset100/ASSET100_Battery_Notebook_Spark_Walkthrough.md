# Battery Notebook & Spark/Fabric Walkthrough — ASSET.100 Interview Prep

**For:** Ali Mert Özdemir · Interview 2026-08-03 · ASSET.100 (Ref. 36468, Soorce GmbH, via Arbeitnehmerüberlassung)
**Companion to:** `docs/job-asset100/ASSET100_Interview_Prep_Kit.docx` and `ASSET100_Technical_Learning_Roadmap.docx`
**Source code:** `notebooks/_deferred/page9-battery/12,13,14,15,16,16c*.py` (EnergyLens repo)
**Language note:** Written in English (interview language) with Turkish explanations (*TR:*) under each concept, so you can study it solo and still say it correctly in English on Monday.

---

## 0. Read this first — three corrections before you study

**0.1 — This interview does not test battery knowledge.**
ASSET.100 is a grid-operator (Netzbetreiber) data platform project: unifying metering data, GIS, and asset-management systems on MS Fabric. Nobody there is going to ask you about depth-of-discharge or round-trip efficiency. The battery notebook is valuable here only as **evidence of Fabric/PySpark competence and data-quality judgment** — the same evidence your existing Interview Prep Kit already points to in questions S1 (ETL/ELT), S5 (data quality/governance), S8 (Fabric internals), S9 (SQL). Use it to answer those questions with a real, specific story instead of a generic one. Don't volunteer "let me tell you about battery dispatch strategies" — that's solving the wrong problem in the room.
*TR: Bu mülakat batarya bilgini ölçmüyor. ASSET.100 bir şebeke işletmecisi (Netzbetreiber) projesi — ölçüm verisi, GIS ve varlık yönetimi sistemlerini Fabric'te birleştirmek. Battery notebook'u burada değerli olma sebebi "batarya uzmanlığı" değil, "gerçek, somut bir Fabric/PySpark mühendislik hikâyem var" ispatı olması. Zaten mevcut Interview Prep Kit'indeki S1/S5/S8/S9 sorularına somut kanıt sağlamak için kullan; sohbeti kendiliğinden "battery stratejileri" konusuna çekme.

**0.2 — Production status: be precise if asked "is this live?"**
Two separate, true facts — know both so a follow-up question can't corner you:
- The Page-9 battery cluster (notebooks 12–16, the ones in this guide) was **quarantined out of the automated batch pipeline** on 2026-06-15 (see `docs/audit/notebook-cleanup-2026-06-15.md`) because an earlier version produced implausible ROI. It now lives in `notebooks/_deferred/page9-battery/` and is run **manually**, not on a schedule. The most recent manual run (notebook 16, 2026-06-22) fixed the root cause and was verified against live data — so the code is real and the fix is real, but the refresh is currently manual, not automated.
- Separately, there **is** a live, pipeline-wired notebook, `notebooks/simulation/04_simulation_engine.py`, part of `03_gold_analytics_pipeline`, which models battery storage as one of three investment scenarios (heat pump / battery / envelope insulation) feeding a general recommendation engine. That one runs on the automated schedule.
So: "have you built battery dispatch simulation logic in Fabric?" → yes, confidently. "Is the Page-9 battery report auto-refreshing in production right now?" → honestly, no — it's manually maintained pending a follow-up fix, and there's a separate always-on battery-scenario notebook that is production-scheduled. Saying this precisely, instead of a blanket "yes it's all live," is exactly the kind of answer that reads as senior judgement, not evasion.
*TR: "Bu canlı mı" diye sorulursa iki ayrı gerçek var. Page-9 battery notebook kümesi (12-16) 15 Haziran'da otomatik pipeline'dan çıkarılıp karantinaya alındı (implausible ROI yüzünden), şu an elle çalıştırılıyor — son çalıştırma (nb16, 22 Haziran) kökten düzeltme yaptı ve canlı veriyle doğrulandı, ama otomasyon değil, manuel. Ayrı olarak, gerçekten pipeline'a bağlı, otomatik çalışan `04_simulation_engine.py` var — o da batarya senaryosu üretiyor ama farklı bir tabloya, farklı bir amaç için (genel yatırım önerisi motoru). "Hepsi canlı" demek yerine bu ayrımı net yapmak, kaçamak değil kıdemli mühendis cevabı gibi durur.

**0.3 — Don't reuse the battery numbers from `EnergyLens_Master_Study_Guide.md`.**
That document's Page-9 section (12 countries × 8 chemistries × 7 strategies = 672 rows) describes a larger, aspirational spec that does **not** match the code that actually runs. The real notebooks operate on 6–7 buildings, 4 strategies (peak-shaving, self-consumption, time-of-use, backup), and 2 chemistries in active use (LFP, NMC — NCA exists only in the unused reference catalog). Section 8 of this guide has the verified numbers. If asked for specifics, use those, not the Master Study Guide's.
*TR: `EnergyLens_Master_Study_Guide.md`'deki battery sayıları (12 ülke, 8 kimya, 672 satır) gerçek kodla uyuşmuyor — o daha büyük, planlanan ama uygulanmamış bir spec'i anlatıyor gibi görünüyor. Gerçek kod 6-7 bina, 4 strateji, 2 aktif kimya (LFP/NMC) üzerinde çalışıyor. Sayı sorulursa bu dokümanın 8. bölümündeki (koddan doğrudan okunmuş) rakamları kullan.

---

## 1. The 30-second pitch

**English (say this):** "I built a gold-layer Spark pipeline in Microsoft Fabric that turns raw 15-minute battery, solar, and consumption meter readings into three production tables: a daily dispatch table with physics- and tariff-based savings, a financial scenario-comparison table with NPV/IRR/payback per building and strategy, and a cumulative-KPI summary table that feeds a Power BI report. It uses the standard bronze→silver→gold pattern, joins against reference tariff and emissions-factor tables, and — this is the part I'm proudest of — I later found and fixed a case where the financial output had quietly decoupled from the real underlying data, and rebuilt it to be transparent about what's measured versus modeled."

*TR: Bu senin "tek cümlelik özün" — mülakatın en başında ya da "bana bir proje anlat" dendiğinde kullanacağın anlatı. Ham 15 dakikalık sayaç verisini üç production tablosuna dönüştüren bir gold-layer Spark pipeline kurdun: günlük dispatch tablosu (fizik + tarife bazlı tasarruf), finansal senaryo karşılaştırma tablosu (NPV/IRR/geri ödeme), ve kümülatif KPI özeti. Standart bronze→silver→gold deseni, referans tablolarla join, ve en güçlü kısım: sonradan finansal çıktının gerçek veriden kopmuş olduğunu fark edip düzelttin — bunu Bölüm 4'te STAR formatında detaylı yazdım.

---

## 2. Pipeline map (what feeds what)

```
RAW (15-min interval readings, via CSV-fallback or bronze tables)
  bronze_battery_status, bronze_solar_generation, bronze_energy_readings
  silver_building_master, ref_electricity_tariffs, ref_grid_emission_factors
        │
        │  nb 12 — daily aggregation (groupBy building_id, date)
        ▼
  gold_battery_dispatch            1 row = building × date × strategy
  (real physics: SoC, charge/discharge kWh, round-trip efficiency,
   cost avoided, demand-charge reduction, CO2 avoided, battery health/SoH)
        │
        ├──▶ nb 12 (superseded) / nb 14 (flawed) / nb 16 (honest, current) ──▶
        │        gold_battery_simulation      1 row = building × strategy
        │        (CAPEX, annual savings, payback, NPV, IRR, comparison score,
        │         data_basis = Measured / Modeled / Prospect)
        │
        └──▶ nb 12 step 6 ──▶ gold_battery_daily_summary
                 (best strategy per day + running cumulative totals)

  gold_battery_hourly_profile (nb 13, synthetic reference curves — 4 strategies × 24h = 96 rows)
        │
        │  nb 15 — scale generic curves by each building's real daily kWh volumes
        ▼
  gold_battery_hourly_dispatch (480 rows: 5 buildings × 4 strategies × 24 hours)
```

*TR: Bu, tüm pipeline'ın haritası. Ham veri → günlük dispatch (gerçek fizik) → finansal senaryo tablosu (nb16 en güncel/doğru versiyon) → günlük özet. Ayrıca saatlik profil (nb13, jenerik eğri) → nb15 ile bina-özel gerçek kWh'ye ölçeklenmiş saatlik tablo. Mülakatta "pipeline'ını çiz" dendiğinde tam bunu kağıda çizebilmen lazım.

---

## 3. Notebook-by-notebook walkthrough

### 3.1 — Notebook 12: `12_battery_dispatch_and_simulation.py` (the foundation)

**What it does:** Reads raw battery/solar/consumption readings, aggregates to daily grain, joins against country-level tariff and grid-CO2 reference tables, computes per-building-per-day dispatch economics, then (in its later, now-superseded section) built the first version of the financial scenario table.

**Key pattern 1 — self-contained fallback reads:**
```python
def read_table_or_csv(table_name: str, csv_path: str, **csv_opts):
    if table_exists(table_name):
        return spark.read.table(table_name)
    else:
        return spark.read.format("csv").option("header", "true")\
            .option("inferSchema", "true").options(**csv_opts).load(csv_path)
```
**English:** "I made the notebook independent of run-order — it tries the registered Lakehouse Delta table first, and falls back to a CSV in the Files section if that table hasn't been built yet. That means notebook 12 doesn't silently fail if notebooks 01/02 haven't run first; it degrades gracefully."
*TR: Bu, "önce Lakehouse tablosunu dene, yoksa CSV'ye düş" deseni. Notebook'u diğer notebook'ların çalışma sırasına bağımlı olmaktan kurtarıyor — bir upstream notebook henüz çalışmamışsa sessizce patlamak yerine CSV'den devam ediyor.

**Key pattern 2 — "latest row per group" with a window function:**
```python
_tar_latest = (
    spark.table("ref_electricity_tariffs")
    .withColumn("_rn", F.row_number().over(
        Window.partitionBy("country_code").orderBy(F.col("year").desc())))
    .filter(F.col("_rn") == 1)
)
```
**English:** "Pricing changes year to year, so the tariff reference table has multiple rows per country. I use `row_number()` over a window partitioned by country and ordered by year descending, then filter to rank 1 — that's the standard 'latest record per group' pattern, equivalent to a correlated subquery or `QUALIFY ROW_NUMBER()=1` in SQL."
*TR: Bir grup içinde "en güncel satırı seç" deseni — SQL'deki `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ... DESC)` ile birebir aynı. Fiyat tablosunda ülke başına birden fazla yıl satırı var; her ülke için en son yılı seçmek için kullanılıyor. Bu, mülakatta pencere fonksiyonu sorulursa vereceğin ilk örnek olsun.

**Key pattern 3 — broadcast join on small reference tables:**
```python
df_bldg_config = (
    df_building_p9.select(...)
    .join(F.broadcast(df_pricing), df_building_p9["country_code"] == df_pricing["country"], "left")
)
```
**English:** "`df_pricing` has one row per country — a handful of rows. Broadcasting it means Spark ships the whole small table to every executor instead of shuffling the much larger building/dispatch data across the cluster to do the join. It's a standard optimization for fact-to-small-dimension joins."
*TR: `df_pricing` ülke başına bir satır — çok küçük bir tablo. `broadcast()` ile bu küçük tabloyu her executor'a kopyalıyoruz, böylece Spark büyük dispatch verisini ağ üzerinden karıştırıp (shuffle) join yapmak zorunda kalmıyor. Küçük boyut referans/dimension tablosu + büyük fact tablosu join'lerinde standart bir performans optimizasyonu.

**Key pattern 4 — defensive null-safety with `coalesce` / `greatest` / `least`:**
```python
.withColumn("charge_kwh", F.greatest(F.lit(0.0), F.coalesce(F.col("charge_kwh_raw"), F.lit(0.0))))
```
**English:** "Sensor data can have nulls or, occasionally, small negative noise. `coalesce` gives a default for missing values, `greatest(0, x)` clamps out negative noise. I do this at the point the raw number enters a financial calculation, not later — bad inputs shouldn't produce a plausible-looking wrong euro figure downstream."
*TR: Sensör verisinde null ya da küçük negatif gürültü olabilir. `coalesce` eksik değere varsayılan veriyor, `greatest(0, x)` negatifi sıfıra kırpıyor. Bunu ham veri finansal hesaba girmeden HEMEN yapıyoruz — kirli veri sona kalırsa "mantıklı görünen ama yanlış" bir € rakamı üretir.

**Key pattern 5 — ranking to find a "winner" per group:**
```python
.withColumn("is_active_strategy",
    F.row_number().over(Window.partitionBy("building_id").orderBy(F.col("comparison_score").desc())) == 1)
```
**English:** "Same `row_number()` tool as pattern 2, different purpose: here it picks the highest-scoring strategy per building — a ranking, not a 'latest date' lookup. One window-function primitive, two everyday use cases."
*TR: Aynı `row_number()` aracı, farklı amaç: burada tarih değil, skor bazlı "en iyi stratejiyi" seçiyor. Tek bir pencere fonksiyonu deseni, iki farklı iş problemine uygulanıyor — bunu mülakatta vurgula, "aynı aracı nerede nasıl kullanırım" bilgisi güçlü bir sinyal.

**Key pattern 6 — running cumulative total (unbounded window):**
```python
window_cum = Window.partitionBy("building_id").orderBy("date").rowsBetween(Window.unboundedPreceding, 0)
df_daily_summary = df_best_strategy.withColumn(
    "total_cost_avoided_eur", F.sum("net_savings_eur").over(window_cum))
```
**English:** "This is a running total — for each building, sum everything from the first row up to the current row, ordered by date. `rowsBetween(unboundedPreceding, 0)` is what makes it cumulative instead of a plain group-level sum. This is the same shape as a running-balance or year-to-date calculation you'd write in SQL."
*TR: Kümülatif toplam — her bina için, ilk günden bugüne kadar olan tüm satırları topla. `rowsBetween(unboundedPreceding, 0)` bunu "grup toplamı" değil "yürüyen toplam" yapan kısım. SQL'de running balance / year-to-date hesaplarken yazacağın pencere fonksiyonuyla birebir aynı mantık.

**A documented trade-off you should be ready to explain — MERGE vs. OVERWRITE:**
```python
# 2026-06-06: OVERWRITE (not MERGE) so the V7 SoH columns reliably persist every run.
df_dispatch.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(DISPATCH_TABLE)
```
**English:** "The notebook header lists 'Delta MERGE upsert pattern' as the intended design, and I do import `DeltaTable` for that. In practice, this table's schema kept evolving as I added new columns (battery state-of-health, cycle counts), and Delta MERGE doesn't reliably pick up brand-new target columns — the write can silently drop them. I switched this specific table to a full overwrite with `overwriteSchema=true`, which guarantees the complete current schema lands every run. The trade-off is a full table rewrite instead of touching only changed rows — acceptable here because the table is small (thousands, not billions, of rows) and rebuilt from source each run anyway. On a genuinely large, incrementally-arriving fact table I'd go back to MERGE keyed on natural keys, or partition-overwrite by date."
*TR: Bu, mülakatta "MERGE mi overwrite mı kullanırsın" tipi bir soruya vereceğin en iyi cevap çünkü GERÇEKTEN yaşadığın bir karar. Notebook başlığı "MERGE upsert" diyor ama pratikte tabloya sürekli yeni kolon eklendikçe (battery health, cycle sayısı gibi) MERGE bu yeni kolonları güvenilir şekilde almadı — sessizce eksik bırakabiliyordu. Bu yüzden bu tabloda tam overwrite'a geçtin: her çalıştırmada güncel şemanın TAMAMI yazılıyor garantili. Bedeli: sadece değişen satırları değil, tüm tabloyu her seferinde yeniden yazmak — bu tabloda sorun değil çünkü küçük ve zaten kaynaktan yeniden inşa ediliyor. Gerçekten büyük, artımlı gelen bir fact tabloda MERGE'e ya da tarihe göre partition-overwrite'a dönerdin.

---

### 3.2 — Notebook 13: `13_gold_battery_hourly_profile.py` (reference curves)

**What it does:** Hand-authored, hourly (0–23h) charge/discharge/SoC reference curves for each of the four dispatch strategies, based on the shape of typical German EPEX day-ahead prices — not measured data, explicitly a modeled reference pattern (96 rows total: 4 strategies × 24 hours).

**English:** "This table is intentionally synthetic — it encodes domain knowledge (when does a peak-shaving battery charge vs. discharge, relative to the EPEX price curve) as data instead of hardcoding it into report logic. Building it in plain Python/pandas made sense here: 96 rows of hand-tuned reference values don't benefit from distributed compute — Spark is used only at the very end, to persist the table as Delta."
*TR: Bu tablo bilinçli olarak sentetik/uydurma değil, "tasarım bilgisi" — hangi stratejinin ne zaman şarj/deşarj yaptığını EPEX fiyat eğrisine göre veri olarak kodluyor, rapor mantığına gömmek yerine. Sadece 96 satır olduğu için düz Python/pandas ile yazıldı — dağıtık hesaplamanın (Spark'ın) hiçbir faydası olmaz bu ölçekte; Spark sadece en sonda, Delta'ya yazarken devreye giriyor. Bu "ne zaman Spark'a gerek yok" sezgisi, aşağıdaki Bölüm 5.6'da ayrıca ele alınıyor.

---

### 3.3 — Notebook 14: `14_gold_battery_simulation_v2.py` (know this exists — it's the "before" half of your best story)

**What it does:** A second attempt at the financial scenario table, built around one hardcoded "anchor" savings value per building (taken from real dispatch data) and fixed multiplier factors to derive the other three strategies.

```python
STRATEGY_RELATIVE_FACTORS = {
    "backup": {"backup": 1.00, "peak_shaving": 4.55, "tou": 3.91, "self_consumption": 3.27},
}
IRR_DISPLAY_CAP = 0.35  # cap the number instead of fixing what makes it unrealistic
```
**English:** "Don't lead with this one — it's the version I replaced. Its problem: multiplying one real number by a fixed factor doesn't track reality per building, and the hardcoded battery capacities in this file (e.g. 5,600 kWh for one building) didn't even match the 800 kWh in the real dispatch table for that same building. It papered over unrealistic outputs with a display cap (IRR shown as at most 35%) instead of fixing the underlying assumption. I keep this file because the fix (§4) is a better story with the 'before' visible."
*TR: Bunu mülakatta ÖNE ÇIKARMA — bu senin sonra değiştirdiğin, kusurlu versiyon. Sorun: bir gerçek sayıyı sabit bir katsayıyla çarpmak bina-özel gerçekliği yakalamıyor, üstelik bu dosyadaki hardcoded batarya kapasiteleri (örn. bir bina için 5.600 kWh) aynı binanın gerçek dispatch tablosundaki 800 kWh ile bile uyuşmuyordu. Ortaya çıkan gerçekçi-olmayan sayıları düzeltmek yerine bir "gösterim tavanı" (IRR en fazla %35 göster) ile üstünü örtmüş. Bu dosyayı sildirmedin çünkü Bölüm 4'teki düzeltme hikâyesi "öncesi" görünür olunca çok daha güçlü duruyor.

---

### 3.4 — Notebook 15: `15_gold_battery_hourly_dispatch.py` (building-specific hourly scaling)

**What it does:** Takes each building's real average daily charge/discharge kWh (from `gold_battery_dispatch`) and scales notebook 13's generic 0–1 hourly *rate* curves into real, building-specific kWh values per hour.

```python
pattern["charge_kwh"] = (pattern["charge_rate"] / max(sum_c, 0.001) * daily_charge).round(2)
```
**English:** "This is a normalize-then-scale pattern: divide each hour's rate by the sum of all hours' rates (so the hourly shares add to 1), then multiply by the building's real daily total. It turns 'a generic 0–1 curve' into 'Hamburg charges 1,120 kWh at 03:00 vs. Berlin's 40 kWh' — the same strategy shape, correctly scaled to each building's actual size."
*TR: "Normalize et, sonra ölçekle" deseni: her saatin oranını tüm saatlerin toplamına bölüp (saatlik paylar toplamı 1 olsun diye), sonra binanın gerçek günlük toplamıyla çarpıyorsun. Jenerik 0-1 eğrisini "Hamburg 03:00'te 1.120 kWh şarj ediyor, Berlin 40 kWh" gibi gerçek, bina-özel sayılara dönüştürüyor — aynı strateji şekli, doğru ölçekte.

**Worth noting honestly:** this notebook does the row-expansion in a plain Python `for` loop over `.collect()`'ed rows, not native Spark transformations. **English:** "The building × strategy grain here is only 20–30 rows, so I collect it to the driver and iterate in Python/pandas — it's simpler to read and there's no cluster-scale data to parallelize. If this needed to run over thousands of buildings I'd rewrite it as a proper Spark `join` + arithmetic column expression instead of a Python loop, to keep the work distributed."
*TR: Bu notebook satır genişletmeyi düz Python for-loop ile yapıyor, native Spark transformasyonuyla değil. Sebep: bina×strateji satır sayısı sadece 20-30 — sürücüye (driver) çekip Python'da dönmek daha okunaklı ve paralelleştirilecek büyüklükte veri yok. Binlerce bina olsaydı bunu gerçek bir Spark join + kolon ifadesine çevirirdim ki iş dağıtık kalsın. Bu ayrımı bilmen (ne zaman Spark, ne zaman düz Python) kıdem göstergesi.

---

### 3.5 — Notebook 16: `16_gold_battery_simulation_v3_honest.py` (the centerpiece — read Section 4 first)

**What it does:** Fully replaces notebook 14's approach. Every output row is labeled by a `data_basis` column: **Measured** (annualized from real dispatch, for the 3 buildings that actually have an installed, monitored strategy), **Modeled** (a from-scratch physics estimate for alternative strategies at a building that does have a battery), or **Prospect** (a physics estimate for a building with no battery installed at all). No display caps anywhere.

```python
def model_strategy(b, strat, p):
    usable = b["capacity_kwh"] * DOD[b["chem"]]
    spread = max(0.0, p["peak"] - p["off"])
    arbitrage = usable * CYCLES_PER_YR[strat] * spread * b["rte"]
    if strat == "peak_shaving":
        return b["power_kw"] * p["demand"] * 12.0 * COINCIDENCE + arbitrage
    if strat == "self_consumption":
        pv_surplus_kwh = b["pv_kwp"] * PV_YIELD * PV_SURPLUS_FRAC
        captured = min(pv_surplus_kwh, usable * CYCLES_PER_YR["self_consumption"])
        return captured * max(0.0, p["peak"] - p["feed_in"]) * b["rte"]
    ...
```
**English:** "Instead of one fixed multiplier, every 'Modeled' or 'Prospect' euro figure is derived from that specific building's own capacity, chemistry, PV size, and country tariff — usable energy × cycles-per-year × price spread × round-trip efficiency, with a demand-charge term added for peak-shaving and a PV-surplus term for self-consumption. It's a small, transparent physics model, not a black box."
*TR: Sabit bir katsayı yerine, her "Modeled" veya "Prospect" € rakamı o binanın kendi kapasitesinden, kimyasından, PV büyüklüğünden ve ülke tarifesinden türetiliyor — kullanılabilir enerji × yıllık döngü sayısı × fiyat farkı × round-trip verimlilik, artı peak-shaving için talep-ücreti terimi, self-consumption için PV-fazlası terimi. Küçük ama şeffaf bir fizik modeli, kara kutu değil.

**Notice what's *absent* compared to notebook 14:** no `IRR_DISPLAY_CAP`, no 25-year payback ceiling. **English:** "If a scenario genuinely has a 15-year payback, this version shows 15 years. Capping the number to look better is a data-integrity smell — I'd rather show an unattractive true number and explain it than show an attractive false one."
*TR: nb14'te olan `IRR_DISPLAY_CAP` ve 25 yıl geri ödeme tavanı burada YOK. Bir senaryo gerçekten 15 yılda geri ödüyorsa, bu versiyon 15 yılı gösteriyor. Sayıyı "daha iyi görünsün" diye kırpmak bir veri bütünlüğü kokusu — çirkin ama doğru sayıyı gösterip açıklamak, güzel ama yanlış sayı göstermekten iyidir. Bu cümleyi neredeyse birebir mülakatta söyleyebilirsin.

**Validation, inline, before writing:**
```python
assert sdf.count() == len(BUILDINGS) * len(STRATEGIES), "row count mismatch"
assert sdf.filter("annual_savings_eur < 0").count() == 0, "negative savings"
```
**English:** "Two cheap sanity assertions before the write: the row count matches what I expect structurally, and no savings figure is negative (which would indicate a sign error upstream). These aren't a test suite, but they catch an entire class of silent errors for almost no cost."
*TR: Yazmadan önce iki ucuz `assert`: satır sayısı beklenen yapıyla uyuşuyor mu, hiçbir tasarruf rakamı negatif değil mi (negatiflik bir yerde işaret hatası olduğunu gösterir). Bunlar bir test paketi değil ama neredeyse sıfır maliyetle koca bir hata sınıfını yakalıyor. Mülakatta "veri kalitesini nasıl sağlarsın" (Kit'teki S5) sorusuna somut örnek.

**Also worth mentioning — a real self-critique baked into the code as a comment:**
```python
# KNOWN ISSUE (flagged, deferred — Mert chose ship-faithful): Modeled/Measured peak+tou
# paybacks 1.6-2.7yr, IRR 40-64% = optimistic vs real BtM (8-18%). NOT invented — matches
# measured dispatch; optimism is inherited from the dispatch simulator's near-full-spread
# assumption. Proper fix = de-rate the dispatch generator itself (separate pass).
```
**English:** "I know this output still looks optimistic compared to typical behind-the-meter battery returns — and I documented exactly why: the number matches our own measured dispatch data, so it's not fabricated, but the *dispatch simulator* that generates that underlying data likely assumes closer to full price-spread capture than a real battery achieves. The honest fix is to de-rate the dispatch generator itself, which I deliberately deferred rather than patching the simulation layer alone — patching only one layer would have made Measured and Modeled numbers inconsistent with each other, which is worse than both being a bit optimistic in the same direction."
*TR: Bu kısım mülakatta çok iyi bir "kendi işinin sınırlarını biliyorsun" sinyali. Çıktı hâlâ tipik gerçek batarya getirilerine göre iyimser görünüyor — ve SEBEBİNİ dokümante etmişsin: sayı kendi ölçülen dispatch verimizle uyuşuyor (uydurma değil), ama o temel veriyi üreten dispatch simülatörü muhtemelen gerçek bir bataryadan daha fazla fiyat-farkı yakalanabileceğini varsayıyor. Dürüst düzeltme dispatch üretecinin kendisini aşağı çekmek — ama bunu bilerek ertelemişsin, çünkü sadece bir katmanı yamalamak Measured ve Modeled sayılarını birbiriyle tutarsız hale getirirdi; ikisinin de aynı yönde biraz iyimser olması bundan daha az kötü.

---

### 3.6 — Notebook 16c: `16c_reload_battery_tables.py` (a real Fabric-specific gotcha)

**What it does:** A small utility that re-reads CSVs and overwrites two Delta tables with a fresh schema, specifically to fix a "column X cannot be found" error after new columns were added upstream but the old Delta table's schema hadn't caught up.

```python
def _resolve_tables_prefix() -> str:
    schemas = [r["namespace"] for r in spark.sql("SHOW SCHEMAS").collect()]
    return "dbo." if "dbo" in schemas else ""
```
**English:** "Fabric Lakehouses can be either schema-less or use a `dbo` schema namespace depending on how they were created, and table references need the right prefix for either case. Rather than hardcoding one assumption, I detect it at runtime by checking `SHOW SCHEMAS`. This is a small but real Fabric-specific gotcha — the kind of platform detail that only shows up once you've actually worked in it, which is a good thing to mention if asked about hands-on Fabric experience versus theoretical knowledge."
*TR: Fabric Lakehouse'lar oluşturulma şekline göre şemasız ya da `dbo` şema alan adı kullanabiliyor, tablo referanslarının doğru öneki alması gerekiyor. Sabit bir varsayım yapmak yerine `SHOW SCHEMAS` ile çalışma zamanında tespit ediyorsun. Küçük ama gerçek bir Fabric'e özgü detay — sadece platformda gerçekten çalışınca karşına çıkan türden. "Fabric'te elle iş yaptın mı yoksa sadece teoride mi biliyorsun" sorusuna iyi bir kanıt.

---

## 4. THE interview story — notebook 14 → notebook 16 (memorize this shape, not the words)

Use the STAR shape. This is your strongest single answer for Kit questions S1, S5, and "tell me about a bug you found" / "tell me about a data quality problem."

**Situation:** *(EN)* "I had a Power BI page showing battery investment ROI per building and strategy — payback years, NPV, IRR — driven by a Spark notebook."
*(TR): Bina ve strateji başına batarya yatırım geri dönüşü (payback, NPV, IRR) gösteren bir Power BI sayfam vardı, bunu besleyen bir Spark notebook'u vardı.*

**Task:** *(EN)* "During a broader notebook cleanup, I decided to verify the simulation output against the real, measured dispatch data it was supposed to relate to — instead of assuming it was still correct."
*(TR): Daha geniş bir notebook temizliği sırasında, simülasyon çıktısının dayandığı gerçek, ölçülen dispatch verisiyle hâlâ tutarlı olup olmadığını doğrulamaya karar verdim — 'hâlâ doğrudur' diye varsaymak yerine.*

**Action:** *(EN)* "I compared the two tables directly and found they'd diverged: one building's simulated battery capacity was 5,600 kWh while its real, installed capacity was 800 kWh; the simulated 'active strategy' for another building didn't match what was actually installed. The old notebook had derived every non-measured number by multiplying one anchor value by a fixed factor — up to 4.55x for one strategy pair — and then capped the resulting IRR display at 35% and payback at 25 years whenever the number looked unrealistic, instead of fixing why it looked unrealistic. I rebuilt the notebook from scratch around a transparent rule: real dispatch data produces a 'Measured' label; a from-scratch physics estimate — capacity × depth-of-discharge × cycles-per-year × price spread × efficiency, using that specific building's own numbers — produces a 'Modeled' or 'Prospect' label; and I removed every display cap so the numbers are always the honest output of the model, even when that's an unflattering 15-year payback."
*(TR): İki tabloyu doğrudan karşılaştırdım ve ayrıştıklarını gördüm: bir binanın simüle edilmiş batarya kapasitesi 5.600 kWh iken gerçek kurulu kapasitesi 800 kWh'ydi; başka bir binanın simüle edilen "aktif stratejisi" gerçekte kurulu olanla uyuşmuyordu. Eski notebook, ölçülmeyen her sayıyı tek bir çapa değeri × sabit katsayı (bir strateji çiftinde 4.55'e kadar) ile türetiyor, sonuç gerçekçi görünmediğinde SEBEBİNİ düzeltmek yerine IRR gösterimini %35'te, geri ödemeyi 25 yılda tavanlıyordu. Notebook'u baştan, şeffaf bir kuralla yeniden kurdum: gerçek dispatch verisi "Measured" etiketi üretir; o binanın kendi sayılarıyla sıfırdan kurulmuş bir fizik tahmini (kapasite × kullanılabilir derinlik × yıllık döngü × fiyat farkı × verimlilik) "Modeled" ya da "Prospect" etiketi üretir; ve her tavanı kaldırdım, sayı her zaman modelin dürüst çıktısı olsun — 15 yıllık çirkin bir geri ödeme bile olsa.*

**Result:** *(EN)* "The rebuilt model reproduced the real measured savings for the one building I could cross-check within about 4%, which gave me confidence the physics logic was sound. I also documented, in the code itself, a remaining known limitation — the numbers are still somewhat optimistic relative to typical real-world battery returns, and I traced *why*: it's inherited from an upstream dispatch simulator's assumption, not from this notebook's own math — and I deliberately chose not to patch around it locally, because that would have made the 'Measured' and 'Modeled' numbers inconsistent with each other. I'd rather ship a transparent, slightly-optimistic-for-a-known-and-documented-reason model than a locally-patched, internally-inconsistent one."
*(TR): Yeniden kurulan model, çapraz kontrol edebildiğim bir bina için gerçek ölçülen tasarrufu ~%4 farkla üretti — bu da fizik mantığının sağlam olduğuna güven verdi. Ayrıca kodun içine kalan bilinen bir sınırlamayı da yazılı olarak belgeledim: sayılar hâlâ tipik gerçek dünya batarya getirilerine göre biraz iyimser, ve NEDENİNİ izledim — bu notebook'un kendi matematiğinden değil, üst akıştaki dispatch simülatörünün bir varsayımından geliyor — ve bunu yerel olarak yamalamamayı bilerek seçtim, çünkü bu "Measured" ve "Modeled" sayılarını birbiriyle tutarsız hale getirirdi. Yerel olarak yamalanmış ama içsel olarak tutarsız bir modelden ziyade, şeffaf ve bilinen/belgelenmiş bir sebeple hafif iyimser bir modeli tercih ederim.*

**Why this answer works:** it shows you (1) don't blindly trust your own past output, (2) can root-cause a discrepancy instead of patching a symptom, (3) understand the difference between fabricated and honestly-imperfect numbers, and (4) make and defend a scope decision (deferring the deeper fix) instead of scope-creeping a cleanup task into an open-ended rebuild. That maps directly onto Kit question S5 ("how do you ensure data quality and governance") and the "single source of truth" language already in your Kit's S7 answer.
*TR: Bu cevabın güçlü olma sebebi: (1) kendi geçmiş çıktına körü körüne güvenmediğini, (2) semptomu yamalamak yerine kök nedeni bulabildiğini, (3) "uydurma" ile "dürüst ama kusurlu" sayı arasındaki farkı bildiğini, (4) bir kapsam kararı verip savunabildiğini (derin düzeltmeyi bilerek ertelemek, temizlik görevini sınırsız bir yeniden yapıma çevirmemek) gösteriyor. Bu tam olarak Kit'teki S5 ("veri kalitesi ve governance") ve S7'deki "single source of truth" diline bağlanıyor.

---

## 5. Junior/Mid Data Engineer fundamentals — all demonstrated in this code

Each of these is something a junior data engineer should be able to define **and** point to a concrete example of. Every example below is a real line from these notebooks, not a textbook example.

**5.1 Transformations vs. actions, and lazy evaluation.**
`.filter()`, `.withColumn()`, `.groupBy().agg()`, `.join()` are all *transformations* — Spark just builds a query plan (a DAG) and does no work yet. `.count()`, `.collect()`, `.show()`, and `.write.saveAsTable()` are *actions* — they trigger actual execution. Notebook 12 builds a long chain of `.withColumn()` calls (section 3) before a single `.count()` — nothing runs until that count, or the final write, executes.
*TR: `.filter()`, `.withColumn()`, `.join()` gibi çağrılar "transformation" — Spark hemen bir şey çalıştırmaz, sadece bir plan (DAG) kurar. `.count()`, `.collect()`, `.write...saveAsTable()` gibi çağrılar "action" — gerçek çalıştırmayı tetikler. nb12'de uzun bir `.withColumn()` zinciri kurulur, ilk `.count()` ya da yazma işlemine kadar hiçbir şey fiilen çalışmaz. Bu "lazy evaluation" kavramı.

**5.2 Medallion architecture (bronze / silver / gold).**
Raw, protocol/source-native data lands in bronze unchanged. Silver cleans, types, and standardizes it (e.g. `silver_building_master`). Gold applies business logic and produces report-ready, aggregated tables (`gold_battery_dispatch`, `gold_battery_simulation`). This notebook is entirely a "gold" notebook — it only reads bronze/silver and reference tables, and writes gold.
*TR: Ham veri bronze'a olduğu gibi iner. Silver temizler, tipler, standardize eder. Gold iş mantığını uygulayıp rapora hazır, özetlenmiş tablolar üretir. Bu notebook tamamen bir "gold" notebook — sadece bronze/silver ve referans tablo okuyor, gold yazıyor.

**5.3 Schema enforcement vs. schema inference.**
Every table this pipeline *produces* has an explicit `StructType`/`StructField` schema (see notebook 13, 15, 16). Schema is only *inferred* (`option("inferSchema", "true")`) when reading an untrusted raw CSV as a fallback. Rule of thumb: infer on the way in from an untrusted source if you must, but always define and enforce a schema on the way out.
*TR: Bu pipeline'ın ÜRETTİĞİ her tablonun açık bir `StructType` şeması var. Şema sadece güvenilmeyen ham CSV okurken "inferSchema" ile tahmin ediliyor (fallback durumunda). Kural: güvenilmeyen kaynaktan girişte zorunlaysa tahmin et, ama çıkışta her zaman şemayı açıkça tanımla ve uygula.

**5.4 Idempotency and rerun-safety.**
Every table in this pipeline is written with `.mode("overwrite")`. Re-running the notebook twice in a row produces the same table, not duplicated rows — that's what "idempotent" means in this context, and it's the simplest way to get it (the alternative, append-mode, requires explicit dedup logic).
*TR: Bu pipeline'daki her tablo `.mode("overwrite")` ile yazılıyor. Notebook'u art arda iki kez çalıştırmak aynı tabloyu üretir, satırları çoğaltmaz — "idempotent" (aynı sonucu veren, tekrar çalıştırılabilir) olmanın en basit yolu budur. Alternatifi (append modu) elle dedup mantığı gerektirir.

**5.5 UDFs — what they cost, and when the cost doesn't matter.**
Notebook 12/14 wrap a Python NPV/IRR (Newton-Raphson) function with `pyspark.sql.functions.udf(...)`. A Python UDF forces Spark to serialize each row out to a Python process and back — it bypasses the Catalyst optimizer and is genuinely slow at large scale. Here it's applied to roughly one row per building × strategy (tens of rows), so the cost is irrelevant. **Be ready to say this nuance out loud**: "I know UDFs aren't the pattern for a hot path over millions of rows — there I'd reach for a native Spark SQL expression, a vectorized pandas UDF, or push the calculation to a different layer. Here, the data volume made it a non-issue."
*TR: nb12/14, Python NPV/IRR (Newton-Raphson) fonksiyonunu `udf(...)` ile sarıyor. Python UDF, Spark'ı her satırı Python sürecine gönderip geri almaya zorluyor — Catalyst optimizer'ı devre dışı bırakıyor, büyük ölçekte gerçekten yavaş. Burada bina×strateji başına ~1 satır (onlarca satır) olduğu için maliyet önemsiz. Mülakatta bu nüansı SESLİ söyle: "UDF'lerin milyonlarca satırlık sıcak yolda doğru desen olmadığını biliyorum — orada native Spark SQL ifadesi ya da vectorized pandas UDF kullanırım. Burada veri hacmi bunu önemsiz kıldı."

**5.6 Knowing when *not* to use Spark.**
Notebooks 13 and 16 build small (24–96 row) reference/lookup tables using plain Python/pandas, and call `spark.createDataFrame(pdf, schema=...)` only at the very end, purely to persist to Delta. Distributing a 24-row computation across a cluster adds overhead for zero benefit. Spark earns its keep on the large, raw, 15-minute-interval readings (notebook 12's aggregation step) — not on small reference tables.
*TR: nb13 ve nb16, küçük (24-96 satır) referans tablolarını düz Python/pandas ile kuruyor, `spark.createDataFrame(...)`'i sadece en sonda, Delta'ya kalıcı hale getirmek için çağırıyor. 24 satırlık bir hesabı kümeye dağıtmak sıfır fayda karşılığında ek yük getirir. Spark'ın gerçek katkısı büyük, ham, 15 dakikalık okuma verisinde (nb12'nin agregasyon adımı) — küçük referans tablolarında değil.

**5.7 Deterministic derived randomness.**
```python
.withColumn("_age_yr", F.round(F.lit(0.5) + (F.abs(F.hash(F.col("building_id"))) % 46) / 10.0, 2))
```
**English:** "I needed a plausible, varied battery install-age per building, but I needed the *same* value every time the notebook reruns — a real `rand()` would give a different number on every run, breaking reproducibility. Hashing a stable key (`building_id`) and taking a modulo gives a deterministic, reproducible pseudo-random value instead."
*TR: Bina başına inandırıcı, çeşitli bir batarya kurulum-yaşı gerekiyordu, ama notebook her çalıştığında AYNI değeri vermeliydi — gerçek bir `rand()` her çalıştırmada farklı sayı verir, tekrarlanabilirliği bozar. Sabit bir anahtarı (`building_id`) hash'leyip mod almak, deterministik/tekrarlanabilir bir sözde-rastgele değer veriyor.

**5.8 Broadcast joins, window functions, defensive nulls, and inline assertions** — already covered with real code in Section 3. Know all four cold; they're the four concepts most likely to come up as generic Spark/SQL questions regardless of the ASSET.100 domain.

---

## 6. SQL equivalents (bridge to Kit question S9)

Your Kit already flags that a SQL question may come up. These are the exact PySpark patterns from this notebook translated to SQL, so you can answer "how would you write that in SQL?" instantly.

| PySpark (this notebook) | Equivalent SQL |
|---|---|
| `df.groupBy("building_id","strategy").agg(F.sum("net_savings_eur"))` | `SELECT building_id, strategy, SUM(net_savings_eur) FROM t GROUP BY building_id, strategy` |
| `dfA.join(F.broadcast(dfB), "country_code", "left")` | `SELECT ... FROM a LEFT JOIN b ON a.country_code = b.country_code` (`/*+ BROADCAST(b) */` hint in Spark SQL) |
| `F.row_number().over(Window.partitionBy("country_code").orderBy(F.col("year").desc()))` then `filter(rn==1)` | `SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY country_code ORDER BY year DESC) rn FROM t) WHERE rn=1` |
| `F.sum("net_savings_eur").over(Window.partitionBy("building_id").orderBy("date").rowsBetween(Window.unboundedPreceding,0))` | `SUM(net_savings_eur) OVER (PARTITION BY building_id ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` |
| `F.coalesce(F.col("x"), F.lit(0.0))` | `COALESCE(x, 0.0)` |

*TR: Kit'in kendisi S9'da bir SQL sorusu gelebileceğini zaten söylüyor. Bu tablo, notebook'taki gerçek PySpark kalıplarının SQL karşılığı — "bunu SQL'de nasıl yazardın" sorusuna anında, somut örnekle cevap verebilmen için.

---

## 7. Fabric-specific talking points (bridge to Kit question S8)

- **OneLake:** every workspace's data lands in one tenant-wide Delta lake; this pipeline reads/writes plain table names (`spark.read.table("gold_battery_dispatch")`) because Fabric notebooks resolve those against the attached Lakehouse automatically — no explicit ABFS path needed for the common case.
- **DirectLake:** Power BI reads these gold Delta tables directly, without an import/refresh copy step — which is exactly why a schema mismatch (Section 3.6) surfaces as a report-breaking error rather than a silent stale copy.
- **Schema evolution:** `spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")` plus `option("overwriteSchema","true")` are the two levers this code uses to let new columns flow through as the model evolved — and Section 3.1 already gives you the story of where `autoMerge` alone wasn't reliable enough.
- **Capacity (F-SKU):** not touched by this notebook's code, but you already have this in your Kit (S8) — F-SKU capacity can be paused when idle to stop billing.

*TR: Kit'in S8 sorusuna (OneLake/DirectLake/kapasite/RLS) ek, kod-temelli detaylar. OneLake: tüm workspace verisi tek bir Delta gölünde, notebook'lar tablo adını doğrudan kullanabiliyor. DirectLake: Power BI bu gold tabloları import'suz okuyor — bu yüzden şema uyuşmazlığı (3.6) sessiz bayat kopya değil, raporu kıran bir hata olarak ortaya çıkıyor. Şema evrimi: `autoMerge` + `overwriteSchema` bu kodun yeni kolonları geçirmek için kullandığı iki araç — ve 3.1'de `autoMerge`'ün tek başına yetmediği durumun hikâyesi zaten var.

---

## 8. Numbers to have ready (verified from the code — not from the Master Study Guide)

| Building | Country | Chemistry | Capacity | PV | Installed / active strategy | `data_basis` in nb16 |
|---|---|---|---|---|---|---|
| B001 Berlin | DE | LFP | 200 kWh | 120 kWp | self_consumption | Measured |
| B003 Hamburg | DE | LFP | 800 kWh | 500 kWp | peak_shaving | Measured |
| B004 Wien | AT | LFP (hypothetical) | 400 kWh | 80 kWp | none — no battery installed | Prospect |
| B005 Frankfurt | DE | NMC | 400 kWh | 200 kWp | backup | Measured |
| B006 Amsterdam | NL | LFP (hypothetical) | 600 kWh | 150 kWp | none — no battery installed | Prospect |
| B007 Copenhagen | DK | LFP | 450 kWh | 380 kWp | self_consumption | Modeled *(dispatch savings field has a pending data bug, so it can't be "Measured" yet)* |

- **4 dispatch strategies:** peak-shaving, self-consumption, time-of-use (ToU), backup.
- **EU Battery Regulation 2023/1542** compliance in this model: LFP = compliant, NMC = not (a deliberate chemistry-level simplification for the 2 chemistries actually in use — the broader 10-product reference catalog in notebook 12 has finer, per-product compliance flags, including NCA cells that split both ways).
- **Financial model constants (nb16):** 5% discount rate, 2.5% inflation, 10-year NPV horizon, 15% year-10 salvage value, 8% install overhead on top of hardware CAPEX, battery hardware cost ≈ €135/kWh (LFP) / €125/kWh (NMC).
- If asked for an exact euro savings or payback figure: say the model computes it per building from live dispatch/tariff data, and that you'd pull the current number rather than quote one from memory — the last verified run was 2026-06-22, and pricing/tariff reference data can move. That's the honest, correct answer given Section 0.2.

*TR: Bu tablo Master Study Guide'daki (12 ülke/8 kimya/672 satır) YANLIŞ sayılar yerine kullanacağın, doğrudan koddan doğrulanmış gerçek sayılar. Kesin bir € tasarruf ya da geri ödeme rakamı sorulursa: "model bunu her bina için canlı dispatch/tarife verisinden hesaplıyor, ezbere bir sayı vermek yerine güncel değeri çekerdim" de — son doğrulanmış çalıştırma 22 Haziran 2026'ydı ve fiyat/tarife referans verisi değişebilir. Bu, Bölüm 0.2'ye göre dürüst ve doğru cevap.

---

## 9. Rehearsal Q&A — mapped to your existing Interview Prep Kit

**Kit S1 ("walk me through an ETL/ELT pipeline you built"):** Use Section 1's pitch, then go one level deeper with Section 2's pipeline map if they want detail.

**Kit S5 ("how do you ensure data quality and governance"):** Use the Section 4 STAR story directly. It is a better, more specific answer than the Kit's current generic S5 answer — use both together: lead with the generic principle from the Kit ("traceability back to source, single source of truth"), then land it with "...and here's a concrete example of when I found and fixed exactly that kind of drift."

**Kit S8 ("Fabric-specific: OneLake, DirectLake, capacity, RLS"):** Use the Kit's existing answer, reinforced with Section 7's two extra, code-grounded details (autoMerge / overwriteSchema, and the `dbo` schema-prefix detection trick) if they probe deeper than the one-paragraph version.

**Kit S9 ("a SQL question"):** Use Section 6's table directly — you can describe any of those four patterns fluently from memory now.

**New question this notebook prepares you for — "tell me about a bug you found in your own work":** Section 4, verbatim shape.

**New question — "when would you *not* use Spark / not use a UDF?":** Sections 5.5 and 5.6 give you two concrete, opposite-direction examples (a small-scale Python loop instead of Spark; a necessary-but-slow UDF used only where volume made it safe) — most junior candidates only have a textbook answer here; you have two real ones.

*TR: Bu bölüm, zaten sahip olduğun Interview Prep Kit'teki sorularla bu dokümanı birebir eşliyor — hangi bölümü hangi soruya kullanacağını gösteriyor. Ayrıca Kit'te olmayan ama bu notebook'un seni hazırladığı iki yeni soru tipi de var (kendi hatanı bulma hikâyesi, Spark/UDF kullanmama kararı).

---

## 10. What *not* to claim

- Don't say this report is currently auto-refreshing in production (Section 0.2) — say it precisely instead.
- Don't quote the Master Study Guide's 12-country/8-chemistry/672-row figures (Section 0.3).
- Don't claim GIS or Unity Catalog hands-on experience — your Kit already handles this correctly (curiosity framing, not false confidence). This notebook doesn't touch either, so it doesn't help you here — don't reach for it.
- Don't lead with "I built a battery optimization system" as your headline pitch for this specific interview — lead with the ETL/ELT + data-quality framing from Section 1. Battery is the example, not the point.

*TR: Son bölüm — söylememen gerekenler. Bu raporun şu an otomatik yenilendiğini söyleme (0.2'deki gibi net konuş). Master Study Guide'daki yanlış sayıları tekrarlama (0.3). GIS ya da Unity Catalog'da elle deneyimin varmış gibi konuşma — Kit zaten bunu doğru çerçeveliyor (merak, sahte özgüven değil), bu notebook ikisine de değinmiyor. Ve bu mülakat için başlık cümlen "battery optimizasyon sistemi kurdum" olmasın — Bölüm 1'deki ETL/ELT + veri kalitesi çerçevesiyle başla. Battery burada örnek, konunun kendisi değil.

---

## Quick self-test (close the laptop, answer out loud)

1. Draw the pipeline from Section 2 from memory, table names included.
2. Tell the Section 4 story in under 90 seconds, in English.
3. Name the four Spark/SQL patterns from Section 6 without looking.
4. Explain, in one sentence, why `gold_battery_dispatch` uses overwrite instead of MERGE.
5. State precisely (Section 0.2) whether this report is live in production.

If all five are fluent without notes, you're ready.

*TR: Beşi de notsuz, akıcı çıkıyorsa hazırsın. Pazartesi için bol şans — teknik taban zaten sende var, bu doküman sadece onu somut örneklerle konuşabilir hale getiriyor.*
