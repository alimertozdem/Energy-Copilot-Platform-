"""add org stripe billing columns

Adds Stripe self-serve billing state to organizations. The subscription_tier /
subscription_status / billing_email / country_code columns already exist; this
migration only adds the Stripe linkage:
  * stripe_customer_id      -- one Stripe Customer per org (created on checkout)
  * stripe_subscription_id  -- the active subscription
  * current_period_end      -- end of the current paid period (renewal/expiry)

Revision ID: a1c4e7b9d2f0
Revises: f3a9c1d40e72
Create Date: 2026-06-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1c4e7b9d2f0"
down_revision: Union[str, Sequence[str], None] = "f3a9c1d40e72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_organizations_stripe_customer_id",
        "organizations",
        ["stripe_customer_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_organizations_stripe_customer_id",
        "organizations",
        type_="unique",
    )
    op.drop_column("organizations", "current_period_end")
    op.drop_column("organizations", "stripe_subscription_id")
    op.drop_column("organizations", "stripe_customer_id")
