"""add pilot_requests (public "request a pilot" lead capture)

Revision ID: c2f7a9e4b610
Revises: b8f2c5a17d39
Create Date: 2026-06-06

Hand-written to mirror app/db/models/pilot.py. Public lead form — no FK to
users/orgs (submitters may not have an account yet).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = "c2f7a9e4b610"
down_revision: Union[str, Sequence[str], None] = "b8f2c5a17d39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pilot_requests",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("organization", sa.String(length=200), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("building_count", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="new"
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
    op.create_index("ix_pilot_requests_email", "pilot_requests", ["email"])
    op.create_index("ix_pilot_requests_status", "pilot_requests", ["status"])


def downgrade() -> None:
    op.drop_index("ix_pilot_requests_status", table_name="pilot_requests")
    op.drop_index("ix_pilot_requests_email", table_name="pilot_requests")
    op.drop_table("pilot_requests")
