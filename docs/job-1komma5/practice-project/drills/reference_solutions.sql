-- DO NOT OPEN UNTIL YOU HAVE TRIED. The checker reads this to derive expected
-- answers at runtime, so it always matches your regenerated data.

-- D1
SELECT COUNT(*) AS duplicate_rows
FROM (SELECT malo_id, ts_local_naive, COUNT(*) c FROM stg_meter
      WHERE ts_local_naive IS NOT NULL GROUP BY 1,2 HAVING COUNT(*)>1) t;

-- D2
SELECT COUNT(*) AS missing_intervals
FROM silver_calendar cal
LEFT JOIN silver_meter m
       ON m.ts_utc = cal.ts_utc
      AND m.malo_id = (SELECT MIN(malo_id) FROM silver_customers)
WHERE cal.local_date BETWEEN DATE '2025-03-01' AND DATE '2025-03-31'
  AND m.malo_id IS NULL;

-- D3
SELECT ROUND(SUM(spot_ct_kwh*kwh_import)/SUM(kwh_import),4) AS vwap_ct_kwh,
       ROUND(AVG(spot_ct_kwh),4)                            AS simple_avg_ct_kwh
FROM gold_interval WHERE segment='PV_battery_HP';

-- D4
SELECT ts_local, ROUND(price_eur_mwh,2) AS price_eur_mwh
FROM silver_prices ORDER BY price_eur_mwh DESC LIMIT 5;

-- D5
SELECT DATE_TRUNC('month', local_date) AS month,
       COUNT(*) FILTER (WHERE is_negative_price) AS negative_mtus
FROM silver_prices GROUP BY 1 HAVING COUNT(*) FILTER (WHERE is_negative_price) > 0
ORDER BY 1;

-- D6
SELECT COUNT(*) AS rejected_customers,
       ROUND(AVG(days_to_supply),2) AS avg_days_to_supply
FROM gold_mako_funnel WHERE reject_count > 0;

-- D7
SELECT dso_name,
       ROUND(100.0*COUNT(*) FILTER (WHERE reject_count=0)/COUNT(*),2) AS first_time_right_pct
FROM gold_mako_funnel GROUP BY 1 ORDER BY dso_name;

-- D8
SELECT local_date, ROUND(MAX(spot_ct_kwh)-MIN(spot_ct_kwh),3) AS spread_ct_kwh
FROM silver_prices GROUP BY 1 ORDER BY spread_ct_kwh DESC LIMIT 10;

-- D9
WITH d AS (SELECT local_date, AVG(spot_ct_kwh) AS daily FROM silver_prices GROUP BY 1)
SELECT local_date, ROUND(daily,3) AS daily_ct_kwh,
       ROUND(AVG(daily) OVER (ORDER BY local_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW),3) AS roll7_ct_kwh
FROM d ORDER BY local_date LIMIT 10;

-- D10
SELECT segment,
       ROUND(AVG(saving_pct) FILTER (WHERE month=DATE '2025-02-01'),2) AS feb,
       ROUND(AVG(saving_pct) FILTER (WHERE month=DATE '2025-03-01'),2) AS mar,
       ROUND(AVG(saving_pct) FILTER (WHERE month=DATE '2025-04-01'),2) AS apr
FROM gold_customer_month GROUP BY 1 ORDER BY segment;
