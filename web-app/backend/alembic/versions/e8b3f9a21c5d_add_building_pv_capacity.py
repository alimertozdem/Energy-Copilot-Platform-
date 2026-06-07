"""add buildings.pv_capacity_kwp

Revision ID: e8b3f9a21c5d
Revises: d5f2a8c41e6b
Create Date: 2026-05-30

Day 20 onboarding -- captures installed solar PV capacity (kWp) per building
so later solar analytics know which buildings have PV and how much. Hand-
written to mirror app/db/models/building.py exactly.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8b3f9a21c5d"
down_revision: Union[str, Sequence[str], None] = "d5f2a8c41e6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "buildings",
        sa.Column("pv_capacity_kwp", sa.Numeric(precision=10, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("buildings", "pv_capacity_kwp")
