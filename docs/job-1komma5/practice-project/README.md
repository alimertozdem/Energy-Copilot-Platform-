# Practice project — dynamic tariff analytics, end to end

A complete, runnable version of the work an **Energy Products & Tariffs** product intern actually does: dirty data in, clean pipeline, business marts, unit economics, a decision memo out.

Nothing here is a toy. Every dataset defect is a real European energy-retail failure mode, and three of the modelling bugs documented in the code are bugs that were genuinely made while building it and then fixed — that history is left in the comments on purpose, because "how do you know your number is right?" is the question you will actually be asked.

> **TR:** Bu proje, bir tarif ürün stajyerinin gerçekten yaptığı işin çalışan bir kopyası: kirli veri → temiz pipeline → iş tabloları → birim ekonomi → karar notu. Verideki her bozukluk gerçek bir sektör hatası. Koddaki üç modelleme hatası da gerçekten yapılıp düzeltildi ve yorumlarda bilinçli olarak bırakıldı — çünkü sorulacak soru "bu sayının doğru olduğunu nereden biliyorsun?".

---

## Run it

```bash
pip install duckdb pandas numpy matplotlib openpyxl
cd python
python 01_generate_data.py        # writes 4 dirty CSVs into ../data/
python 02_run_pipeline.py         # bronze -> silver -> gold in DuckDB
python 03_answer_questions.py     # the 10 PM questions, -> output/pm_answers.md
python 04_tariff_backtest.py      # fixed vs dynamic vs battery, -> charts + CSVs
python 05_build_workbook.py       # -> output/unit_economics_model.xlsx
```

Total runtime under 30 seconds. If your `output/` folder sits on OneDrive or Dropbox, the sync client locks DuckDB's write-ahead log — set `DUCKDB_PATH` to a local folder:

```powershell
$env:DUCKDB_PATH="C:\temp\energy.duckdb"
python 02_run_pipeline.py
```

> **TR:** PowerShell 5.x'te `&&` çalışmaz — komutları satır başına bir yaz. `output/` klasörü OneDrive/Dropbox içindeyse DuckDB'nin WAL dosyası kilitlenir; `DUCKDB_PATH`'i yerel bir klasöre ver.

---

## What is in here

| Path | What it is |
|---|---|
| `python/01_generate_data.py` | Builds the synthetic portfolio and **injects 12 named defects** |
| `python/02_run_pipeline.py` | Runs the SQL layers in order |
| `python/03_answer_questions.py` | Executes the PM questions and writes a work sample |
| `python/04_tariff_backtest.py` | The battery/tariff backtest with a **physical sanity gate** |
| `python/05_build_workbook.py` | Builds the live-formula Google Sheets model |
| `sql/01_bronze.sql` | Raw landing — all text, nothing dropped |
| `sql/02_silver.sql` | Clean, conformed, typed — one fix per named defect |
| `sql/03_gold.sql` | Business marts: interval fact, customer P&L, MaKo funnel, DSO scorecard, DQ |
| `sql/04_pm_questions.sql` | Ten analysis questions with their framing |
| `output/unit_economics_model.xlsx` | 7-tab model — upload to Drive, opens in Google Sheets |
| `output/backtest_charts.png` | Dispatch day, bill by scenario, ratio before/after |
| `output/pm_answers.md` | The query answers, reproducible |
| `DECISION-MEMO.md` | **The actual deliverable** — findings, recommendations, and what I would not claim |
| `BUILD-GUIDE-google-sheets.md` | Build the model yourself, step by step |

---

## The 12 data defects, and why each one matters commercially

