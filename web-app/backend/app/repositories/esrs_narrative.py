"""Repository for ESRS E-1 narrative text (per organization, per disclosure datapoint)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.esrs_narrative import EsrsNarrative


def list_for_org(db: Session, org_id: UUID) -> list[EsrsNarrative]:
    """All saved narrative rows for one organization."""
    return list(
        db.scalars(
            select(EsrsNarrative).where(EsrsNarrative.organization_id == org_id)
        )
    )


def upsert(
    db: Session,
    *,
    org_id: UUID,
    datapoint_key: str,
    content: str,
    reporting_year: int | None,
    user_id: UUID | None,
) -> EsrsNarrative:
    """Create or update the narrative for one (org, datapoint) pair."""
    row = db.scalar(
        select(EsrsNarrative).where(
            EsrsNarrative.organization_id == org_id,
            EsrsNarrative.datapoint_key == datapoint_key,
        )
    )
    if row is None:
        row = EsrsNarrative(
            organization_id=org_id,
            datapoint_key=datapoint_key,
            content=content,
            reporting_year=reporting_year,
            updated_by_user_id=user_id,
        )
        db.add(row)
    else:
        row.content = content
        if reporting_year is not None:
            row.reporting_year = reporting_year
        row.updated_by_user_id = user_id
    db.commit()
    db.refresh(row)
    return row
