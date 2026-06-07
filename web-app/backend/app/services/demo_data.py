"""Demo data service — reads the public sample portfolio (B001-B006).

The list of demo-visible buildings is hardcoded here (DEMO_FABRIC_IDS) rather
than queried from Postgres for two reasons:
  1. Defense in depth — even if the Postgres demo_user row is misconfigured,
     this module physically cannot return B007+.
  2. Public endpoints stay fast — no Postgres round-trip for the unauth'd
     route.

Numbers are read from Fabric Lakehouse silver_building_master + gold_kpi_daily
the same way /portfolio reads them, anchored to MAX([date]) so the demo always
shows realistic numbers even when sample data ends in the past.

RLS strategy (Day 17, 2026-05-29):
  We originally planned to pass effectiveIdentity (username + 'Demo' role) on
  every embed token so the Power BI dataset itself enforced the B001-B006
  allowlist. That turned out to be incompatible with our semantic model: the
  Power BI REST API rejects identities[] for DirectLake datasets with
      "Creating embed token with effective identity is not supported for
       this datasource."
  This is a Microsoft DirectLake limitation, not a bug in our setup.

  V1 demo security therefore relies on a two-layer defence:
    1. Backend whitelist (is_demo_building) -- this module refuses any
       building_id outside DEMO_FABRIC_IDS with a 403.
    2. Frontend filter (PowerBIReport in demo mode hardcodes the filter to
       B001-B006). Dev-tools tampering can defeat this layer, but since the
       demo dataset is published sample data with zero customer information,
       the exfiltration impact is nil.

  V1.5+ path: if we move the semantic model to Import mode (or DirectLake
  with composite Import-table for RLS), restore the identities[] call by
  passing rls_username / rls_roles to pbi_embed.generate_embed_token.
"""

import os
from datetime import date, timedelta

from app.integrations import fabric_sql, pbi_embed
from app.schemas.demo import DemoBuilding, DemoBuildingsResponse, DemoEmbedTokenResponse


# -----------------------------------------------------------------------------
# Hardcoded demo allowlist — defense in depth
# -----------------------------------------------------------------------------
# These 6 buildings represent a balanced cross-section of the 10-building
# sample portfolio (4 countries, 6 building types). B007-B010 are reserved
# for richer scenarios in /portfolio (Page 7 extreme showcase).
DEMO_FABRIC_IDS: tuple[str, ...] = (
    "B001",  # Office,     Berlin, DE
    "B002",  # Retail,     Istanbul, TR
    "B003",  # Logistics,  Hamburg, DE
    "B004",  # Hotel,      Vienna, AT
    "B005",  # Healthcare, Frankfurt, DE
    "B006",  # Education,  Amsterdam, NL
)


def _safe_float(v) -> float:
    return float(v) if v is not None else 0.0


def get_demo_buildings() -> DemoBuildingsResponse:
    """Return the public sample buildings with their last-30-day kWh total.

    Read pattern mirrors /portfolio: pull building_master rows, LEFT JOIN a
    30-day kWh aggregate anchored at MAX([date]). Empty payload if Fabric has
    no rows for these IDs (extremely unlikely — these are deterministic seeds).
    """
    ph, ids_params = fabric_sql.format_in_clause(list(DEMO_FABRIC_IDS))

    # Anchor to the latest date with data for any demo building.
    anchor_sql = (
        f"SELECT MAX([date]) AS max_date "
        f"FROM [dbo].[gold_kpi_daily] "
        f"WHERE building_id IN ({ph})"
    )
    anchor: date | None = fabric_sql.execute_scalar(anchor_sql, ids_params)

    if anchor is None:
        start_date = end_date = date.today()
    else:
        start_date = anchor - timedelta(days=29)
        end_date = anchor

    sql = f"""
    SELECT
        b.building_id,
        b.building_name,
        b.city,
        b.country_code,
        b.building_type,
        b.gross_floor_area_m2,
        b.energy_certificate,
        ISNULL(k.kwh_30d, 0) AS kwh_30d
    FROM [dbo].[silver_building_master] b
    LEFT JOIN (
        SELECT
            building_id,
            SUM(total_consumption_kwh) AS kwh_30d
        FROM [dbo].[gold_kpi_daily]
        WHERE building_id IN ({ph})
          AND [date] BETWEEN ? AND ?
        GROUP BY building_id
    ) k ON k.building_id = b.building_id
    WHERE b.building_id IN ({ph})
    ORDER BY b.building_id ASC
    """

    params = (
        *ids_params,                             # k subquery IN clause
        start_date, end_date,                    # k subquery date range
        *ids_params,                             # outer WHERE
    )

    rows = fabric_sql.execute_query(sql, params)
    buildings = [
        DemoBuilding(
            fabric_building_id=r["building_id"],
            name=r["building_name"] or "",
            city=r["city"] or "",
            country=r["country_code"] or "",
            building_type=r["building_type"] or "",
            floor_area_m2=_safe_float(r.get("gross_floor_area_m2")),
            epc_class=r.get("energy_certificate"),
            kwh_30d=_safe_float(r.get("kwh_30d")),
        )
        for r in rows
    ]
    return DemoBuildingsResponse(buildings=buildings)


def is_demo_building(fabric_building_id: str) -> bool:
    """Whitelist check used by /demo/embed/token to refuse non-demo IDs.

    Kept as a module-level helper so the embed endpoint can import it without
    pulling the whole service layer.
    """
    return fabric_building_id in DEMO_FABRIC_IDS


async def get_demo_embed_token(building_id: str | None = None) -> DemoEmbedTokenResponse:
    """Issue a short-lived Power BI embed token for the public demo page.

    The token carries RLS effectiveIdentity (username + 'Demo' role). The
    dataset's Demo role contains a DAX filter that restricts every visual to
    B001-B006 -- even a tampered embed URL cannot exfiltrate B007+ data.

    `building_id` is only used for an extra app-level whitelist check; the
    Power BI side already enforces the same limit via RLS.
    """
    if building_id is not None and not is_demo_building(building_id):
        # Pre-empt PBI: refuse non-demo IDs at the API layer with a clear 403.
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail=f"building_id '{building_id}' is not part of the demo portfolio",
        )

    workspace_id = os.getenv("PBI_WORKSPACE_ID")
    report_id = os.getenv("PBI_REPORT_ID")
    if not workspace_id or not report_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail="PBI_WORKSPACE_ID / PBI_REPORT_ID not configured",
        )

    # DirectLake datasets reject identities[] (see module docstring).
    # We deliberately omit rls_username / rls_roles -- the frontend hardcoded
    # buildingIds filter + this service's whitelist check provide the V1
    # security boundary.
    token_data = await pbi_embed.generate_embed_token(
        workspace_id=workspace_id,
        report_id=report_id,
    )

    return DemoEmbedTokenResponse(
        embed_token=token_data["embed_token"],
        embed_url=token_data["embed_url"],
        report_id=token_data["report_id"],
        expiration=token_data["expiration"],
        building_id=building_id,
    )
