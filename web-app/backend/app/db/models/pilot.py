"""PilotRequest model — public "request a pilot" lead capture.

A visitor on the landing page / demo / tour can ask to run a pilot (optionally
using their own building). No auth: it's a public lead form. The founder reviews
the queue in /admin and works the status. PII is just name + email + (optional)
organization — consented by submission.
"""
from uuid import UUID, uuid4

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.base import TimestampMixin


class PilotRequest(Base, TimestampMixin):
    """A self-submitted request to run an EnergyLens pilot."""

    __tablename__ = "pilot_requests"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    # Rough size of the prospect's portfolio (free signal for qualification).
    building_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Where the lead came from: 'landing' | 'demo' | 'tour' | 'pricing' | ...
    source: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # new | contacted | qualified | closed
    status: Mapped[str] = mapped_column(
        String(20), default="new", index=True, nullable=False
    )

    def __repr__(self) -> str:
        return f"<PilotRequest {self.email} status={self.status}>"
