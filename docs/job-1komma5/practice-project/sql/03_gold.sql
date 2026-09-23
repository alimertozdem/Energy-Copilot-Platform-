-- ============================================================================
-- 03_gold.sql  ·  BUSINESS LOGIC / MARTS
-- ----------------------------------------------------------------------------
-- Gold answers questions in business language. No cleaning happens here -- if
-- you find yourself fixing data in gold, the silver layer is incomplete.
--   Fabric equivalent: notebook 03_gold_business_logic + the semantic model.
-- ============================================================================

-- TECHNIQUE: pivot a tall parameter table into one wide row with FILTER.
-- Now every downstream query can CROSS JOIN v_params and reference a NAME
-- instead of a magic number. This is the SQL version of the spreadsheet rule
-- "no hardcoded numbers inside formulas".
CREATE OR REPLACE VIEW v_params AS
SELECT
  MAX(value) FILTER (WHERE param='dyn_markup_ct_kwh')      AS dyn_markup_ct_kwh,
  MAX(value) FILTER (WHERE param='dyn_base_fee_eur_month') AS dyn_base_fee_eur_month,
  MAX(value) FILTER (WHERE param='fix_energy_ct_kwh')      AS fix_energy_ct_kwh,
  MAX(value) FILTER (WHERE param='fix_base_fee_eur_month') AS fix_base_fee_eur_month,
  MAX(value) FILTER (WHERE param='grid_fee_ct_kwh')        AS grid_fee_ct_kwh,
  MAX(value) FILTER (WHERE param='levies_tax_ct_kwh')      AS levies_tax_ct_kwh,
  MAX(value) FILTER (WHERE param='vat_rate')               AS vat_rate,
  MAX(value) FILTER (WHERE param='cac_eur')                AS cac_eur,
  MAX(value) FILTER (WHERE param='service_cost_eur_year')  AS service_cost_eur_year,
  MAX(value) FILTER (WHERE param='flex_rev_eur_kw_year')   AS flex_rev_eur_kw_year,
  MAX(value) FILTER (WHERE param='software_fee_eur_month') AS software_fee_eur_month
FROM silver_params;

-- ============================================== 1. INTERVAL-LEVEL FACT TABLE
-- One row per customer per quarter-hour, priced under BOTH tariffs so the
-- counterfactual is always available. This is the table every question below
-- is answered from.
CREATE OR REPLACE TABLE gold_interval AS
SELECT
    m.malo_id, m.ts_utc, m.ts_local, m.local_date,
    m.segment, m.tariff_type, m.dso_name, m.city,
    m.controllable_kw, m.battery_kwh, m.pv_kwp,
    m.kwh_import, m.is_substitute_value,
    pr.spot_ct_kwh, pr.is_negative_price,

    -- the non-commodity block: identical under both tariffs, and the reason a
    -- customer who shifts 30% of load does NOT save 30% of their bill
    (pa.grid_fee_ct_kwh + pa.levies_tax_ct_kwh)                        AS non_commodity_ct_kwh,

    -- DYNAMIC: spot follows the market quarter-hour by quarter-hour
    (pr.spot_ct_kwh + pa.dyn_markup_ct_kwh)                            AS dyn_energy_ct_kwh,
    (pr.spot_ct_kwh + pa.dyn_markup_ct_kwh
       + pa.grid_fee_ct_kwh + pa.levies_tax_ct_kwh) * (1+pa.vat_rate)  AS dyn_gross_ct_kwh,
    m.kwh_import * (pr.spot_ct_kwh + pa.dyn_markup_ct_kwh
       + pa.grid_fee_ct_kwh + pa.levies_tax_ct_kwh) * (1+pa.vat_rate)
       / 100.0                                                         AS dyn_cost_eur,

    -- FIXED: same volume, flat energy component
    (pa.fix_energy_ct_kwh
       + pa.grid_fee_ct_kwh + pa.levies_tax_ct_kwh) * (1+pa.vat_rate)  AS fix_gross_ct_kwh,
    m.kwh_import * (pa.fix_energy_ct_kwh
       + pa.grid_fee_ct_kwh + pa.levies_tax_ct_kwh) * (1+pa.vat_rate)
       / 100.0                                                         AS fix_cost_eur,

    -- supplier gross margin on the commodity leg only (net of VAT)
    m.kwh_import * pa.dyn_markup_ct_kwh / 100.0                        AS dyn_margin_eur
