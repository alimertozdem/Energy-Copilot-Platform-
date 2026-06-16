"""bronze_iot_readings landing table (SCADA/IoT Phase A ingestion)

Revision ID: c3d4e5f6a7b8
Revises: fab1c0d3e5a7
Create Date: 2026-06-16

Phase A edge-agent ingestion (ADR-001 scada-solar-live-ingestion): the on-site
edge agent normalizes telemetry at the edge and POSTs 5-15 min micro-batches to
POST /ingest/telemetry, which lands them here. No Event Hub / EventStream /
Eventhouse -> zero new always-on Fabric capacity. This is the Postgres landing
the backend can actually write to (Azure cannot reach the Fabric SQL endpoint).
A later loader can sync this to the Fabric Lakehouse Bronze when streaming
(Phase B) is funded.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "fab1c0d3e5a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bronze_iot_readings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # the building the agent token resolved to (provenance + security boundary)
        sa.Column("agent_building_uuid", PG_UUID(as_uuid=True), nullable=False),
        # business/fabric building id carried on the reading (e.g. "B005")
        sa.Column("building_id", sa.Text(), nullable=False),
        sa.Column("device_id", sa.Text(), nullable=False),
        sa.Column("sensor_type", sa.Text(), nullable=False),
        sa.Column("sensor_location", sa.Text(), nullable=True),
        sa.Column("reading_value", sa.Float(), nullable=True),
        sa.Column("reading_unit", sa.Text(), nullable=True),
        sa.Column("source_protocol", sa.Text(), nullable=True),
        sa.Column("reading_quality", sa.SmallInteger(), nullable=True),
        # device/source timestamp (when the reading was taken)
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        # server ingest timestamp
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # original normalized payload for audit / replay
        sa.Column("raw", JSONB(), nullable=True),
    )
    op.create_index(
        "ix_bronze_iot_readings_bid_ts",
        "bronze_iot_readings",
        ["building_id", "source_timestamp"],
    )
    op.create_index(
        "ix_bronze_iot_readings_dev_ts",
        "bronze_iot_readings",
        ["device_id", "source_timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_bronze_iot_readings_dev_ts", table_name="bronze_iot_readings")
    op.drop_index("ix_bronze_iot_readings_bid_ts", table_name="bronze_iot_readings")
    op.drop_table("bronze_iot_readings")
