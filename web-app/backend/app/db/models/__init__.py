"""ORM models registry.

Importing this package registers all models with Base.metadata,
which Alembic uses to autogenerate migrations.

Add every new model class here as it gets created.
"""
from app.db.models.user import User, UserAuthProvider
from app.db.models.organization import Organization, OrgMember
from app.db.models.invitation import OrgInvitation
from app.db.models.building import Building, BuildingModule
from app.db.models.recommendation import RecommendationStatus
from app.db.models.alert_status import AlertStatus
from app.db.models.copilot import CopilotConversation, CopilotMessage
from app.db.models.audit import AuditLog
from app.db.models.partner import PartnerClientLink
from app.db.models.connection import Device, SensorPoint
from app.db.models.agent import AgentToken
from app.db.models.password_reset import PasswordResetToken
from app.db.models.iot_reading import IotReading
from app.db.models.gold_solar_daily import GoldSolarDaily
from app.db.models.bridge import BridgeRequest
from app.db.models.pilot import PilotRequest
from app.db.models.installer import InstallerRequest
from app.db.models.esrs_narrative import EsrsNarrative
from app.db.models.residential import (
    Unit,
    ResidentIdentity,
    UnitResident,
    ResidentInviteToken,
)

__all__ = [
    "User",
    "UserAuthProvider",
    "Organization",
    "OrgMember",
    "OrgInvitation",
    "Building",
    "BuildingModule",
    "RecommendationStatus",
    "AlertStatus",
    "CopilotConversation",
    "CopilotMessage",
    "AuditLog",
    "PartnerClientLink",
    "Device",
    "SensorPoint",
    "AgentToken",
    "PasswordResetToken",
    "IotReading",
    "GoldSolarDaily",
    "BridgeRequest",
    "PilotRequest",
    "InstallerRequest",
    "EsrsNarrative",
    "Unit",
    "ResidentIdentity",
    "UnitResident",
    "ResidentInviteToken",
]
