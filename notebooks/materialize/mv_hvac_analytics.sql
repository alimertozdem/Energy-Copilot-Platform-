-- mv_hvac_analytics — materialized copy of Fabric gold_hvac_analytics (monthly grain)
-- Purpose: backend gold_read (pg-first/Fabric-fallback) + Page 7 (HVAC) verification.
-- Run ONCE in Supabase (SQL editor) before the 50_materialize notebook's HVAC cell.
-- Naming follows mv_ convention (drops "gold_" prefix, like mv_ghg_scope / mv_kpi_daily).
-- Grain: one row per building_id × year_month.

CREATE TABLE IF NOT EXISTS public.mv_hvac_analytics (
  building_id            text NOT NULL,
  year_month             date NOT NULL,
  reporting_year         integer,
  reporting_month        integer,
  total_consumption_kwh  double precision,
  heating_energy_kwh     double precision,
  cooling_energy_kwh     double precision,
  ventilation_kwh        double precision,
  hvac_total_kwh         double precision,
  non_hvac_kwh           double precision,
  hvac_share_pct         double precision,
  heating_share_pct      double precision,
  cooling_share_pct      double precision,
  hdd_monthly            double precision,
  cdd_monthly            double precision,
  cop_actual_avg         double precision,
  scop_rolling           double precision,
  heat_loss_kwh          double precision,
  heat_loss_kwh_m2       double precision,
  u_composite            double precision,
  insulation_score       double precision,
  hvac_efficiency_score  double precision,
  system_type            text,
  system_label           text,
  renovation_priority    text,
  renovation_reason      text,
  updated_at             timestamp without time zone,
  PRIMARY KEY (building_id, year_month)
);

COMMENT ON TABLE public.mv_hvac_analytics IS
  'Materialized copy of Fabric gold_hvac_analytics (monthly grain) for backend gold_read + Page 7 verification. Synced by notebooks/materialize/50_materialize_to_postgres.ipynb.';
