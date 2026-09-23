-- ============================================================================
-- 04_pm_questions.sql  ·  THE TEN QUESTIONS A TARIFF PM ACTUALLY ASKS
-- ----------------------------------------------------------------------------
-- Each block is run separately by 03_answer_questions.py, which prints the
-- result and the "so what". Read the comment before each query out loud -- the
-- framing is what gets judged, not the SQL.
-- ============================================================================

-- Q1 ------------------------------------------------------------------------
-- "How long does it take from signature to first supplied kWh, and which DSO
--  is costing us the most days?"  This is the JD's "faster, more reliable".
SELECT dso_name, switches, first_time_right_pct, median_days_to_supply,
       worst_days_to_supply, total_rejects, stuck_cases, most_common_reject
FROM gold_dso_scorecard ORDER BY median_days_to_supply DESC;

-- Q2 ------------------------------------------------------------------------
-- "What share of switches succeed first time, and what are the top rejection
--  causes? Fix the cause, not the case."
SELECT COALESCE(first_reject_note,'(no rejection)') AS reject_cause,
       COUNT(*)                                          AS customers,
       ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1)     AS share_pct,
       ROUND(AVG(days_to_supply),1)                      AS avg_days_to_supply
FROM gold_mako_funnel GROUP BY 1 ORDER BY customers DESC;

-- Q3 ------------------------------------------------------------------------
-- "Where do the days actually go? Split the funnel into its hops so we know
--  whether the problem is us, the DSO, or the statutory waiting period."
SELECT ROUND(AVG(DATEDIFF('day', contract_signed_at, first_utilmd_at)),1) AS us_signature_to_utilmd,
       ROUND(AVG(days_utilmd_to_ack),1)                                   AS dso_utilmd_to_ack,
       ROUND(AVG(days_ack_to_supply),1)                                   AS statutory_ack_to_supply,
       ROUND(AVG(days_to_supply),1)                                       AS total_to_supply,
       ROUND(AVG(days_to_first_invoice - days_to_supply),1)               AS supply_to_first_invoice
FROM gold_mako_funnel WHERE supply_start_at IS NOT NULL;

-- Q4 ------------------------------------------------------------------------
-- "Which segments actually save money on dynamic vs fixed, and how much?
--  If a segment loses money we are selling them the wrong product."
SELECT segment,
       COUNT(DISTINCT malo_id)                       AS customers,
       ROUND(SUM(kwh_import),0)                      AS kwh_observed,
       ROUND(SUM(fixed_bill_eur),2)                  AS fixed_bill_eur,
       ROUND(SUM(dynamic_bill_eur),2)                AS dynamic_bill_eur,
       ROUND(SUM(saving_vs_fixed_eur),2)             AS saving_eur,
       ROUND(100.0*SUM(saving_vs_fixed_eur)/NULLIF(SUM(fixed_bill_eur),0),2) AS saving_pct,
       ROUND(AVG(realised_to_average_ratio),4)       AS avg_realised_to_average
FROM gold_customer_month GROUP BY 1 ORDER BY saving_pct DESC;

-- Q5 ------------------------------------------------------------------------
-- "Is optimisation working? realised/average < 1.00 means the customer buys
--  disproportionately in cheap quarter-hours. > 1.00 means they are WORSE than
--  a flat consumer and a dynamic tariff is actively harming them."
SELECT segment,
       COUNT(*)                                                   AS customers,
       ROUND(MIN(realised_to_average_ratio),4)                     AS best_ratio,
       ROUND(MEDIAN(realised_to_average_ratio),4)                  AS median_ratio,
       ROUND(MAX(realised_to_average_ratio),4)                     AS worst_ratio,
       COUNT(*) FILTER (WHERE realised_to_average_ratio > 1.0)     AS customers_worse_than_flat
FROM gold_customer_summary GROUP BY 1 ORDER BY median_ratio;

