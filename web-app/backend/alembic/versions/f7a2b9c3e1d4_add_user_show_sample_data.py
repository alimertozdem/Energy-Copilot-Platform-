"""add users.show_sample_data (per-user sample/demo building visibility toggle)

Revision ID: f7a2b9c3e1d4
Revises: e5c3a9b71d42
Create Date: 2026-06-12

Sample/demo building visibility was always-on for every user (building repo
_visible_org_filter). This makes it a per-user choice: default true (no regression),
and the user can turn it off to see only their own buildings, or back on to load the
sample buildings (e.g. to preview/run the reports).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f7a2b9c3e1d4"
down_revision: Union[str, Sequence[str], None] = "e5c3a9b71d42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "show_sample_data",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "show_sample_data")
