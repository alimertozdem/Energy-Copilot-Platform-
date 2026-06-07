"""Pydantic models for /alerts endpoints.

/alerts is a portfolio-wide monitoring surface over Fabric `gold_anomaly_log`.

Two independent state dimensions:
  * Fabric `is_resolved`  -> analytical: did the data return to normal
    (pipeline-driven, read-only here).
  * Postgres `ack_status` -> operational: has a human acknowledged / dismissed
    it (Day 31 overlay -> alert_status table). 'new' = no row yet.

The two are NOT redundant. Field naming for the reading is unit-neutral
(metric_value / threshold_value) because an anomaly may be kWh, CO2 ppm, °C, or
a ratio -- we must not mislabel a CO2 spike as kWh. Severity values are
UPPERCASE in the source table (CRITICAL/HIGH/MEDIUM/LOW -- Day 15 finding).
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AckStatus = Literal["new", "acknowledged", "dismissed"]
"""Operational overlay state (Postgres alert_status). 'new' = no row yet."""


class AlertItem(BaseModel):
    """One row on the /alerts table -- a single anomaly event."""

    # gold_anomaly_log has a real surrogate key (unlike gold_recommendations,
    # which forced the synthetic "building|rank" id used by /actions).
    anomaly_id: str | None = Field(
        default=None, description="gold_anomaly_log.anomaly_id (stable surrogate)."
    )

    fabric_building_id: str
    building_name: str

    anomaly_type: str | None = Field(
        default=None, description="e.g. SOLAR_PR_DROP, CONSUMPTION_SPIKE, CO2_HIGH."
    )
    severity: str | None = Field(
        default=None, description="CRITICAL / HIGH / MEDIUM / LOW (uppercase)."
    )
    detected_at: datetime | None = None
    is_resolved: bool = Field(
        default=False, description="From Fabric is_resolved bit (pipeline-driven)."
    )

    # Unit-neutral on purpose -- see module docstring.
    metric_value: float | None = Field(
        default=None, description="The observed value that tripped the rule."
    )
    threshold_value: float | None = Field(
        default=None, description="The expected / baseline value for the rule."
    )
    deviation_pct: float | None = Field(
        default=None,
        description="(metric - threshold) / threshold * 100; None when threshold is 0/null.",
    )

    description: str | None = Field(default=None, description="description_en from Fabric.")
    recommended_action: str | None = Field(
        default=None, description="recommended_action_en from Fabric."
    )

    # ---- Postgres acknowledge overlay (Day 31) ----
    ack_status: AckStatus = Field(
        default="new",
        description="Operational state: new (no row) / acknowledged / dismissed.",
    )
    acknowledged_at: datetime | None = Field(
        default=None, description="When last acknowledged/dismissed; None when new."
    )
    ack_notes: str | None = Field(default=None, description="Free-text triage notes.")

    can_manage: bool = Field(
        default=False,
        description=(
            "True if the caller may change this alert's triage status (own org or "
            "full-manage partner). False = read-only (e.g. sample buildings)."
        ),
    )


class AlertSeverityCounts(BaseModel):
    """Severity distribution across the visible set -- drives chips, cards, badge.

    Computed via GROUP BY over the full visible set (NOT the row cap), so the
    numbers and the nav badge stay accurate even when the table is truncated.
    """

    # Totals across resolved + unresolved.
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    total: int = 0

    # Unresolved-only breakdown (Fabric is_resolved = 0).
    unresolved_total: int = 0
    unresolved_critical: int = 0
    unresolved_high: int = 0
    unresolved_medium: int = 0
    unresolved_low: int = 0

    # Unhandled = unresolved AND not acknowledged/dismissed = triage queue + badge.
    unhandled_total: int = 0
    unhandled_critical: int = 0
    unhandled_high: int = 0

    # Operational overlay tallies (Postgres).
    acknowledged: int = 0
    dismissed: int = 0


class AlertsResponse(BaseModel):
    """The /alerts GET payload."""

    alerts: list[AlertItem]
    severity_counts: AlertSeverityCounts


class AlertAckUpdateRequest(BaseModel):
    """Body for PATCH /alerts/{anomaly_id}.

    `building_id` is required for authorization + org resolution (the anomaly_id
    alone does not carry the building, unlike the /actions synthetic id).
    """

    ack_status: AckStatus
    building_id: str = Field(description="fabric_building_id the anomaly belongs to.")
    notes: str | None = Field(default=None, max_length=2000)


class AlertAckUpdateResponse(BaseModel):
    """Returned after a successful PATCH."""

    anomaly_id: str
    ack_status: AckStatus
    acknowledged_at: datetime | None = None
