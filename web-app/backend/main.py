import os
from typing import Annotated
from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import msal
import httpx
import logging
try:
    import pyodbc
except Exception:
    pyodbc = None
from fastapi.responses import JSONResponse

# Load .env file (override=True forces .env values to win over any pre-existing shell env vars)
load_dotenv(override=True)

logger = logging.getLogger("energylens.api")

# Routers
from app.routers import actions as actions_router
from app.routers import admin as admin_router
from app.routers import auth as auth_router
from app.routers import buildings as buildings_router
from app.routers import copilot as copilot_router
from app.routers import demo as demo_router
from app.routers import portfolio as portfolio_router
from app.routers import settings as settings_router
from app.routers import solar as solar_router
from app.routers import alerts as alerts_router
from app.routers import billing as billing_router
from app.routers import compliance as compliance_router
from app.routers import partners as partners_router
from app.routers import residence as residence_router
from app.routers import installer as installer_router
from app.routers import residential as residential_router
from app.routers import connections as connections_router
from app.routers import agent as agent_router
from app.routers import abatement as abatement_router
from app.routers import pilot as pilot_router

# Auth + DB + repo for the RLS-scoped /embed/token (server-side row-level security)
from app.db.database import get_db
from app.utils.jwt import get_current_user_id
from app.repositories import building as building_repo

# Read Power BI credentials from environment
PBI_TENANT_ID = os.getenv("PBI_TENANT_ID")
PBI_CLIENT_ID = os.getenv("PBI_CLIENT_ID")
PBI_CLIENT_SECRET = os.getenv("PBI_CLIENT_SECRET")
PBI_WORKSPACE_ID = os.getenv("PBI_WORKSPACE_ID")
PBI_REPORT_ID = os.getenv("PBI_REPORT_ID")

# Verify all credentials are loaded
_required = ["PBI_TENANT_ID", "PBI_CLIENT_ID", "PBI_CLIENT_SECRET", "PBI_WORKSPACE_ID", "PBI_REPORT_ID"]
_missing = [k for k in _required if not os.getenv(k)]
if _missing:
    raise RuntimeError(f"Missing .env values: {', '.join(_missing)}")

# Power BI API constants
PBI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
PBI_API_BASE = "https://api.powerbi.com/v1.0/myorg"

# CORS origins: comma-separated env var for prod (Vercel domain), localhost fallback for dev.
_cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]

# FastAPI app
app = FastAPI(
    title="EnergyLens API",
    description="Commercial Building Intelligence Platform - Backend API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Fabric connection warmup (perf) ------------------------------------------
# The first SQL Analytics Endpoint query is cold (connection + DirectLake spin-up),
# which makes the first page a user opens feel slow. Prime the pyodbc pool in a
# background thread on startup so the first real request is warm. Best-effort:
# any failure (e.g. Fabric down) is swallowed — the request path already handles it.
@app.on_event("startup")
def _warm_fabric_connection() -> None:
    import threading

    def _warm() -> None:
        try:
            from app.integrations import fabric_sql

            fabric_sql.execute_scalar("SELECT 1")
            logger.info("Fabric connection warmed up.")
        except Exception as e:  # noqa: BLE001 — best-effort warmup
            logger.warning("Fabric warmup skipped: %s", e)

    threading.Thread(target=_warm, daemon=True).start()

# --- Fabric availability guard -------------------------------------------------
# pyodbc is used ONLY for the Fabric Lakehouse SQL endpoint (Postgres goes
# through SQLAlchemy/psycopg), so any pyodbc.Error means Fabric data is
# unavailable -- e.g. a gold table was dropped or hasn't synced to the SQL
# endpoint yet. Convert it to a typed 503 (never an uncaught 500) and log it
# loudly so the cause is visible in the server logs. The frontend degrades to a
# calm "data temporarily unavailable" notice on this code.
@app.exception_handler(pyodbc.Error)
async def fabric_unavailable_handler(request: Request, exc: pyodbc.Error):
    logger.error(
        "Fabric SQL unavailable on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Live data is temporarily unavailable.",
            "code": "fabric_unavailable",
        },
    )


