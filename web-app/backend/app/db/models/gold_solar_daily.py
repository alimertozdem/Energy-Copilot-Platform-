"""GoldSolarDaily -- telemetry-derived daily solar KPIs (Phase A loader output).

Populated by app/services/solar_telemetry_rollup.run_rollup from bronze_iot_readings.
data_source='telemetry' marks these as REAL (vs the synthetic mv_kpi_daily rows).
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class GoldSolarDaily(Base):
    """One building-day of telemetry-derived solar KPIs."""

    __tablename__ = "gold_solar_daily"

    building_id: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    solar_generated_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_self_consumed_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_exported_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_solar_pr: Mapped[float | None] = mapped_column(Float, nullable=True)
    in_plane_irradiation_kwh_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    pv_capacity_kwp: Mapped[float | None] = mapped_column(Float, nullable=True)
    reading_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_load_meter: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    generation_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(Text, server_default="telemetry", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
