"""add building envelope U-values + insulation_year + has_gas_heating

Revision ID: b1e7c9d35a20
Revises: f7a2b9c3e1d4
Create Date: 2026-06-13

Comprehensive onboarding (self-serve Data Score): capture the envelope U-values
(wall/roof/window), insulation year and a gas-heating flag so the GEG conformity,
EPC and CO2/Scope-1 reports can be produced. All nullable (unknown until provided).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1e7c9d35a20"
down_revision: Union[str, Sequence[str], None] = "f7a2b9c3e1d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("buildings", sa.Column("wall_u_value", sa.Numeric(5, 3), nullable=True))
    op.add_column("buildings", sa.Column("roof_u_value", sa.Numeric(5, 3), nullable=True))
    op.add_column("buildings", sa.Column("window_u_value", sa.Numeric(5, 3), nullable=True))
    op.add_column("buildings", sa.Column("insulation_year", sa.Integer(), nullable=True))
    op.add_column("buildings", sa.Column("has_gas_heating", sa.Boolean(), nullable=True))


def downgrade() -> None:
    for c in ("has_gas_heating", "insulation_year", "window_u_value", "roof_u_value", "wall_u_value"):
        op.drop_column("buildings", c)
