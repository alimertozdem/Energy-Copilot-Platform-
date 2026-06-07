"""add alert_status

Revision ID: f3a9c1d40e72
Revises: e8b3f9a21c5d
Create Date: 2026-05-31

Day 31 -- backs the /alerts acknowledge overlay. Mirrors
app/db/models/alert_status.py exactly (hand-written per the project's Alembic
convention so model and migration stay in lockstep).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f3a9c1d40e72"
down_revision: Union[str, Sequence[str], None] = "e8b3f9a21c5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alert_status",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fabric_anomaly_id", sa.String(length=100), nullable=False),
        sa.Column(
            "ack_status",
            sa.String(length=20),
            server_default="new",
            nullable=False,
        ),
        sa.Column(
            "acknowledged_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["building_id"], ["buildings.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["acknowledged_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "fabric_anomaly_id",
            name="uq_alert_status_identity",
        ),
    )
    op.create_index(
        "ix_alert_status_organization_id", "alert_status", ["organization_id"]
    )
    op.create_index(
        "ix_alert_status_building_id", "alert_status", ["building_id"]
    )
    op.create_index(
        "ix_alert_status_fabric_anomaly_id",
        "alert_status",
        ["fabric_anomaly_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_alert_status_fabric_anomaly_id", table_name="alert_status"
    )
    op.drop_index("ix_alert_status_building_id", table_name="alert_status")
    op.drop_index(
        "ix_alert_status_organization_id", table_name="alert_status"
    )
    op.drop_table("alert_status")
