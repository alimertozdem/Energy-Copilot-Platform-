"""Repository for building_consumption — uploaded/manual monthly baseline."""
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.building import BuildingConsumption


def _dec(value: float | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def upsert_rows(
    db: Session,
    *,
    building_id: UUID,
    rows: list[tuple[str, float, float | None]],
    source: str = "csv",
) -> int:
    """Insert or update one row per (building_id, period). Caller commits.

    `rows` is a list of (period 'YYYY-MM', energy_kwh, cost_eur|None).
    Returns the number of rows written.
    """
    for period, kwh, cost in rows:
        existing = db.scalar(
            select(BuildingConsumption)
            .where(BuildingConsumption.building_id == building_id)
            .where(BuildingConsumption.period == period)
        )
        if existing is not None:
            existing.energy_kwh = Decimal(str(kwh))
            existing.cost_eur = _dec(cost)
            existing.source = source
        else:
            db.add(
                BuildingConsumption(
                    building_id=building_id,
                    period=period,
                    energy_kwh=Decimal(str(kwh)),
                    cost_eur=_dec(cost),
                    source=source,
                )
            )
    return len(rows)


def get_summary(db: Session, *, building_id: UUID) -> dict:
    """Aggregate a building's uploaded consumption into a summary dict."""
    rows = list(
        db.scalars(
            select(BuildingConsumption)
            .where(BuildingConsumption.building_id == building_id)
            .order_by(BuildingConsumption.period)
        ).all()
    )
    if not rows:
        return {
            "months": 0,
            "period_start": None,
            "period_end": None,
            "total_kwh": 0.0,
            "total_cost_eur": None,
            "avg_monthly_kwh": None,
        }

    total_kwh = float(sum((r.energy_kwh for r in rows), Decimal(0)))
    costs = [r.cost_eur for r in rows if r.cost_eur is not None]
    total_cost = float(sum(costs, Decimal(0))) if costs else None
    months = len(rows)

    return {
        "months": months,
        "period_start": rows[0].period,
        "period_end": rows[-1].period,
        "total_kwh": round(total_kwh, 2),
        "total_cost_eur": round(total_cost, 2) if total_cost is not None else None,
        "avg_monthly_kwh": round(total_kwh / months, 2) if months else None,
    }


def list_rows(db: Session, *, building_id: UUID) -> list[BuildingConsumption]:
    """All uploaded consumption rows for a building, ordered by period.

    Used by the baseline-KPI engine (pure compute over these rows).
    """
    return list(
        db.scalars(
            select(BuildingConsumption)
            .where(BuildingConsumption.building_id == building_id)
            .order_by(BuildingConsumption.period)
        ).all()
    )
