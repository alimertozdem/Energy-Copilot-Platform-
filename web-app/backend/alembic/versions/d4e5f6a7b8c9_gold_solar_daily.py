"""gold_solar_daily -- telemetry-derived daily solar KPIs (Phase A loader)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-16

Postgres-first roll-up of bronze_iot_readings (real inverter/SCADA telemetry)
into daily solar KPIs, so /solar can show REAL generation + PR for connected
buildings with no Fabric (ADR-001 Phase A). self_consumed/exported stay NULL
until a building load meter is connected (inverter telemetry can't split them).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gold_solar_daily",
        sa.Column("building_id", sa.Text(), primary_key=True),
        sa.Column("date", sa.Date(), primary_key=True),
        sa.Column("solar_generated_kwh", sa.Float(), nullable=True),
        sa.Column("solar_self_consumed_kwh", sa.Float(), nullable=True),
        sa.Column("solar_exported_kwh", sa.Float(), nullable=True),
        sa.Column("avg_solar_pr", sa.Float(), nullable=True),
        sa.Column("in_plane_irradiation_kwh_m2", sa.Float(), nullable=True),
        sa.Column("pv_capacity_kwp", sa.Float(), nullable=True),
        sa.Column("reading_count", sa.Integer(), nullable=True),
        sa.Column("has_load_meter", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("generation_method", sa.Text(), nullable=True),
        sa.Column("data_source", sa.Text(), server_default="telemetry", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("gold_solar_daily")