FROM silver_meter m
JOIN silver_prices pr USING (ts_utc)
CROSS JOIN v_params pa;

-- ================================================== 2. CUSTOMER x MONTH MART
CREATE OR REPLACE TABLE gold_customer_month AS
SELECT
    g.malo_id, g.segment, g.tariff_type, g.dso_name, g.city,
    DATE_TRUNC('month', g.local_date)                     AS month,
    COUNT(*)                                              AS intervals,
    ROUND(SUM(g.kwh_import), 1)                           AS kwh_import,

    -- TECHNIQUE: volume-weighted average price. SUM(price*volume)/SUM(volume),
    -- never AVG(price). The difference between these two numbers IS the value
    -- of load shifting, and confusing them is the classic tariff-analysis error.
    ROUND(SUM(g.spot_ct_kwh * g.kwh_import) / NULLIF(SUM(g.kwh_import),0), 3) AS vwap_spot_ct_kwh,
    ROUND(AVG(g.spot_ct_kwh), 3)                          AS simple_avg_spot_ct_kwh,
    -- < 1.00 means this customer consumes disproportionately in cheap hours.
    -- This is the honest measure of whether optimisation actually works.
    ROUND( (SUM(g.spot_ct_kwh * g.kwh_import) / NULLIF(SUM(g.kwh_import),0))
           / NULLIF(AVG(g.spot_ct_kwh),0), 4)             AS realised_to_average_ratio,

    ROUND(SUM(g.dyn_cost_eur), 2)                         AS dynamic_bill_eur,
    ROUND(SUM(g.fix_cost_eur), 2)                         AS fixed_bill_eur,
    ROUND(SUM(g.fix_cost_eur) - SUM(g.dyn_cost_eur), 2)   AS saving_vs_fixed_eur,
    ROUND(100.0 * (SUM(g.fix_cost_eur) - SUM(g.dyn_cost_eur))
          / NULLIF(SUM(g.fix_cost_eur),0), 2)             AS saving_pct,
    ROUND(SUM(g.dyn_margin_eur), 2)                       AS supplier_margin_eur,

    -- how much of the bill was actually exposed to the market
    ROUND(100.0 * SUM(g.kwh_import * g.dyn_energy_ct_kwh)
          / NULLIF(SUM(g.kwh_import * (g.dyn_energy_ct_kwh + g.non_commodity_ct_kwh)),0), 1)
                                                          AS commodity_share_of_net_pct,

    -- negative-price capture: consumption that was PAID FOR by the market
    ROUND(SUM(g.kwh_import) FILTER (WHERE g.is_negative_price), 1) AS kwh_in_negative_prices,
    ROUND(SUM(-g.kwh_import * g.spot_ct_kwh / 100.0)
          FILTER (WHERE g.is_negative_price), 2)          AS negative_price_credit_eur,

    ROUND(100.0 * COUNT(*) FILTER (WHERE g.is_substitute_value) / COUNT(*), 2)
                                                          AS substitute_value_pct
FROM gold_interval g
GROUP BY 1,2,3,4,5,6;

