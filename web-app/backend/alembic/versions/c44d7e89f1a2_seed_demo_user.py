"""seed demo user for public /demo page

Revision ID: c44d7e89f1a2
Revises: b023c206267e
Create Date: 2026-05-29

Seeds:
  * 1 user: demo@energylens.eu (is_demo=True, no auth_provider rows)
  * 1 org_member: links demo_user -> SAMPLE_ORG_ID as 'viewer' (already accepted)

Why no auth_provider row?
  Demo user is backend-only. /demo public endpoints reference demo_user.id
  to set Power BI RLS effective identity. There is no login path for this
  user -- attempting to log in returns 401 (no provider record found).

Deterministic UUIDs (continuation of b023c206267e pattern):
  demo_user.id  = 00000000-0000-1000-8000-000000000002
  org_member.id = 00000000-0000-1000-8000-000000000003
"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# revision identifiers, used by Alembic.
revision: str = 'c44d7e89f1a2'
down_revision: Union[str, Sequence[str], None] = 'b023c206267e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# -----------------------------------------------------------------------------
# Deterministic IDs
# -----------------------------------------------------------------------------
DEMO_USER_ID = uuid.UUID("00000000-0000-1000-8000-000000000002")
SAMPLE_ORG_ID = uuid.UUID("00000000-0000-1000-8000-000000000001")
DEMO_MEMBER_ID = uuid.UUID("00000000-0000-1000-8000-000000000003")


# -----------------------------------------------------------------------------
# Lightweight table refs for bulk_insert
# -----------------------------------------------------------------------------
users_t = sa.table(
    "users",
    sa.column("id", PG_UUID(as_uuid=True)),
    sa.column("email", sa.String),
    sa.column("display_name", sa.String),
    sa.column("is_active", sa.Boolean),
    sa.column("is_demo", sa.Boolean),
    sa.column("is_platform_admin", sa.Boolean),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

org_members_t = sa.table(
    "org_members",
    sa.column("id", PG_UUID(as_uuid=True)),
    sa.column("organization_id", PG_UUID(as_uuid=True)),
    sa.column("user_id", PG_UUID(as_uuid=True)),
    sa.column("role", sa.String),
    sa.column("invitation_accepted_at", sa.DateTime(timezone=True)),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------------------
    # 1) Demo user row
    #    - No UserAuthProvider rows -> login is impossible
    #    - is_demo=True flag drives backend middleware (block all writes)
    # ---------------------------------------------------------------------
    op.bulk_insert(users_t, [{
        "id": DEMO_USER_ID,
        "email": "demo@energylens.eu",
        "display_name": "Demo User",
        "is_active": True,
        "is_demo": True,
        "is_platform_admin": False,
        "created_at": now,
        "updated_at": now,
    }])

    # ---------------------------------------------------------------------
    # 2) OrgMember linking demo_user -> sample org as 'viewer'
    #    invitation_accepted_at is set so this is a fully active membership
    # ---------------------------------------------------------------------
    op.bulk_insert(org_members_t, [{
        "id": DEMO_MEMBER_ID,
        "organization_id": SAMPLE_ORG_ID,
        "user_id": DEMO_USER_ID,
        "role": "viewer",
        "invitation_accepted_at": now,
        "created_at": now,
        "updated_at": now,
    }])


def downgrade() -> None:
    # Reverse order: org_members -> users
    op.execute(
        "DELETE FROM org_members WHERE user_id = "
        "'00000000-0000-1000-8000-000000000002'"
    )
    op.execute(
        "DELETE FROM users WHERE id = "
        "'00000000-0000-1000-8000-000000000002'"
    )
