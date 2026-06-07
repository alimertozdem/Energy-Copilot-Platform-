"""seed sample workspace and 10 buildings

Revision ID: b023c206267e
Revises: 7cfe01762f07
Create Date: 2026-05-27 15:15:08.274838

Seeds:
  * 1 organization: "EnergyLens Sample Portfolio" (is_sample=True)
  * 10 buildings:   B001-B010 (Page 7 extreme showcase set)
  * 30 building_modules: 3 modules per building (meters / iot / battery)

Source of truth for metadata: sample-data/building_master.csv

Deterministic UUIDs (00000000-0000-1000-8000-XXXXXXXXXXXX pattern):
  * 0001         -> SAMPLE_ORG_ID
  * 0101..010A   -> Buildings B001..B010
  * 02XX         -> 'meters'  module for building XX
  * 03XX         -> 'iot'     module for building XX
  * 04XX         -> 'battery' module for building XX

Module enablement rule (approved 2026-05-27):
  meters  -> always True                (Pages 1-7 available everywhere)
  iot     -> tier IN ('Insight','Copilot')   (Page 8 — IoT Monitoring)
  battery -> has_battery=True from CSV       (Page 9 — Battery Strategy)
"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# revision identifiers, used by Alembic.
revision: str = 'b023c206267e'
down_revision: Union[str, Sequence[str], None] = '7cfe01762f07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# -----------------------------------------------------------------------------
# Deterministic IDs
# -----------------------------------------------------------------------------
SAMPLE_ORG_ID = uuid.UUID("00000000-0000-1000-8000-000000000001")

# Building IDs (hex 0101..010A)
B_IDS = {
    "B001": uuid.UUID("00000000-0000-1000-8000-000000000101"),
    "B002": uuid.UUID("00000000-0000-1000-8000-000000000102"),
    "B003": uuid.UUID("00000000-0000-1000-8000-000000000103"),
    "B004": uuid.UUID("00000000-0000-1000-8000-000000000104"),
    "B005": uuid.UUID("00000000-0000-1000-8000-000000000105"),
    "B006": uuid.UUID("00000000-0000-1000-8000-000000000106"),
    "B007": uuid.UUID("00000000-0000-1000-8000-000000000107"),
    "B008": uuid.UUID("00000000-0000-1000-8000-000000000108"),
    "B009": uuid.UUID("00000000-0000-1000-8000-000000000109"),
    "B010": uuid.UUID("00000000-0000-1000-8000-00000000010a"),
}

# Module ID helper: 02XX=meters, 03XX=iot, 04XX=battery
def _mod_id(prefix: str, building_seq_hex: str) -> uuid.UUID:
    return uuid.UUID(f"00000000-0000-1000-8000-00000000{prefix}{building_seq_hex}")


# -----------------------------------------------------------------------------
# Lightweight table refs for bulk_insert
# -----------------------------------------------------------------------------
organizations_t = sa.table(
    "organizations",
    sa.column("id", PG_UUID(as_uuid=True)),
    sa.column("name", sa.String),
    sa.column("slug", sa.String),
    sa.column("subscription_tier", sa.String),
    sa.column("subscription_status", sa.String),
    sa.column("is_sample", sa.Boolean),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

buildings_t = sa.table(
    "buildings",
    sa.column("id", PG_UUID(as_uuid=True)),
    sa.column("organization_id", PG_UUID(as_uuid=True)),
    sa.column("fabric_building_id", sa.String),
    sa.column("name", sa.String),
    sa.column("city", sa.String),
    sa.column("country_code", sa.String),
    sa.column("building_type", sa.String),
    sa.column("floor_area_m2", sa.Numeric),
    sa.column("construction_year", sa.Integer),
    sa.column("timezone", sa.String),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

building_modules_t = sa.table(
    "building_modules",
    sa.column("id", PG_UUID(as_uuid=True)),
    sa.column("building_id", PG_UUID(as_uuid=True)),
    sa.column("module_key", sa.String),
    sa.column("enabled", sa.Boolean),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


# -----------------------------------------------------------------------------
# Building metadata (from sample-data/building_master.csv)
# (fabric_building_id, seq_hex, name, city, country, type, area, year, tz, tier, has_battery)
# -----------------------------------------------------------------------------
BUILDINGS = [
    ("B001", "01", "Berliner Bürogebäude Alpha",         "Berlin",     "DE", "Office",      5200,  2005, "Europe/Berlin",     "Monitor", True),
    ("B002", "02", "Istanbul Ticaret Merkezi Beta",      "Istanbul",   "TR", "Retail",      8500,  1998, "Europe/Istanbul",   "Insight", False),
    ("B003", "03", "Hamburg Logistics Hub Gamma",        "Hamburg",    "DE", "Logistics",  12000,  2018, "Europe/Berlin",     "Copilot", True),
    ("B004", "04", "Wien Grand Hotel Delta",             "Vienna",     "AT", "Hotel",       7800,  2008, "Europe/Vienna",     "Insight", False),
    ("B005", "05", "Frankfurt Klinikum Epsilon",         "Frankfurt",  "DE", "Healthcare", 15000,  2000, "Europe/Berlin",     "Copilot", True),
    ("B006", "06", "Amsterdam Universiteit Zeta",        "Amsterdam",  "NL", "Education",   9500,  1985, "Europe/Amsterdam",  "Monitor", False),
    ("B007", "07", "Copenhagen Net-Plus HQ Eta",         "Copenhagen", "DK", "Office",      6500,  2023, "Europe/Copenhagen", "Copilot", True),
    ("B008", "08", "Leipzig Plattenbau Theta",           "Leipzig",    "DE", "Office",      9200,  1968, "Europe/Berlin",     "Monitor", False),
    ("B009", "09", "Frankfurt Datacenter Iota",          "Frankfurt",  "DE", "Data_Center", 9500,  2020, "Europe/Berlin",     "Copilot", False),
    ("B010", "0a", "Stockholm Karolinska BioLab Kappa",  "Stockholm",  "SE", "Lab",         4800,  2018, "Europe/Stockholm",  "Copilot", False),
]


def upgrade() -> None:
    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------------------
    # 1) Sample organization
    # ---------------------------------------------------------------------
    op.bulk_insert(organizations_t, [{
        "id": SAMPLE_ORG_ID,
        "name": "EnergyLens Sample Portfolio",
        "slug": "energylens-sample-portfolio",
        "subscription_tier": "free",
        "subscription_status": "active",
        "is_sample": True,
        "created_at": now,
        "updated_at": now,
    }])

    # ---------------------------------------------------------------------
    # 2) 10 buildings
    # ---------------------------------------------------------------------
    building_rows = []
    for fabric_id, seq_hex, name, city, country, btype, area, year, tz, tier, has_bat in BUILDINGS:
        building_rows.append({
            "id": B_IDS[fabric_id],
            "organization_id": SAMPLE_ORG_ID,
            "fabric_building_id": fabric_id,
            "name": name,
            "city": city,
            "country_code": country,
            "building_type": btype,
            "floor_area_m2": area,
            "construction_year": year,
            "timezone": tz,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
    op.bulk_insert(buildings_t, building_rows)

    # ---------------------------------------------------------------------
    # 3) Building modules (30 rows: 3 per building)
    #    meters  -> always True
    #    iot     -> tier IN ('Insight','Copilot')
    #    battery -> has_battery
    # ---------------------------------------------------------------------
    module_rows = []
    for fabric_id, seq_hex, _name, _city, _ctry, _btype, _area, _year, _tz, tier, has_bat in BUILDINGS:
        b_id = B_IDS[fabric_id]
        iot_enabled = tier in ("Insight", "Copilot")
        module_rows.extend([
            {
                "id": _mod_id("02", seq_hex),
                "building_id": b_id,
                "module_key": "meters",
                "enabled": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": _mod_id("03", seq_hex),
                "building_id": b_id,
                "module_key": "iot",
                "enabled": iot_enabled,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": _mod_id("04", seq_hex),
                "building_id": b_id,
                "module_key": "battery",
                "enabled": has_bat,
                "created_at": now,
                "updated_at": now,
            },
        ])
    op.bulk_insert(building_modules_t, module_rows)


def downgrade() -> None:
    # Reverse order: modules -> buildings -> organization
    op.execute(
        "DELETE FROM building_modules WHERE building_id IN "
        "(SELECT id FROM buildings WHERE organization_id = "
        "'00000000-0000-1000-8000-000000000001')"
    )
    op.execute(
        "DELETE FROM buildings WHERE organization_id = "
        "'00000000-0000-1000-8000-000000000001'"
    )
    op.execute(
        "DELETE FROM organizations WHERE id = "
        "'00000000-0000-1000-8000-000000000001'"
    )
