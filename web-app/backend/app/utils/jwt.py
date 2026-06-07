"""JWT helpers for stateless authentication.

Used by:
  * auth router  -- issues tokens on /sync, /register, /login
  * other routers -- consume tokens via get_current_user / get_current_user_id

Design:
  * Algorithm   : HS256 (symmetric, single-backend setup)
  * Expiration  : 24 hours (matches V1 NextAuth session length)
  * Claims      : sub (user_id), org_id, email, iat, exp, iss
  * Secret      : JWT_SECRET env var (64-char random hex, never committed)

V1.5 backlog: refresh tokens, key rotation, asymmetric (RS256) for SP issuance.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User

# Security scheme for FastAPI / Swagger UI integration.
# auto_error=False so that we can raise our own consistent 401 messages
# (instead of FastAPI's default "Not authenticated").
bearer_scheme = HTTPBearer(auto_error=False, description="JWT access_token")

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "energylens-backend"
JWT_EXPIRATION_HOURS = 24


def _get_secret() -> str:
    """Read JWT_SECRET from env at call time -- supports dotenv override on reload."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET not configured. Set it in .env (64-char random hex)."
        )
    return secret


def create_access_token(
    *,
    user_id: UUID,
    organization_id: UUID,
    email: str,
) -> str:
    """Encode a JWT bearing the user's identity. Returned to the client on login."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "org_id": str(organization_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRATION_HOURS)).timestamp()),
        "iss": JWT_ISSUER,
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode + verify a JWT. Raises 401 on any failure (no leak of cause to client)."""
    try:
        return jwt.decode(
            token,
            _get_secret(),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _extract_bearer_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> str:
    """Pull the raw token out of an 'Authorization: Bearer <token>' header.

    Using HTTPBearer (not raw Header()) so Swagger UI shows the global
    "Authorize" button -- one token, all protected endpoints.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization must be 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_user_id(
    token: Annotated[str, Depends(_extract_bearer_token)],
) -> UUID:
    """FastAPI dependency: return the authenticated user's UUID.

    No DB lookup -- use when the endpoint only needs the user_id
    (e.g. repository authorization filter).
    """
    claims = decode_access_token(token)
    try:
        return UUID(claims["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing valid 'sub' claim",
        )


def get_current_org_id(
    token: Annotated[str, Depends(_extract_bearer_token)],
) -> UUID:
    """FastAPI dependency: return the org_id carried in the JWT.

    The token issued at login carries the user's *current* organization
    context (their personal org in V1 -- no org switcher yet). Used by
    /settings so a user can only ever read/manage their active org.
    """
    claims = decode_access_token(token)
    try:
        return UUID(claims["org_id"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing valid 'org_id' claim",
        )


def get_current_user(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """FastAPI dependency: return the full User row.

    Use when the endpoint needs more than user_id (e.g. email for audit logs).
    """
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def get_current_platform_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """FastAPI dependency: require the platform admin (founder).

    Loads the full User (via get_current_user) and asserts is_platform_admin.
    Gates all /admin/* endpoints. Non-admins get 403 -- they're authenticated,
    just not authorized, so hiding existence (404) isn't needed here.
    """
    if not user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required",
        )
    return user


def get_current_platform_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """FastAPI dependency: require the platform admin (founder).

    Loads the full User (via get_current_user) and asserts is_platform_admin.
    Gates all /admin/* endpoints. Non-admins get 403 -- they're authenticated,
    just not authorized, so hiding existence (404) isn't needed here.
    """
    if not user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required",
        )
    return user


# --- Resident session tokens (separate from the B2B access token) -----------
# Residents are NOT NextAuth/B2B users. Their lightweight session is a distinct
# JWT: a different issuer + a `rid` (resident_identity_id) claim and no org. It
# is carried in a separate httpOnly cookie, never the NextAuth cookie.
JWT_RESIDENT_ISSUER = "energylens-resident"
RESIDENT_TOKEN_EXPIRATION_HOURS = 24 * 30  # 30 days; residents are low-activity


def create_resident_token(*, resident_identity_id: UUID) -> str:
    """Encode a resident session JWT (distinct issuer; no org/user claims)."""
    now = datetime.now(timezone.utc)
    payload = {
        "rid": str(resident_identity_id),
        "kind": "resident",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=RESIDENT_TOKEN_EXPIRATION_HOURS)).timestamp()),
        "iss": JWT_RESIDENT_ISSUER,
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)


def decode_resident_token(token: str) -> UUID:
    """Decode + verify a resident session JWT. Raises 401 on any failure."""
    try:
        claims = jwt.decode(
            token, _get_secret(), algorithms=[JWT_ALGORITHM], issuer=JWT_RESIDENT_ISSUER
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Resident session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid resident session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return UUID(claims["rid"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Resident token missing 'rid' claim",
        )
