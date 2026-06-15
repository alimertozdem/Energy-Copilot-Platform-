"""mv_ Fabric gold materialization tables (compliance module)

Revision ID: fab1c0d3e5a7
Revises: b1e7c9d35a20
Create Date: 2026-06-15

Read-only Postgres mirror of the Fabric gold/silver columns the backend needs.
Azure Container Apps cannot reach the Fabric SQL endpoint, so a Fabric notebook
materializes these tables into Supabase; the backend reads them (fast + reachable)
with Fabric as fallback. See 50_materialize_to_postgres.ipynb (Fabric side).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "fab1c0d3e5a7"
down_revision: Union[str, Sequence[str], None] = "b1e7c9d35a20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mv_building_master",
        sa.Column("building_id", sa.Text(), primary_key=True),
        sa.Column("building_name", sa.Text(), nullable=True),
        sa.Column("building_type", sa.Text(), nullable=True),
        sa.Column("gross_floor_area_m2", sa.Float(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("country_code", sa.Text(), nullable=True),
        sa.Column("energy_certificate", sa.Text(), nullable=True),
    )
    op.create_table(
        "mv_ghg_scope",
        sa.Column("building_id", sa.Text(), nullable=False),
        sa.Column("reporting_year", sa.Integer(), nullable=False),
        sa.Column("scope1_total_tco2", sa.Float(), nullable=True),
        sa.Column("scope2_location_tco2", sa.Float(), nullable=True),
        sa.Column("scope2_market_tco2", sa.Float(), nullable=True),
        sa.Column("scope3_estimated_tco2", sa.Float(), nullable=True),
        sa.Column("total_ghg_location_tco2", sa.Float(), nullable=True),
        sa.Column("total_ghg_market_tco2", sa.Float(), nullable=True),
        sa.Column("data_quality_flag", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_mv_ghg_scope_bid_year", "mv_ghg_scope", ["building_id", "reporting_year"]
    )
    op.create_table(
        "mv_kpi_daily",
        sa.Column("building_id", sa.Text(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_consumption_kwh", sa.Float(), nullable=True),
        sa.Column("solar_self_consumed_kwh", sa.Float(), nullable=True),
    )
    op.create_index(
        "ix_mv_kpi_daily_bid_date", "mv_kpi_daily", ["building_id", "date"]
    )
    op.create_table(
        "mv_sync_log",
        sa.Column("table_name", sa.Text(), primary_key=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("mv_sync_log")
    op.drop_index("ix_mv_kpi_daily_bid_date", table_name="mv_kpi_daily")
    op.drop_table("mv_kpi_daily")
    op.drop_index("ix_mv_ghg_scope_bid_year", table_name="mv_ghg_scope")
    op.drop_table("mv_ghg_scope")
    op.drop_table("mv_building_master")
