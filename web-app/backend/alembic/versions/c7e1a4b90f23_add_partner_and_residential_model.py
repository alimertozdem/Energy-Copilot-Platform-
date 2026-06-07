"""add partner (consultant) layer + residential unit & resident-identity tables

P1 control-plane migration for the unified 4-level access spine
(partner_org -> client_org -> building -> unit) and the residential resident layer.

Additive + zero data loss — the existing customer path is unchanged:
  * organizations.org_type   -- 'customer' (every existing org backfills here) | 'partner'
  * partner_client_link       -- delegated, revocable consultant -> client grant (the only new
                                 control-plane table the consultant layer needs)
  * units                     -- Postgres unit record; bridges to Fabric silver_unit_master
                                 via fabric_unit_id (mirrors buildings.fabric_building_id)
  * resident_identity         -- minimal-PII resident (email only); magic-link first
  * unit_resident             -- tenancy window (valid_from/valid_to) for Mieterwechsel
  * resident_invite_token     -- passwordless magic-link bound to a tenancy

Enumerated values use String columns (matching the existing subscription_tier / status / role
convention), validated at the app layer — NOT native PG enums.

Refs: docs/architecture/unified-access-model.md, docs/architecture/residential-data-model.md

Revision ID: c7e1a4b90f23
Revises: a1c4e7b9d2f0
Create Date: 2026-06-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c7e1a4b90f23"
down_revision: Union[str, Sequence[str], None] = "a1c4e7b9d2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. organizations.org_type ────────────────────────────────────────────
    # 'customer' = a tenant that owns buildings (every existing org → backfilled here,
    # zero behaviour change). 'partner' = a consultancy that manages other orgs via
    # partner_client_link. Platform-admin stays the existing users.is_platform_admin flag.
    op.add_column(
        "organizations",
        sa.Column(
            "org_type",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'customer'"),
        ),
    )

    # ── 2. partner_client_link — consultant -> client delegated, revocable grant ─
    op.create_table(
        "partner_client_link",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_org_id", sa.UUID(), nullable=False),
        sa.Column("client_org_id", sa.UUID(), nullable=False),
        # pending -> active (client must consent) -> suspended | revoked
        sa.Column("relationship_status", sa.String(length=20), nullable=False,
                  server_default=sa.text("'pending'")),
        # read_only (advisory) | full_manage
        sa.Column("scope", sa.String(length=20), nullable=False,
                  server_default=sa.text("'read_only'")),
        sa.Column("commission_model", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("invited_by_user_id", sa.UUID(), nullable=True),
        # DSGVO: the client (controller) authorises the partner (processor); set on accept.
        sa.Column("client_consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("partner_org_id <> client_org_id", name="ck_partner_client_not_self"),
    )
    op.create_index(op.f("ix_partner_client_link_partner_org_id"), "partner_client_link",
                    ["partner_org_id"], unique=False)
    op.create_index(op.f("ix_partner_client_link_client_org_id"), "partner_client_link",
                    ["client_org_id"], unique=False)
    # exactly one LIVE link per (partner, client) — partial unique where not revoked
    op.create_index(
        "uq_partner_client_live",
        "partner_client_link",
        ["partner_org_id", "client_org_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    # ── 3. units — Postgres unit record; bridges to Fabric silver_unit_master ──
    op.create_table(
        "units",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("building_id", sa.UUID(), nullable=False),
        # == silver_unit_master.unit_id (the analytics bridge; mirrors fabric_building_id)
        sa.Column("fabric_unit_id", sa.String(length=50), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=True),  # e.g. 'Whg 3.2' (manager-facing)
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_units_building_id"), "units", ["building_id"], unique=False)
    op.create_index(op.f("ix_units_fabric_unit_id"), "units", ["fabric_unit_id"], unique=True)

    # ── 4. resident_identity — minimal PII (email only); magic-link first ─────
    op.create_table(
        "resident_identity",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        # invited -> active | disabled
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'invited'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        # consumption data is NEVER stored here — it lives in the lakehouse, read via fabric_unit_id
    )
    op.create_index(op.f("ix_resident_identity_email"), "resident_identity", ["email"], unique=True)

    # ── 5. unit_resident — tenancy window (Mieterwechsel; DSGVO-scoped access) ─
    op.create_table(
        "unit_resident",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("unit_id", sa.UUID(), nullable=False),
        sa.Column("resident_identity_id", sa.UUID(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),  # move-in
        sa.Column("valid_to", sa.Date(), nullable=True),    # move-out (NULL = current tenant)
        # active | ended
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resident_identity_id"], ["resident_identity.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_unit_resident_unit_id"), "unit_resident", ["unit_id", "valid_to"], unique=False)
    op.create_index(op.f("ix_unit_resident_resident_identity_id"), "unit_resident",
                    ["resident_identity_id"], unique=False)

    # ── 6. resident_invite_token — passwordless magic-link bound to a tenancy ──
    op.create_table(
        "resident_invite_token",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("unit_resident_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),  # store a hash, never the raw token
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["unit_resident_id"], ["unit_resident.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resident_invite_token_unit_resident_id"), "resident_invite_token",
                    ["unit_resident_id"], unique=False)
    op.create_index(op.f("ix_resident_invite_token_token_hash"), "resident_invite_token",
                    ["token_hash"], unique=True)


def downgrade() -> None:
    # reverse FK order; drop_table also drops the table's indexes/constraints
    op.drop_table("resident_invite_token")
    op.drop_table("unit_resident")
    op.drop_table("resident_identity")
    op.drop_table("units")
    op.drop_table("partner_client_link")
    op.drop_column("organizations", "org_type")
