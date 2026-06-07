"""Demo router — public, auth-free endpoints for the marketing /demo page.

Routes:
  GET  /demo/buildings           -> public sample portfolio (B001-B006)
  POST /demo/embed/token         -> public PBI embed token (added in PARÇA 3)

Auth model:
  These endpoints take NO Authorization header and NO cookies. They are
  intentionally public so an anonymous browser can render the demo page
  for marketing, BSBI pilot, and EU funding application links.

Defense in depth:
  * The building list is hardcoded in app.services.demo_data.DEMO_FABRIC_IDS.
    Even a misconfigured Postgres demo_user row cannot expose B007+.
  * The embed token (PARÇA 3) will set effective identity to the Postgres
    'demo' user, which the DAX RLS role restricts to B001-B006.
  * Rate limiting is V1.5 backlog — Cloudflare WAF + per-IP throttle.
"""

from fastapi import APIRouter

from app.schemas.demo import (
    DemoBuildingsResponse,
    DemoEmbedTokenRequest,
    DemoEmbedTokenResponse,
)
from app.services import demo_data

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/buildings", response_model=DemoBuildingsResponse)
def get_demo_buildings() -> DemoBuildingsResponse:
    """Return the 6-building public sample portfolio with 30d kWh totals.

    No auth. No filtering knobs. The same payload for every anonymous caller.
    """
    return demo_data.get_demo_buildings()


@router.post("/embed/token", response_model=DemoEmbedTokenResponse)
async def create_demo_embed_token(
    body: DemoEmbedTokenRequest | None = None,
) -> DemoEmbedTokenResponse:
    """Issue a short-lived Power BI embed token for the public /demo page.

    No auth. Token expires in ~10 minutes (Power BI default). The token
    carries RLS effectiveIdentity bound to the dataset's 'Demo' role, which
    restricts visibility to B001-B006 via a DAX filter.

    Optional body: { "building_id": "B003" }
      - When supplied, MUST be one of B001-B006; otherwise 403.
      - Even with no building_id the embed is RLS-restricted to the 6 demos.

    Rate limiting is V1.5 backlog (Cloudflare WAF / per-IP throttle).
    """
    building_id = body.building_id if body else None
    return await demo_data.get_demo_embed_token(building_id=building_id)
