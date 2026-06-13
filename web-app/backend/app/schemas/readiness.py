"""Building readiness + Data Score response schema (mirrors building_readiness service)."""
from pydantic import BaseModel


class ReadinessSignal(BaseModel):
    key: str
    label: str
    points: int
    present: bool
    applicable: bool
    help: str


class ReadinessReport(BaseModel):
    key: str
    label: str
    status: str  # ready | partial | locked | not_applicable
    missing: list[str]
    note: str


class ReadinessAction(BaseModel):
    key: str
    label: str
    points: int
    help: str
    unlocks: list[str]


class BuildingReadiness(BaseModel):
    data_score: int
    points_earned: int
    points_possible: int
    signals: list[ReadinessSignal]
    reports: list[ReadinessReport]
    next_actions: list[ReadinessAction]
