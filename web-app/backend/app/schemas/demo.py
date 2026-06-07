"""Pydantic response models for /demo public endpoints.

Demo endpoints are auth-free and serve a fixed sample portfolio (B001-B006).
Payloads are intentionally narrower than /portfolio — no module flags, no
recommendations, no anomaly counts. Just enough to render a public marketing
page with a Power BI embed.
"""

from pydantic import BaseModel, Field


class DemoBuilding(BaseModel):
    """One sample building shown on the public /demo page."""

    fabric_building_id: str = Field(description="Stable Fabric Lakehouse ID, e.g. 'B001'.")
    name: str
    city: str
    country: str = Field(description="ISO 3166-1 alpha-2 (DE, TR, AT, NL, DK, SE).")
    building_type: str = Field(description="Office / Retail / Hotel / Healthcare / Logistics / Education / ...")
    floor_area_m2: float
    epc_class: str | None = Field(default=None, description="Energy Performance Certificate band (A-G).")
    kwh_30d: float = Field(description="Sum of total_consumption_kwh over the most recent 30 days.")


class DemoBuildingsResponse(BaseModel):
    """Public sample building list payload."""

    buildings: list[DemoBuilding]


class DemoEmbedTokenRequest(BaseModel):
    """Request body for POST /demo/embed/token.

    building_id is optional. When supplied it MUST be one of the demo
    allowlist IDs (B001-B006); the backend rejects any other value with 403.
    The frontend uses this to pre-filter the embed to the selected building.
    """

    building_id: str | None = Field(
        default=None,
        description="Optional demo building ID (B001-B006). Other IDs rejected with 403.",
    )


class DemoEmbedTokenResponse(BaseModel):
    """Short-lived Power BI embed token for the public demo page."""

    embed_token: str
    embed_url: str
    report_id: str
    expiration: str = Field(
        description="ISO-8601 UTC expiry (~10 minutes from issuance)."
    )
    # Echo back which building (if any) the token was issued for so the
    # frontend can confirm its UI state matches the embed scope.
    building_id: str | None = None
