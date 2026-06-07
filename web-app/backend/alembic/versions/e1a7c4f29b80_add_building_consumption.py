"""add building_consumption table

Revision ID: e1a7c4f29b80
Revises: d9b4f17c2e83
Create Date: 2026-06-05

Uploaded / manually-entered monthly consumption — the baseline a customer can
provide (CSV / bills) before live Fabric data is connected. One row per month
per building. Hand-written to mirror app/db/models/building.py exactly.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = "e1a7c4f29b80"
down_revision: Union[str, Sequence[str], None] = "d9b4f17c2e83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "building_consumption",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "building_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("buildings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("energy_kwh", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("cost_eur", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="csv"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("building_id", "period", name="uq_building_consumption_period"),
    )
    op.create_index(
        "ix_building_consumption_building_id",
        "building_consumption",
        ["building_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_building_consumption_building_id", table_name="building_consumption")
    op.drop_table("building_consumption")