-- ====================================== 3. CUSTOMER SUMMARY (ANNUALISED P&L)
CREATE OR REPLACE TABLE gold_customer_summary AS
WITH base AS (
    SELECT
        g.malo_id, g.segment, g.tariff_type, g.dso_name, g.city,
        c.pv_kwp, c.battery_kwh, c.has_heat_pump, c.has_ev, c.controllable_kw,
        COUNT(DISTINCT g.local_date)                       AS days_observed,
        SUM(g.kwh_import)                                  AS kwh_observed,
        SUM(g.dyn_cost_eur)                                AS dyn_bill_observed,
        SUM(g.fix_cost_eur)                                AS fix_bill_observed,
        SUM(g.dyn_margin_eur)                              AS margin_observed,
        SUM(g.spot_ct_kwh*g.kwh_import)/NULLIF(SUM(g.kwh_import),0) AS vwap,
        AVG(g.spot_ct_kwh)                                 AS avg_spot
    FROM gold_interval g
    JOIN silver_customers c USING (malo_id)
    GROUP BY 1,2,3,4,5,6,7,8,9,10
)
SELECT
    b.*,
    -- ANNUALISATION IS AN ASSUMPTION, NOT A FACT. We observed Feb-Apr, which is
    -- a heating-heavy, low-solar window, so scaling x(365/days) OVERSTATES the
    -- annual figure. Flag it in the column name so nobody quotes it as actual.
    ROUND(b.kwh_observed      * 365.0 / b.days_observed, 0)  AS kwh_annualised_ASSUMPTION,
    ROUND(b.dyn_bill_observed * 365.0 / b.days_observed, 2)  AS dyn_bill_annualised_ASSUMPTION,
    ROUND(b.fix_bill_observed * 365.0 / b.days_observed, 2)  AS fix_bill_annualised_ASSUMPTION,
    ROUND(b.vwap / NULLIF(b.avg_spot,0), 4)                  AS realised_to_average_ratio,

    -- supplier-side annual gross margin per customer
    ROUND(b.margin_observed * 365.0 / b.days_observed
          + p.dyn_base_fee_eur_month  * 12
          + p.software_fee_eur_month   * 12
          + p.flex_rev_eur_kw_year     * b.controllable_kw
          - p.service_cost_eur_year, 2)                      AS gross_margin_eur_year,
    ROUND(p.cac_eur / NULLIF(
          (b.margin_observed * 365.0 / b.days_observed
           + p.dyn_base_fee_eur_month*12 + p.software_fee_eur_month*12
           + p.flex_rev_eur_kw_year*b.controllable_kw
           - p.service_cost_eur_year) / 12.0, 0), 1)         AS cac_payback_months
FROM base b CROSS JOIN v_params p;

-- ============================================= 4. MARKTKOMMUNIKATION FUNNEL
-- TECHNIQUE: MIN(CASE WHEN ...) collapses an event log into one row per entity
-- with a column per milestone. This is THE pattern for every funnel question.
CREATE OR REPLACE TABLE gold_mako_funnel AS
WITH stages AS (
    SELECT
        malo_id, dso_name,
        MIN(event_ts) FILTER (WHERE stage='CONTRACT_SIGNED') AS contract_signed_at,
        MIN(event_ts) FILTER (WHERE stage='UTILMD_SENT')     AS first_utilmd_at,
        MIN(event_ts) FILTER (WHERE stage='CONTRL_ACK')      AS acknowledged_at,
        MIN(event_ts) FILTER (WHERE stage='SUPPLY_START')    AS supply_start_at,
        MIN(event_ts) FILTER (WHERE stage='FIRST_INVOICE')   AS first_invoice_at,
        COUNT(*)      FILTER (WHERE stage='UTILMD_SENT')     AS utilmd_attempts,
        COUNT(*)      FILTER (WHERE stage='APERAK_REJECT')   AS reject_count,
        -- first rejection cause is the actionable one
        MIN(error_code) FILTER (WHERE stage='APERAK_REJECT') AS first_reject_code,
        MIN(note)       FILTER (WHERE stage='APERAK_REJECT') AS first_reject_note
    FROM silver_mako_events
    GROUP BY 1,2
)
SELECT
    s.*, c.segment, c.tariff_type, c.city,
    s.reject_count = 0                                          AS first_time_right,
    s.acknowledged_at IS NULL                                   AS stuck_never_acknowledged,
    s.supply_start_at IS NOT NULL AND s.first_invoice_at IS NULL AS supplied_but_never_invoiced,
    DATEDIFF('day', s.contract_signed_at, s.supply_start_at)    AS days_to_supply,
    DATEDIFF('day', s.contract_signed_at, s.first_invoice_at)   AS days_to_first_invoice,
    DATEDIFF('day', s.first_utilmd_at,   s.acknowledged_at)     AS days_utilmd_to_ack,
    DATEDIFF('day', s.acknowledged_at,   s.supply_start_at)     AS days_ack_to_supply