| # | Defect | What it costs if you miss it |
|---|---|---|
| 1 | Duplicate rows (re-published prices, re-sent MSCONS) | Double-counted volume → over-billing → complaints |
| 2 | Missing intervals | Under-billed volume; invisible unless you build a calendar spine |
| 3 | Hard NULL values | `SUM` silently treats them as nothing; totals look plausible and are wrong |
| 4 | German decimal comma (`0,25`) | Whole column parses as text; `SUM` returns 0 |
| 5 | Mixed timestamp formats | Half the rows fail to parse and disappear |
| 6 | Naive local timestamps + DST | 2025-03-30 has **92** quarter-hours, 2025-10-26 has **100** |
| 7 | kW reported instead of kWh | **4× inflation** of those customers' consumption |
| 8 | PV export leaked into the import register | Negative consumption; clamping to zero hides an energy-balance error |
| 9 | MaLo-ID leading zero stripped by Excel | A naive join **silently drops 14% of customers** |
| 10 | Dirty categoricals (`Berlin`/`BERLIN`/`berlin `) | One city becomes three rows in every `GROUP BY` |
| 11 | Orphan foreign keys | Inner join drops them with no trace unless you log rejects |
| 12 | Funnel dead ends | Customers supplied but never invoiced; revenue simply never arrives |

**Measured result of the cleaning:** 257,061 rows landed → 18,566 rejected (17,024 orphan MaLo, 1,542 unparseable) → 2,786 duplicates removed → **235,709 usable (91.69%)**. Mean interval completeness 98.53%. Substitute values (*Ersatzwerte*) 2.09%.

> **TR:** Tablodaki 12 bozukluğu ezberlemene gerek yok ama 6, 7 ve 9'u anlatabilmelisin — yaz saati (bir gün 92, bir gün 100 çeyrek saat), kW/kWh karışması (4 kat şişme) ve Excel'in MaLo-ID'den sıfır kırpması (join'in müşterilerin %14'ünü sessizce yemesi). Bunlar mülakat malzemesi.

---

## The SQL techniques demonstrated, and where

Everything below is standard ANSI SQL. It runs unchanged on Postgres, Snowflake and BigQuery with at most a function-name swap.

| Technique | Where | Why it is the right tool |
|---|---|---|
| `ROW_NUMBER() … QUALIFY rn = 1` | dedup prices and meter | The canonical dedup: partition by business key, order by what makes one row authoritative |
| Calendar spine + `LEFT JOIN` | `silver_calendar`, `qa_price_days` | You cannot detect a **missing** row by querying rows that exist |
| `AT TIME ZONE` in both directions | `silver_prices`, `silver_meter` | The single most misunderstood concept in SQL time handling — see the boxed comment in `02_silver.sql` |
| `LAG()` / `LEAD()` | `silver_mako_events` | Latency of each funnel hop, not just the end-to-end total |
| `MIN(…) FILTER (WHERE …)` | `gold_mako_funnel` | Collapses an event log into one row per entity with a column per milestone — **the** funnel pattern |
| `FILTER` as a pivot | `v_params`, negative-price metrics | Tall config table → one wide row of named parameters |
| Volume-weighted average | `gold_customer_month` | `SUM(price×volume)/SUM(volume)`, never `AVG(price)`. The gap between the two *is* the value of load shifting |
| `MEDIAN()` / `MODE()` | `gold_dso_scorecard` | Medians survive outliers; a mean time-to-supply is destroyed by one stuck case |
| Reject table + reconciliation | `silver_meter_rejects`, `gold_data_quality` | Every input row is accounted for: landed = rejected + deduped + usable |
| Cohort join, ops → commercial | Q10 | Turns an operational metric into a funded business case |

---

## The three modelling bugs left documented in the code

These are in `04_tariff_backtest.py`, with the reasoning preserved:

1. **Sort order instead of time order.** Discharging into the priciest quarter-hours and charging in the cheapest lets the battery discharge at 08:00 energy it only charges at 13:00. Reported a **66% bill cut** — physically impossible.
2. **State of charge reset at midnight.** Throws away energy already paid for. Made the battery **increase** the portfolio bill by €3,768.
3. **No economic gate on cycling.** The round-trip loss is priced at **retail**, not spot, because every grid kWh pays grid fees, levies and VAT. Without the gate the battery was worth ~€0 and made 9 customers worse off.

The fix for (3) produced the most interesting finding in the whole project:

```
basis = P_charge/η + (1/η − 1) × (markup + grid fee + levies)
      = 1.136 × P_charge + 3.22 ct/kWh      (η = 0.88, German 2026 stack)
```

