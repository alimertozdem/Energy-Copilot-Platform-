-- mv_iot_fdd — Page 8 IoT fault-detection cost mirror (Supabase).
-- WHERE TO RUN: Supabase Dashboard -> SQL Editor -> paste -> Run.
-- Safe to run more than once (IF NOT EXISTS). After this, populate it from Fabric
-- with notebooks/materialize/cell_mv_iot_fdd.py.

CREATE TABLE IF NOT EXISTS mv_iot_fdd (
  building_id          text NOT NULL,
  equipment            text,
  equipment_type       text,
  fault_code           text,
  severity             text,
  confidence           double precision,
  priority_score       integer,
  description          text,
  probable_cause       text,
  recommended_action   text,
  occurrence_count     integer,
  power_waste_kw       double precision,
  energy_impact_kwh    double precision,
  cost_eur_estimate    double precision,
  grid_price           double precision,
  building_type        text,
  event_date           text
);

CREATE INDEX IF NOT EXISTS ix_mv_iot_fdd_building   ON mv_iot_fdd (building_id);
CREATE INDEX IF NOT EXISTS ix_mv_iot_fdd_event_date ON mv_iot_fdd (event_date);
