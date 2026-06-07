"""add agent_tokens (edge-agent credentials)

Revision ID: a7d3e9f10c42
Revises: f4c2a8d61b90
Create Date: 2026-06-05

Building-scoped tokens an edge gateway uses to pull its node-map from
/agent/config. Stored hashed (SHA-256). Hand-written to mirror
app/db/models/agent.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = "a7d3e9f10c42"
down_revision: Union[str, Sequence[str], None] = "f4c2a8d61b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_tokens",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "building_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("buildings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("token_prefix", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False, server_default="edge agent"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_agent_tokens_hash"),
    )
    op.create_index("ix_agent_tokens_building_id", "agent_tokens", ["building_id"])
    op.create_index("ix_agent_tokens_token_hash", "agent_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_agent_tokens_token_hash", table_name="agent_tokens")
    op.drop_index("ix_agent_tokens_building_id", table_name="agent_tokens")
    op.drop_table("agent_tokens")
