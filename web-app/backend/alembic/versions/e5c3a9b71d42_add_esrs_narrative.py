"""add esrs_narrative (per-org ESRS E-1 qualitative narrative)

Revision ID: e5c3a9b71d42
Revises: d4b1f8c2e9a7
Create Date: 2026-06-12

Hand-written to mirror app/db/models/esrs_narrative.py. Stores the company-written
narrative for the ESRS E-1 qualitative disclosures (E1-1..E1-4, E1-7..E1-9), keyed by
organization + datapoint code. FK to organizations + users.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "e5c3a9b71d42"
down_revision: Union[str, Sequence[str], None] = "d4b1f8c2e9a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "esrs_narrative",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("datapoint_key", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("reporting_year", sa.Integer(), nullable=True),
        sa.Column(
            "updated_by_user_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
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
        sa.UniqueConstraint(
            "organization_id", "datapoint_key", name="uq_esrs_narrative_identity"
        ),
    )
    op.create_index(
        "ix_esrs_narrative_organization_id", "esrs_narrative", ["organization_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_esrs_narrative_organization_id", table_name="esrs_narrative")
    op.drop_table("esrs_narrative")
