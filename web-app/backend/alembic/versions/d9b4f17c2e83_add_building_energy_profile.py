"""add buildings energy-profile columns

Revision ID: d9b4f17c2e83
Revises: c7e1a4b90f23
Create Date: 2026-06-05

Richer building profile captured at onboarding (beyond floor area): declared EPC
class, heating / cooling system, occupancy pattern, floor count and typical
occupants. These power the advisor + compliance even before live Fabric data is
connected. Hand-written to mirror app/db/models/building.py exactly.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d9b4f17c2e83"
down_revision: Union[str, Sequence[str], None] = "c7e1a4b90f23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("buildings", sa.Column("epc_class", sa.String(length=2), nullable=True))
    op.add_column("buildings", sa.Column("heating_system", sa.String(length=40), nullable=True))
    op.add_column("buildings", sa.Column("cooling_system", sa.String(length=40), nullable=True))
    op.add_column("buildings", sa.Column("occupancy_pattern", sa.String(length=40), nullable=True))
    op.add_column("buildings", sa.Column("floors_above_ground", sa.Integer(), nullable=True))
    op.add_column("buildings", sa.Column("typical_occupants", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("buildings", "typical_occupants")
    op.drop_column("buildings", "floors_above_ground")
    op.drop_column("buildings", "occupancy_pattern")
    op.drop_column("buildings", "cooling_system")
    op.drop_column("buildings", "heating_system")
    op.drop_column("buildings", "epc_class")
