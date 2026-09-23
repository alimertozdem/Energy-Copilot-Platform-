# START HERE — the order to do things in

Total ~4 hours of doing, spread over 2–3 sittings. No long reading anywhere in this list.

---

## 0 · Setup (5 min, once)

Open PowerShell. One command per line — `&&` does not work in PS 5.x.

```powershell
python --version
```

- Says `Python 3.x` → continue.
- Says nothing / "not recognized" → install from python.org, tick **"Add Python to PATH"**, reopen PowerShell.

```powershell
pip install duckdb pandas numpy matplotlib openpyxl
```

**Why DuckDB:** a database in a single file, no server, no install wizard. The SQL you write in it runs unchanged on Postgres, Snowflake and BigQuery — which is what an employer cares about.

```powershell
cd "C:\Energy Management App\Energy-copilot-platform\docs\job-1komma5\practice-project\python"
$env:DUCKDB_PATH="C:\temp\energy.duckdb"
```

**Why the env var:** the repo folder may be synced by OneDrive, which locks DuckDB's log file. Keep the database on a local path.

---

## 1 · Run the pipeline once, without reading anything (10 min)

```powershell
python 01_generate_data.py
python 02_run_pipeline.py
python 03_answer_questions.py
python 04_tariff_backtest.py
python 05_build_workbook.py
```

**Why:** you need to see it work before you understand it. Watch the terminal — `01` prints the 12 data defects it injected, `04` prints `SANITY GATE: PASS`.

**Look at two things only:**
- `output/backtest_charts.png` — one day of battery dispatch, bills by scenario, and the ratio scatter
- terminal output of `04` — the three portfolio numbers

Stop there. Don't read the SQL yet.

---

## 2 · SQL drills — you write, the machine grades (90 min)

This is the part that actually builds the skill.

1. Open `drills/SQL-DRILLS.md` — it is a **table of 10 one-line tasks**, not prose.
2. Open `drills/my_answers.sql`. Write your SQL under `-- D1`, `-- D2`, …
3. Run the grader as often as you like:

```powershell
python 06_check_drills.py
```

It prints PASS/FAIL per drill with a hint, and for small results it shows yours next to the expected one. It derives the expected answers from your own data at runtime, so it is never stale.

**Rules:** look up syntax freely. Do **not** open `reference_solutions.sql` until a drill has beaten you for 15 minutes.

**Why these 10:** D1–D2 are data quality (most of the actual job). D3 is the single most common tariff-analysis mistake. D5/D8 are how you size a flexibility opportunity. D6–D7 are the Marktkommunikation funnel the job ad names explicitly. D9–D10 are window functions and pivots — every SQL screen tests those two.

Goal: **10/10 without the reference file.**

---

## 3 · Google Sheets — build the model yourself (60 min)

1. Upload `output/unit_economics_model.xlsx` to Google Drive → right-click → *Open with Google Sheets*. Look at the 7 tabs for 2 minutes. **Close it.**
2. Open a blank sheet. Build it from `BUILD-GUIDE-google-sheets.md` — that file is step-by-step, formulas given, minimal prose.
3. Compare yours to the original at the end.

**Why build it instead of using it:** in the interview you will be asked how a number is produced, not shown one. You only own the logic you typed.

**The three things being graded, in order:** inputs isolated in one block · no hardcoded numbers in formulas · a sensitivity grid you can explain.

---

## 4 · Sheets drills — data wrangling (45 min)

Import `output/backtest_by_customer.csv` into Sheets, then do the 8 tasks in `drills/SHEETS-DRILLS.md`. Expected answers are in the table so you self-check.

**Why separate from step 3:** step 3 taught modelling. This teaches **wrangling** — `QUERY`, pivot tables, `XLOOKUP`, `ARRAYFORMULA`, `SUMIFS`, conditional formatting. Job ads say "comfortable with Google Sheets" and mean both. Modelling without wrangling is the more common gap.

Finish with the three `QUERY()` exercises at the bottom. If you can write those from memory you are past what the JD asks.

---

## 5 · Read the memo, once, out loud (15 min)

`DECISION-MEMO.md`. Read it aloud. It is the only document here written the way you would actually speak in the interview: finding → number → recommendation → named risk.

Then close everything and say the three sentences at the bottom of `README.md` from memory. If you can't, reread the memo and try again tomorrow.

---

## 6 · Optional but high-return (60 min)

Break the model on purpose and watch the guards catch you:

- In Sheets `02_Inputs`, set **Autarkiegrad uplift** to `0.8`. `07_Checks` should flip to `CHECK — impossible autarky`. That guard exists because my first version reported **zero grid import** — a household buying no electricity, because PV was allowed to cover the night.
- Set **average spot** to `16`. Customer saving goes negative and the dashboard turns `RED — do not sell this`. That is the 13.6 ct/kWh break-even.
- In `04_tariff_backtest.py`, change `ETA` from `0.88` to `1.0` (a lossless battery) and rerun. Battery value jumps. That gap **is** the 3.2 ct/kWh arbitrage threshold — the losses pay retail, not spot.

**Why:** anyone can run a model. Being able to say "here is how I tried to break it and here is what stopped me" is the difference between an analyst and someone who gets trusted with a decision.

---

## Where the time actually goes

| Step | Time | What you walk out with |
|---|---|---|
| 0–1 | 15 min | It runs; you have seen the outputs |
| 2 | 90 min | **You can write analytical SQL from scratch** |
| 3 | 60 min | You can build an auditable model |
| 4 | 45 min | You can wrangle data in Sheets, not just model in it |
| 5 | 15 min | You can tell the story in 3 sentences |
| 6 | 60 min | You can defend the numbers under pressure |

Steps 2 and 4 are the ones that close real gaps. If you only have one evening, do 2.