-- Q6 ------------------------------------------------------------------------
-- "How much of the bill is even exposed to the market? This is the number that
--  stops us over-promising savings -- the #1 churn driver in this segment."
SELECT ROUND(AVG(commodity_share_of_net_pct),1)                 AS commodity_share_of_net_bill_pct,
       ROUND(100-AVG(commodity_share_of_net_pct),1)              AS untouchable_grid_and_levies_pct,
       ROUND(AVG(saving_pct),2)                                  AS actual_avg_saving_pct,
       'A 30% load shift cannot yield a 30% bill cut -- only ~this share moves' AS reality_check
FROM gold_customer_month;

-- Q7 ------------------------------------------------------------------------
-- "Negative prices: how often, and did our customers capture any of it?
--  If capture is near zero, the HEMS is not doing its job."
SELECT COUNT(*) FILTER (WHERE is_negative_price)                       AS negative_price_intervals,
       ROUND(100.0*COUNT(*) FILTER (WHERE is_negative_price)/COUNT(*),2) AS pct_of_intervals,
       ROUND(SUM(kwh_import) FILTER (WHERE is_negative_price),1)        AS kwh_bought_at_negative,
       ROUND(100.0*SUM(kwh_import) FILTER (WHERE is_negative_price)
             /NULLIF(SUM(kwh_import),0),2)                             AS pct_of_volume,
       ROUND(SUM(-kwh_import*spot_ct_kwh/100.0) FILTER (WHERE is_negative_price),2) AS credit_earned_eur
FROM gold_interval;

-- Q8 ------------------------------------------------------------------------
-- "Gross margin per customer per year and CAC payback, by segment. Which
--  segment should sales be pushing?"
SELECT segment,
       COUNT(*)                                       AS customers,
       ROUND(AVG(controllable_kw),1)                   AS avg_controllable_kw,
       ROUND(AVG(gross_margin_eur_year),2)             AS avg_gross_margin_eur_year,
       ROUND(AVG(cac_payback_months),1)                AS avg_cac_payback_months
FROM gold_customer_summary GROUP BY 1 ORDER BY avg_gross_margin_eur_year DESC;

-- Q9 ------------------------------------------------------------------------
-- "Attach rate: what share of the hardware base is also on our tariff, and
--  what share is on the DYNAMIC tariff? The core metric of a bundled model."
SELECT CASE WHEN segment='no_hardware' THEN 'no hardware' ELSE 'has hardware' END AS base,
       COUNT(*)                                                          AS customers,
       COUNT(*) FILTER (WHERE tariff_type='DYNAMIC')                     AS on_dynamic,
       ROUND(100.0*COUNT(*) FILTER (WHERE tariff_type='DYNAMIC')/COUNT(*),1) AS dynamic_attach_pct
FROM gold_customer_summary GROUP BY 1;

-- Q10 -----------------------------------------------------------------------
-- "Does a failed switch predict a bad start? Join the operational funnel to the
--  commercial outcome -- this is the query that turns an ops metric into a
--  business case."
SELECT CASE WHEN f.reject_count = 0 THEN 'clean switch' ELSE 'had >=1 rejection' END AS cohort,
       COUNT(*)                                          AS customers,
       ROUND(AVG(f.days_to_supply),1)                     AS avg_days_to_supply,
       ROUND(AVG(f.days_to_first_invoice),1)              AS avg_days_to_first_invoice,
       COUNT(*) FILTER (WHERE f.supplied_but_never_invoiced) AS never_invoiced,
       ROUND(AVG(s.gross_margin_eur_year),2)              AS avg_margin_eur_year,
       ROUND(AVG(f.days_to_supply) * ROUND(AVG(s.gross_margin_eur_year),2)/365.0,2)
                                                          AS revenue_delayed_eur_per_customer
FROM gold_mako_funnel f
LEFT JOIN gold_customer_summary s USING (malo_id)
GROUP BY 1 ORDER BY 1;
