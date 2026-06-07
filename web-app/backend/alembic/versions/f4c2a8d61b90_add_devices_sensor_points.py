"""add devices + sensor_points (Tier-2/3 connection wiring)

Revision ID: f4c2a8d61b90
Revises: e1a7c4f29b80
Create Date: 2026-06-05

Each Device a building exposes (protocol + JSONB connection config) and each
SensorPoint on it (point_ref -> normalized sensor_type + zone). Hand-written to
mirror app/db/models/connection.py exactly.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = "f4c2a8d61b90"
down_revision: Union[str, Sequence[str], None] = "e1a7c4f29b80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "building_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("buildings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("protocol", sa.String(length=20), nullable=False),
        sa.Column("connection_config", JSONB, nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("template_key", sa.String(length=60), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_devices_building_id", "devices", ["building_id"])

    op.create_table(
        "sensor_points",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "device_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("devices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("point_ref", sa.String(length=120), nullable=False),
        sa.Column("sensor_type", sa.String(length=40), nullable=False),
        sa.Column("zone", sa.String(length=80), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("scale", sa.Numeric(precision=12, scale=6), nullable=False, server_default="1"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("device_id", "point_ref", name="uq_sensor_point_ref"),
    )
    op.create_index("ix_sensor_points_device_id", "sensor_points", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_sensor_points_device_id", table_name="sensor_points")
    op.drop_table("sensor_points")
    op.drop_index("ix_devices_building_id", table_name="devices")
    op.drop_table("devices")
