"""mv_iot_fdd -- Page 8 IoT FDD cost mirror (idempotent).

Revision ID: b2c9f1a4d7e3
Revises: e6f7a8b9c0d1
Create Date: 2026-06-21

Mirror of Fabric gold_iot_fdd (Page 8 single source of truth for fault/waste cost).
The table is also creatable directly via notebooks/materialize/mv_iot_fdd_create.sql
(Supabase SQL Editor). Idempotent -> safe whether or not the table already exists.
event_date kept TEXT to match the other mv_ tables.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "b2c9f1a4d7e3"
down_revision: Union[str, Sequence[str], None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DDL = """
CREATE TABLE IF NOT EXISTS mv_iot_fdd (
  building_id text NOT NULL, equipment text, equipment_type text, fault_code text,
  severity text, confidence double precision, priority_score integer, description text,
  probable_cause text, recommended_action text, occurrence_count integer,
  power_waste_kw double precision, energy_impact_kwh double precision,
  cost_eur_estimate double precision, grid_price double precision, building_type text,
  event_date text
);
CREATE INDEX IF NOT EXISTS ix_mv_iot_fdd_building ON mv_iot_fdd (building_id);
CREATE INDEX IF NOT EXISTS ix_mv_iot_fdd_event_date ON mv_iot_fdd (event_date);
"""


def upgrade() -> None:
    op.execute(_DDL)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS mv_iot_fdd")
