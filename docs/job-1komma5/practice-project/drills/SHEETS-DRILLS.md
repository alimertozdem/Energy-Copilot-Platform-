# Google Sheets drills — do these after building the model

Open `output/backtest_by_customer.csv` in Google Sheets (`File → Import`). 28 rows, one per customer. Then do these eight. Expected answers are given so you can self-check.

| # | Task | Function | Expected |
|---|---|---|---|
| **S1** | List only customers with `battery_kwh > 0`, sorted by `save_C_vs_B` descending, showing malo_id, segment, save_C_vs_B. | `=QUERY(A:Z,"select A,B,F where D>0 order by ... desc",1)` — adjust letters | 20 rows |
| **S2** | Pivot table: average `bill_B_dynamic` by `segment`. | `Insert → Pivot table` | 5 segments |
| **S3** | On a second tab, type any malo_id and return its segment. | `XLOOKUP` (or `INDEX/MATCH`) | matches source |
| **S4** | New column: saving % of B vs A, for all rows in one formula. | `=ARRAYFORMULA((bill_A-bill_B)/bill_A)` | ~7–11% |
| **S5** | Total `kwh_load` for `PV_battery_HP` only. | `SUMIFS` | ≈ 51,605 |
| **S6** | Highlight red every row where `ratio_B > 1`. | `Format → Conditional formatting`, custom formula | all 28 rows go red |
| **S7** | Build the two-way sensitivity grid from the build guide, from scratch. | `$` anchoring, one formula dragged | saving flips negative ≈13.6 ct |
| **S8** | Column chart of `bill_A` vs `bill_B` vs `bill_C` by segment. | `Insert → Chart` | 3 series |

**S6 is the interesting one.** Every single customer has `ratio_B > 1` — they all consume disproportionately in expensive quarter-hours. If you did not expect that, that is the finding, not a bug.

**S7 is the one that matters for the interview.** Sheets has no Data Table feature, so the grid is built with `$` anchoring: row header `$A7`, column header `B$6`, everything else fully absolute. Get that right and one formula fills the grid.

## Then the harder half: `QUERY()`

`QUERY()` is the highest-leverage function in Sheets and the one most people never learn. Do these three on the same data:

1. `select segment, sum(E) group by segment order by sum(E) desc` — aggregation without a pivot table
2. `select * where B = 'PV_battery_HP' and D > 8` — multi-condition filter
3. `select segment, avg(H) group by segment label avg(H) 'mean ratio'` — aggregate with a renamed output

If you can write those three from memory, you are past what "comfortable with Google Sheets" means in a JD.
