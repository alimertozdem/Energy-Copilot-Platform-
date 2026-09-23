# SQL drills — write these yourself

Write your answer under the matching marker in `my_answers.sql`, then run `python 06_check_drills.py`. It tells you PASS/FAIL per drill and gives a hint. It derives the expected answer from `reference_solutions.sql` at runtime, so it always matches your data.

Tables available: `stg_meter`, `silver_meter`, `silver_prices`, `silver_calendar`, `silver_customers`, `silver_mako_events`, `gold_interval`, `gold_customer_month`, `gold_customer_summary`, `gold_mako_funnel`.

| # | Task | Technique it forces |
|---|---|---|
| **D1** | How many `(malo_id, timestamp)` pairs appear more than once in `stg_meter`? Ignore rows with an unparseable timestamp. | `GROUP BY … HAVING COUNT(*)>1` |
| **D2** | For the customer with the lowest `malo_id`, how many 15-min intervals are **missing** in March 2025? | calendar spine + `LEFT JOIN … IS NULL` |
| **D3** | For segment `PV_battery_HP`: the **volume-weighted** average spot price paid, and the simple average. Both, side by side. | `SUM(p*v)/SUM(v)` vs `AVG(p)` |
| **D4** | The 5 most expensive quarter-hours of 2025, showing **local** time and price in EUR/MWh. | `ORDER BY … LIMIT`, timezone display |
| **D5** | Negative-price quarter-hours **per month**. Only show months that had at least one. | `DATE_TRUNC` + `FILTER` |
| **D6** | How many customers had at least one rejected UTILMD, and what was their average days-to-supply? | conditional aggregate on a funnel table |
| **D7** | First-time-right switch rate per DSO, as a percentage. | `COUNT(*) FILTER (…)/COUNT(*)` |
| **D8** | The 10 days of 2025 with the largest intraday peak-to-trough spread in ct/kWh. | `MAX−MIN` per group |
| **D9** | Daily average spot **plus** a rolling 7-day average. First 10 days. | window frame `ROWS BETWEEN 6 PRECEDING` |
| **D10** | Average saving % per segment, with **February, March, April as three columns**. | `FILTER` pivot |

**Why these ten:** D1–D2 are data-quality work (most of the job). D3 is the single most common tariff-analysis error. D5 and D8 are how you size a flexibility opportunity. D6–D7 are the Marktkommunikation funnel the JD explicitly names. D9–D10 are window functions and pivots, the two things a SQL screen always checks.

Stuck on syntax is fine — look it up. Stuck on *what to compute* is the thing to notice.
