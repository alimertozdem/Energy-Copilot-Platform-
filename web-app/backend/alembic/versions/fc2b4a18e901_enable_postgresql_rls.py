"""Enable PostgreSQL Row Level Security (RLS) on tenant tables.

Revision ID: fc2b4a18e901
Revises: fab1c0d3e5a7
Create Date: 2026-09-23
"""
from typing import Sequence, Union
from alembic import op

revision: str = "fc2b4a18e901"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tablolarda RLS'i etkinleştir
    op.execute("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE buildings ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE building_consumption ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE alert_status ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE bronze_iot_readings ENABLE ROW LEVEL SECURITY;")

    # 2. Binalar için izolasyon kuralı:
    # Kullanıcı yalnızca kendi organizasyonunun binalarını veya demo binaları görebilir
    op.execute("""
        CREATE POLICY tenant_isolation_buildings ON buildings
        FOR ALL
        USING (
            organization_id IN (
                SELECT organization_id FROM org_members 
                WHERE user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            )
            OR organization_id IN (
                SELECT id FROM organizations WHERE is_sample = true
            )
        );
    """)

    # 3. Tüketim verileri için izolasyon kuralı
    op.execute("""
        CREATE POLICY tenant_isolation_consumption ON building_consumption
        FOR ALL
        USING (
            building_id IN (
                SELECT id FROM buildings
            )
        );
    """)


def downgrade() -> None:
    # Geri alma (rollback)
    op.execute("DROP POLICY IF EXISTS tenant_isolation_consumption ON building_consumption;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_buildings ON buildings;")
    op.execute("ALTER TABLE bronze_iot_readings DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE alert_status DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE building_consumption DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE buildings DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;")
