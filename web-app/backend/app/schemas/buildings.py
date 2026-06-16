"""Pydantic schemas for buildings endpoints."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Building type options (mirror Building.building_type comment).
BuildingType = Literal[
    "Office",
    "Retail",
    "Hotel",
    "Healthcare",
    "Logistics",
    "Datacenter",
    "Residential",
    "Mixed",
]

# Energy-profile enums (declared at onboarding; drive the advisor + compliance
# even before live Fabric data is connected).
EpcClass = Literal["A", "B", "C", "D", "E", "F", "G"]
HeatingSystem = Literal[
    "gas_boiler", "heat_pump", "district_heating", "electric", "oil", "biomass", "other"
]
CoolingSystem = Literal["none", "split_ac", "central_chiller", "district_cooling", "other"]
OccupancyPattern = Literal["standard_hours", "extended_hours", "always_on", "seasonal"]


class BuildingModuleResponse(BaseModel):
    """A single module's enablement state for a building."""

    module_key: Literal["meters", "iot", "battery", "solar"]
    enabled: bool

    model_config = ConfigDict(from_attributes=True)


class BuildingResponse(BaseModel):
    """Full metadata + module unlock state for one building.

    Used by:
      * GET /buildings             -> list of these
      * GET /buildings/{fabric_id} -> a single one
      * POST /buildings            -> the created building
    """

    id: UUID
    fabric_building_id: str | None
    name: str
    city: str | None
    country_code: str | None
    building_type: str | None
    floor_area_m2: float | None
    pv_capacity_kwp: float | None
    construction_year: int | None
    epc_class: str | None
    heating_system: str | None
    cooling_system: str | None
    occupancy_pattern: str | None
    floors_above_ground: int | None
    typical_occupants: int | None
    timezone: str
    is_active: bool
    organization_id: UUID
    # True if this building belongs to a sample/demo org. Frontend uses this
    # to show a "Sample" badge on cards. Joined from organizations.is_sample.
    is_sample_org: bool
    modules: list[BuildingModuleResponse]

    model_config = ConfigDict(from_attributes=True)


class BuildingListResponse(BaseModel):
    """Result of GET /buildings."""

    buildings: list[BuildingResponse]
    total: int


# ---------------------------------------------------------------------------
# Create (onboarding wizard -> POST /buildings)
# ---------------------------------------------------------------------------

class BuildingModuleInput(BaseModel):
    """Desired module state at creation (onboarding Systems step)."""

    module_key: Literal["meters", "iot", "battery", "solar"]
    enabled: bool = False
    # Free-text intent, e.g. data-source protocol ("Modbus TCP", "SolarEdge API").
    notes: str | None = None


class BuildingCreateRequest(BaseModel):
    """Payload for POST /buildings.

    fabric_building_id is intentionally NOT accepted -- a new building has no
    Fabric data yet; the bridge id is assigned later when data is connected.
    """

    name: str = Field(min_length=1, max_length=255)
    building_type: BuildingType | None = None
    city: str | None = Field(default=None, max_length=100)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    address: str | None = None
    floor_area_m2: float | None = Field(default=None, ge=0)
    construction_year: int | None = Field(default=None, ge=1800, le=2100)
    epc_class: EpcClass | None = None
    # heating/cooling accept a free-text value when the user picks "Other", so
    # these stay plain strings (frontend offers a curated list + an Other box).
    heating_system: str | None = Field(default=None, max_length=40)
    cooling_system: str | None = Field(default=None, max_length=40)
    occupancy_pattern: OccupancyPattern | None = None
    floors_above_ground: int | None = Field(default=None, ge=0, le=300)
    typical_occupants: int | None = Field(default=None, ge=0)
    timezone: str = "Europe/Berlin"
    # Installed solar PV capacity in kWp (onboarding solar step). None = no PV.
    pv_capacity_kwp: float | None = Field(default=None, ge=0)
    # Envelope + fuel (onboarding) — unlock GEG / EPC / CO₂ reports. None = unknown.
    wall_u_value: float | None = Field(default=None, ge=0, le=5)
    roof_u_value: float | None = Field(default=None, ge=0, le=5)
    window_u_value: float | None = Field(default=None, ge=0, le=10)
    insulation_year: int | None = Field(default=None, ge=1800, le=2100)
    has_gas_heating: bool | None = None
    modules: list[BuildingModuleInput] = []


# ---------------------------------------------------------------------------
# Bulk import (portfolio CSV -> POST /buildings/bulk)
# ---------------------------------------------------------------------------

class BulkBuildingRow(BaseModel):
    """One building's metadata in a bulk portfolio import.

    A light subset of BuildingCreateRequest -- enough to create a building shell
    a portfolio manager (Hausverwaltung) can refine + add a baseline to later.
    The 'meters' module is auto-enabled on each created building.
    """

    name: str = Field(min_length=1, max_length=255)
    building_type: BuildingType | None = None
    city: str | None = Field(default=None, max_length=100)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    floor_area_m2: float | None = Field(default=None, ge=0)
    construction_year: int | None = Field(default=None, ge=1800, le=2100)
    epc_class: EpcClass | None = None
    heating_system: str | None = Field(default=None, max_length=40)


class BulkImportRequest(BaseModel):
    """Payload for POST /buildings/bulk (max 200 rows per call)."""

    rows: list[BulkBuildingRow] = Field(min_length=1, max_length=200)


class BulkImportRowResult(BaseModel):
    """Per-row outcome so the UI can show exactly which rows imported."""

    index: int
    name: str
    ok: bool
    id: UUID | None = None
    error: str | None = None


class BulkImportResponse(BaseModel):
    created: int
    failed: int
    results: list[BulkImportRowResult]
