"""add installer_requests (Execution Marketplace Phase 0 lead capture)

Revision ID: d4b1f8c2e9a7
Revises: c2f7a9e4b610
Create Date: 2026-06-12

Hand-written to mirror app/db/models/installer.py. Authenticated lead capture --
FK to organizations + users; the founder brokers from /admin. Phase 1+ deferred.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "d4b1f8c2e9a7"
down_revision: Union[str, Sequence[str], None] = "c2f7a9e4b610"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "installer_requests",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "requested_by_user_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("fabric_building_id", sa.String(length=100), nullable=False),
        sa.Column("building_name", sa.String(length=255), nullable=True),
        sa.Column("action_type", sa.String(length=80), nullable=True),
        sa.Column("measure_label", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="requested"
        ),
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
    )
    op.create_index(
        "ix_installer_requests_organization_id",
        "installer_requests",
        ["organization_id"],
    )
    op.create_index(
        "ix_installer_requests_fabric_building_id",
        "installer_requests",
        ["fabric_building_id"],
    )
    op.create_index(
        "ix_installer_requests_status", "installer_requests", ["status"]
    )


def downgrade() -> None:
    op.drop_index("ix_installer_requests_status", table_name="installer_requests")
    op.drop_index(
        "ix_installer_requests_fabric_building_id", table_name="installer_requests"
    )
    op.drop_index(
        "ix_installer_requests_organization_id", table_name="installer_requests"
    )
    op.drop_table("installer_requests")
