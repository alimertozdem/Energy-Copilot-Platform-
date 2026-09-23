-- ============================================================================
-- 01_bronze.sql  ·  RAW LANDING LAYER
-- ----------------------------------------------------------------------------
-- Rule of the bronze layer: load everything AS TEXT, change nothing, drop
-- nothing. If you cast or filter here you destroy the evidence you need to
-- explain a number later. Every real data platform works this way.
--   Fabric equivalent: notebook 01_bronze_ingestion writing Delta tables.
-- ============================================================================

CREATE OR REPLACE TABLE bronze_prices AS
SELECT * FROM read_csv('../data/raw_day_ahead_prices.csv',
                       all_varchar = true, header = true);

CREATE OR REPLACE TABLE bronze_meter AS
SELECT * FROM read_csv('../data/raw_meter_readings.csv',
                       all_varchar = true, header = true);

CREATE OR REPLACE TABLE bronze_customers AS
SELECT * FROM read_csv('../data/raw_customers.csv',
                       all_varchar = true, header = true);

CREATE OR REPLACE TABLE bronze_mako AS
SELECT * FROM read_csv('../data/raw_mako_events.csv',
                       all_varchar = true, header = true);

-- Business parameters live in a TABLE, never inside a formula or a WHERE clause.
-- Same discipline rule as the spreadsheet model: one place, sourced, auditable.
CREATE OR REPLACE TABLE silver_params AS
SELECT * FROM (VALUES
  ('dyn_markup_ct_kwh',      1.80, 'Supplier markup on spot, dynamic tariff'),
  ('dyn_base_fee_eur_month', 12.99,'Monthly base fee, dynamic tariff'),
  ('fix_energy_ct_kwh',      15.40,'Fixed-tariff energy component (procurement+sales+margin)'),
  ('fix_base_fee_eur_month', 9.90, 'Monthly base fee, fixed tariff'),
  ('grid_fee_ct_kwh',         9.26,'Netzentgelt, DE household average 2026'),
  ('levies_tax_ct_kwh',      12.61,'Stromsteuer + KWKG + 19 StromNEV + offshore + concession'),
  ('vat_rate',                0.19,'German VAT'),
  ('cac_eur',               420.00,'Blended customer acquisition cost (assumption)'),
  ('service_cost_eur_year',  28.00,'Support + billing cost per customer per year (assumption)'),
  ('flex_rev_eur_kw_year',   65.00,'Flexibility revenue per controllable kW per year (assumption)'),
  ('software_fee_eur_month',  9.90,'Heartbeat-style HEMS software fee (assumption)')
) AS t(param, value, note);
