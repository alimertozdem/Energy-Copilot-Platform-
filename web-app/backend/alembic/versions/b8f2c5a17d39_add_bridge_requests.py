"""add bridge_requests (self-serve Fabric bridging -- Access Layer 3)

Revision ID: b8f2c5a17d39
Revises: a7d3e9f10c42
Create Date: 2026-06-06

A customer's request to unlock the full Fabric analytics for a pending building.
Hand-written to mirror app/db/models/bridge.py. A partial unique index enforces
at most one *pending* request per building.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = "b8f2c5a17d39"
down_revision: Union[str, Sequence[str], None] = "a7d3e9f10c42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bridge_requests",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "building_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("buildings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "requested_by",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("target_tier", sa.String(length=20), nullable=False, server_default="full"),
        sa.Column("readiness", JSONB, nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "resolved_by",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_bridge_requests_building_id", "bridge_requests", ["building_id"])
    op.create_index("ix_bridge_requests_organization_id", "bridge_requests", ["organization_id"])
    op.create_index("ix_bridge_requests_status", "bridge_requests", ["status"])
    # At most one OPEN (pending) request per building.
    op.create_index(
        "uq_bridge_requests_one_pending",
        "bridge_requests",
        ["building_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("uq_bridge_requests_one_pending", table_name="bridge_requests")
    op.drop_index("ix_bridge_requests_status", table_name="bridge_requests")
    op.drop_index("ix_bridge_requests_organization_id", table_name="bridge_requests")
    op.drop_index("ix_bridge_requests_building_id", table_name="bridge_requests")
    op.drop_table("bridge_requests")