# Mount routers
app.include_router(auth_router.router)
app.include_router(buildings_router.router)
app.include_router(portfolio_router.router)
app.include_router(copilot_router.router)
app.include_router(demo_router.router)
app.include_router(actions_router.router)
app.include_router(admin_router.router)
app.include_router(settings_router.router)
app.include_router(solar_router.router)
app.include_router(alerts_router.router)
app.include_router(billing_router.router)
app.include_router(compliance_router.router)
app.include_router(partners_router.router)
app.include_router(residence_router.router)
app.include_router(residential_router.router)
app.include_router(connections_router.router)
app.include_router(agent_router.router)
app.include_router(abatement_router.router)
app.include_router(pilot_router.router)
app.include_router(installer_router.router)


def get_azure_token() -> str:
    """Authenticate to Azure AD via service principal, return access token."""
    msal_app = msal.ConfidentialClientApplication(
        client_id=PBI_CLIENT_ID,
        client_credential=PBI_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{PBI_TENANT_ID}",
    )
    result = msal_app.acquire_token_for_client(scopes=PBI_SCOPE)

    if "access_token" not in result:
        err = result.get("error_description") or result.get("error") or "Unknown auth error"
        raise HTTPException(status_code=500, detail=f"Azure auth failed: {err}")

    return result["access_token"]


class EmbedTokenResponse(BaseModel):
    embed_token: str
    embed_url: str
    report_id: str
    expiration: str


@app.get("/")
def root():
    return {"status": "ok", "app": "EnergyLens API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/embed/token", response_model=EmbedTokenResponse)
async def get_embed_token(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
):
    """Generate an RLS-scoped Power BI embed token for the authenticated user.

    Server-side row-level security: resolve the caller's visible Fabric
    building-ids (same source of truth as the pyodbc pages --
    building_repo.list_buildings_for_user) and stamp them into the V2 embed
    token effectiveIdentity customData. The dataset CustomerRLS role
    (PATHCONTAINS(CUSTOMDATA(), silver_building_master[building_id])) then
    filters every page to those buildings, so the token can no longer read the
    whole model. Empty list -> fail-closed. Requires the model OneLake source
    bound to a fixed-identity connection (SSO off); see
    docs/pilot/cp2-embed-rls-smoke-test.md.
    """
    buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    # Exclude shared sample/demo-org buildings: a customer's embedded report
    # shows ONLY their own (and partner-client) live buildings, never the demo
    # portfolio. A customer with no live building yet sees an empty report (the
    # app's "data pending" banner explains why).
    fabric_ids = [
        b.fabric_building_id
        for b in buildings
        if b.fabric_building_id and not b.organization.is_sample
    ]
    custom_data = "|".join(fabric_ids)

    azure_token = get_azure_token()

    headers = {
        "Authorization": f"Bearer {azure_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Get report details (embedUrl + datasetId)
        report_url = f"{PBI_API_BASE}/groups/{PBI_WORKSPACE_ID}/reports/{PBI_REPORT_ID}"
        report_resp = await client.get(report_url, headers=headers)

        if report_resp.status_code != 200:
            raise HTTPException(
                status_code=report_resp.status_code,
                detail=f"Get report failed: {report_resp.text}",
            )

        report_data = report_resp.json()
        embed_url = report_data["embedUrl"]
        dataset_id = report_data["datasetId"]

        # 2. Generate embed token via V2 API with RLS effectiveIdentity (customData).
        token_url = f"{PBI_API_BASE}/GenerateToken"
        token_body = {
            "datasets": [{"id": dataset_id}],
            "reports": [{"id": PBI_REPORT_ID}],
            "targetWorkspaces": [{"id": PBI_WORKSPACE_ID}],
            "identities": [
                {
                    "username": "rls@energylens.app",
                    "roles": ["CustomerRLS"],
                    "datasets": [dataset_id],
                    "customData": custom_data,
                }
            ],
        }
        token_resp = await client.post(token_url, headers=headers, json=token_body)

        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=token_resp.status_code,
                detail=f"Generate token failed: {token_resp.text}",
            )

        token_data = token_resp.json()

        return EmbedTokenResponse(
            embed_token=token_data["token"],
            embed_url=embed_url,
            report_id=PBI_REPORT_ID,
            expiration=token_data["expiration"],
        )
