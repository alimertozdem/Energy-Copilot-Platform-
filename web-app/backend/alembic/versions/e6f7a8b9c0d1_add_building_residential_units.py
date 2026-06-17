"""add buildings.residential_units

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-06-17

Declared dwelling-unit count for residential buildings, captured at onboarding /
portfolio import. Sharpens the BEG/KfW subsidy cap (per Wohneinheit) in the
financing model — without it we estimate units from floor area. Nullable;
non-residential buildings leave it NULL. Hand-written to mirror
app/db/models/building.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("buildings", sa.Column("residential_units", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("buildings", "residential_units")
