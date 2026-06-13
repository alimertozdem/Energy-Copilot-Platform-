"""EsrsNarrative model — per-org saved narrative for the ESRS E-1 report.

The quantitative ESRS E-1 datapoints (E1-5 energy, E1-6 GHG) come from Fabric; the
qualitative disclosures (E1-1..E1-4, E1-7..E1-9) are written by the company. This
table stores the company's narrative text per disclosure datapoint, keyed by
organization + datapoint code (e.g. "E1-1"). One editable narrative per disclosure
per organization; the report renders the saved text, falling back to a guided
boilerplate default when none is saved.
"""
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class EsrsNarrative(Base, TimestampMixin):
    """Per-organization narrative text for one ESRS E-1 qualitative disclosure."""

    __tablename__ = "esrs_narrative"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "datapoint_key",
            name="uq_esrs_narrative_identity",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # ESRS disclosure code, e.g. "E1-1" … "E1-9" (qualitative slots only).
    datapoint_key: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    reporting_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship()  # noqa: F821
    updated_by: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[updated_by_user_id],
    )

    def __repr__(self) -> str:
        return f"<EsrsNarrative {self.datapoint_key} org={self.organization_id}>"