Residential spot arbitrage needs roughly a **3.2 ct/kWh spread before it earns anything**. That is why home batteries in Germany earn their money on **self-consumption** (displacing ~37 ct retail), not on trading the curve.

A fourth constraint followed: **do not fill a battery the household cannot empty.** A 15 kWh battery in a home using 7 kWh/day strands the surplus. Oversized storage cannot be monetised by a small consumer, no matter how good the optimiser is.

The script ends with a **sanity gate** of five physical assertions and refuses to report a clean result if any trips. Its tolerance for the period-boundary effect is *derived* (one full charge at retail price), not tuned until the symptom disappeared.

> **TR:** Bu üç hata bilerek kodda bırakıldı çünkü mülakatta anlatılacak en güçlü şey bunlar: (1) sıralama yerine zaman sırası — batarya gelecekten borç alamaz, %66 tasarruf çıkmıştı; (2) gece yarısı şarj sıfırlama — bataryayı zarara çevirdi; (3) çevrim için ekonomik eşik yok — kayıp enerji perakende fiyat ödediği için ~3,2 ct/kWh makas şart. Üçüncüsünün düzeltmesi projenin en değerli bulgusunu üretti: ev bataryasının parası arbitrajda değil öz-tüketimde.

---

## How this maps to Microsoft Fabric

You already know Fabric. This project deliberately uses vendor-neutral SQL so the skill transfers, but the mapping is one-to-one — say it in their vocabulary, not yours.

| Here | Fabric | Snowflake / BigQuery / dbt |
|---|---|---|
| `01_bronze.sql` | Notebook writing Delta tables to the Lakehouse | `raw` / landing schema |
| `02_silver.sql` | Notebook `02_silver_transform` | dbt `staging` models |
| `03_gold.sql` | Notebook `03_gold_business_logic` | dbt `marts` models |
| `v_params` | Config Delta table read at the top of each notebook | dbt `seed` / `vars` |
| `gold_data_quality` | DQ notebook + Data Activator alert | dbt tests / `elementary` |
| DAX measures | Semantic model on DirectLake | Looker/Metabase metrics layer |
| `AT TIME ZONE` both ways | `to_utc_timestamp()` / `from_utc_timestamp()` | same as here |
| `QUALIFY` | Spark SQL supports it | Snowflake native; BigQuery native |

**How to say it:** *"The concepts are identical, only the vendor's words change — bronze/silver/gold is raw/staging/marts, notebooks are transformation jobs, DAX is the metrics layer. I wrote this in portable SQL specifically so it isn't tied to one platform."* That signals transferability rather than tool loyalty.

---

## What to actually take into the interview

Three artefacts and three sentences.

**Artefacts:** `DECISION-MEMO.md`, `output/backtest_charts.png`, and the Google Sheets model. Not the code — nobody reads code in a 45-minute call.

**Sentences:**

1. *"I backtested a dynamic tariff against a year of German day-ahead prices and found the saving is a price-level effect, not an optimisation effect — every unoptimised household has a realised/average price ratio above 1.0, because the evening consumption peak sits on the evening price peak."*
2. *"Battery spot arbitrage came out at about €57 per battery per year, because the round-trip loss pays retail, not spot — it needs a 3.2 ct/kWh spread before it earns anything. That's why home storage makes its money on self-consumption."*
3. *"The highest-return fix I found wasn't in the tariff at all. 18% of switches were rejected first time, mostly 'MaLo-ID unknown at DSO', and the root cause was an Excel export stripping leading zeros — which also silently dropped 14% of customers from every downstream report. One regex at signup."*

Then stop talking and let them ask.

> **TR:** Görüşmeye kod götürme — 45 dakikalık aramada kimse kod okumaz. Üç çıktı (karar notu, grafikler, Sheets modeli) ve üç cümle götür. Üçüncü cümle en güçlüsü, çünkü ilanın "Marktkommunikation süreçlerini iyileştir" satırına doğrudan cevap veriyor ve kök-sebep bulma becerisi gösteriyor. Cümleleri söyleyip **sus** — sorularını sormalarına izin ver.

---

*Synthetic data throughout. The method transfers; the magnitudes need real metered data.*
