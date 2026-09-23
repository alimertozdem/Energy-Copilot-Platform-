# Out-of-hours energy review — the repeatable version

One product, one command, same output every time. No Spark, no Fabric, no cloud
account. Runs on a laptop with Python + pandas + matplotlib.

```
python audit.py jobs/<client>.json
```

## Why this is not the EnergyLens anomaly notebook

`notebooks/anomaly-detection/anomaly_detection.py` in EnergyLens is good work, but
it cannot do this job:

| | EnergyLens notebook | this tool |
|---|---|---|
| runtime | PySpark on Fabric | plain Python, a laptop |
| depends on | gold_kpi_daily → silver → bronze → weather/price/CO₂ loaders | one CSV |
| granularity | daily aggregates | the client's raw interval data |
| cost to run once | a Fabric capacity | nothing |
| out-of-hours logic | monthly weekend-vs-weekday EUI ratio | every interval, against stated hours |

What carried over is the **thinking** — rule shapes, threshold discipline, the
habit of writing down why a number is what it is. Not the code.

## What it produces

A single self-contained HTML file (images embedded, opens anywhere, prints to
PDF). One building, one period, seven findings, two charts, a scenario table,
evidence rows, and the reconciliation checks printed inside the report.

## Why the client can trust the numbers

Every figure carries a label:

- **MEASURED** — straight from their file
- **DERIVED** — arithmetic on their file, formula printed next to it
- **ASSUMED** — supplied by us, value and source printed

The headline is deliberately MEASURED: *how much electricity was used while the
building was closed.* No benchmark, no model, no assumption — it is their own
meter, split by the operating hours they gave us.

The savings figure is DERIVED, not promised: **€X per year for every 1 kW removed
from the closed-period load** (closed hours × tariff). The client picks the
target; we supply the conversion rate. That is the difference between a claim we
can defend and one we cannot.

## The checks

`engine/checks.py::reconcile` runs eight checks on every job and **the report is
not written if any fails**:

1. Report total = sum of rows used
2. Rows used reconcile to the raw file total (duplicates accounted for)
3. Closed + occupied energy = total (no interval double-counted)
4. No negative readings
5. Interval coverage ≥ 95%
6. The site's demonstrated floor is below its typical closed load
7. Avoidable energy ⊆ closed-period energy
8. Avoidable energy < 40% of annual use (sanity ceiling)

## The fixture

`testdata/make_fixture.py` builds a synthetic year with **known planted waste**:
an 18 kW night floor, HVAC starting at 05:30 against stated 08:00 opening, a
Christmas shutdown that never switches off, plus 3 gaps, 1 duplicate row and both
daylight-saving days. `fixture_truth.json` records the right answers.

Run the fixture after any change to the engine. It has already earned its keep —
it caught two real defects:

- the "site's own best night" method silently under-reports when waste is
  *constant* (a building that is always bad has no good night to compare with).
  That is why the headline is now the measured closed-period share.
- the ramp detector reported the middle of the morning ramp rather than its
  start; the threshold moved from 25% to 10% of daily range.

## Layout

```
audit.py              one command per client
engine/ingest.py      read any CSV, normalise, report data quality
engine/checks.py      the analysis + the reconciliation checks
engine/report.py      charts + self-contained HTML
jobs/                 one JSON per client — the only thing that varies
testdata/             the fixture and its ground truth
INTAKE.md             what to ask the client for
```

## Real-data validation (done)

Source: **Building Data Genome Project 2** — 1,636 real buildings, 2 years of
hourly meter data, open licence.
`https://github.com/buds-lab/building-data-genome-project-2`
Files sit behind git-LFS; fetch them from the media endpoint, not `raw.`:
`https://media.githubusercontent.com/media/buds-lab/building-data-genome-project-2/master/data/...`

Two real buildings were run through the tool. It found three defects the
synthetic fixture could not:

1. **Missing `tzdata`** — Windows ships no system timezone database, so any
   non-local timezone died in a 60-line traceback. Now a dependency, and the
   error is caught with a readable message.
2. **DST handling destroyed a real reading.** BDG2 timestamps are naive and
   carry *no* DST shifts. The code force-localised them to a DST zone, which
   pushed the non-existent spring-forward hour onto the next real one, called
   the collision a "duplicate" and deleted 77.5 kWh. Fixed: the loader now
   detects whether the series is wall-clock local or fixed standard time and
   says which reading it used. Nothing is moved or merged.
3. **The 40% ceiling was firing without explaining itself.** Replaced with a
   schedule-plausibility check: when closed-period load exceeds 55% of occupied
   load the building either runs 24/7 or the stated hours are wrong, and the run
   stops with that sentence instead of a bare number.

**Commercially useful finding:** of 296 real office buildings screened, **70
(24%) fit this report's assumptions.** The rest run closer to 24/7. Roughly one
office in four is a candidate — worth knowing before writing 50 emails.

On the building that did fit (Hog office, 18,213 m², 1.22 GWh/yr): 53.3% of the
year's electricity was used while closed, and the closed-day load profile
follows a working-day shape — the site runs its plant on a weekday schedule at
weekends. That is a real, specific, sellable finding.

## Two deliverables, one engine

`audit.py` → the PDF/HTML report. `export_powerbi.py` → a Power BI model
(fact + 2 dimensions + 24 DAX measures + build guide). Both call
`engine/checks.py`, so the closed/occupied split and the tariff are computed
once. The exporter runs the same reconciliation checks and refuses to write a
model the report would not be issued from. No business logic lives in DAX.

## Before selling this

- [ ] Confirm the residence permit allows self-employed work before invoicing
- [ ] Decide the price. The report states annual € at risk; the fee should be
      small next to it.
- [ ] Ask the schedule question in the intake — 24/7 sites are not candidates