FROM stages s
LEFT JOIN silver_customers c USING (malo_id);

-- ================================================= 5. DSO SCORECARD
-- The operational league table. This is the artifact that gets a process fix
-- funded, because it names where the days and the money are going.
CREATE OR REPLACE TABLE gold_dso_scorecard AS
SELECT
    dso_name,
    COUNT(*)                                                       AS switches,
    ROUND(100.0*COUNT(*) FILTER (WHERE first_time_right)/COUNT(*),1) AS first_time_right_pct,
    SUM(reject_count)                                              AS total_rejects,
    ROUND(AVG(utilmd_attempts),2)                                  AS avg_utilmd_attempts,
    MEDIAN(days_to_supply)                                         AS median_days_to_supply,
    MAX(days_to_supply)                                            AS worst_days_to_supply,
    MEDIAN(days_utilmd_to_ack)                                     AS median_days_to_ack,
    COUNT(*) FILTER (WHERE stuck_never_acknowledged)               AS stuck_cases,
    COUNT(*) FILTER (WHERE supplied_but_never_invoiced)            AS uninvoiced_cases,
    MODE(first_reject_note)                                        AS most_common_reject
FROM gold_mako_funnel
GROUP BY 1 ORDER BY first_time_right_pct;

-- ============================================ 6. DATA QUALITY SCORECARD
-- Publish this next to every analysis. It is the difference between "here is a
-- number" and "here is a number and here is how much of the data it rests on".
CREATE OR REPLACE TABLE gold_data_quality AS
SELECT 'meter_rows_landed'        AS metric, (SELECT COUNT(*) FROM bronze_meter)::DOUBLE AS value, 'rows' AS unit
UNION ALL SELECT 'meter_rows_rejected',     (SELECT COUNT(*) FROM silver_meter_rejects)::DOUBLE, 'rows'
UNION ALL SELECT 'meter_rows_deduplicated', ((SELECT COUNT(*) FROM bronze_meter)
                                            -(SELECT COUNT(*) FROM silver_meter_rejects)
                                            -(SELECT COUNT(*) FROM silver_meter))::DOUBLE, 'rows'
UNION ALL SELECT 'meter_rows_usable',       (SELECT COUNT(*) FROM silver_meter)::DOUBLE, 'rows'
UNION ALL SELECT 'meter_usable_pct',        ROUND(100.0*(SELECT COUNT(*) FROM silver_meter)
                                                  /(SELECT COUNT(*) FROM bronze_meter),2), '%'
UNION ALL SELECT 'orphan_malo_rows_dropped',(SELECT COUNT(*) FROM silver_meter_rejects
                                             WHERE reject_reason='R3_orphan_malo_not_in_master')::DOUBLE,'rows'
UNION ALL SELECT 'customers_with_malformed_malo_id',
                                            (SELECT COUNT(*) FROM silver_customers WHERE malo_id_was_malformed)::DOUBLE,'customers'
UNION ALL SELECT 'customers_reporting_kW_not_kWh',
                                            (SELECT COUNT(*) FROM silver_customers WHERE reporting_unit='KW')::DOUBLE,'customers'
UNION ALL SELECT 'substitute_value_share',  (SELECT ROUND(100.0*COUNT(*) FILTER (WHERE is_substitute_value)/COUNT(*),2) FROM silver_meter),'%'
UNION ALL SELECT 'export_leaked_into_import_kwh',
                                            (SELECT ROUND(SUM(kwh_export_leaked),1) FROM silver_meter),'kWh'
UNION ALL SELECT 'mean_interval_completeness',(SELECT ROUND(AVG(completeness_pct),2) FROM qa_meter_gaps),'%'
UNION ALL SELECT 'price_mtus_missing_2025',  (SELECT SUM(missing_mtu)::DOUBLE FROM qa_price_days),'MTU'
UNION ALL SELECT 'price_days_incomplete',    (SELECT COUNT(*) FROM qa_price_days WHERE completeness<>'complete')::DOUBLE,'days';
