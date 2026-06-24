"""Auth router -- /auth/sync + /auth/register + /auth/login endpoints.

Called by frontend NextAuth signIn callback after a successful login (sync)
or by the /signup + /login forms (register, login).
Service-to-service auth: protected by INTERNAL_API_KEY shared secret.
Public users never hit these endpoints directly.
"""
import hashlib
import hmac
import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Organization, OrgMember, User
from app.integrations.email import send_email
from app.repositories import organization as org_repo
from app.repositories import password_reset as pwreset_repo
from app.repositories import user as user_repo
from app.schemas.auth import (
    AuthSyncRequest,
    AuthSyncResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.utils.jwt import create_access_token
from app.utils.naming import get_personal_org_name, slugify_org_name
from app.utils.password import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def verify_internal_api_key(
    x_internal_api_key: str = Header(..., alias="X-Internal-Api-Key"),
) -> None:
    """Constant-time comparison against INTERNAL_API_KEY from .env.

    Raises 401 if key missing or wrong, 500 if backend not configured.
    """
    expected = os.getenv("INTERNAL_API_KEY")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_API_KEY not configured on backend",
        )
    if not hmac.compare_digest(x_internal_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )


@router.post("/sync", response_model=AuthSyncResponse)
def sync_user(
    payload: AuthSyncRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_api_key),
) -> AuthSyncResponse:
    """Upsert User + UserAuthProvider; create personal Org on first login.

    Idempotent: safe to call on every login (only inserts when new).
    Transactional: all writes commit together, or none commit.
    """
    # 1. Find or create User (email is canonical identity).
    user = user_repo.find_user_by_email(db, payload.email)
    is_new_user = user is None
    if is_new_user:
        user = user_repo.create_user(
            db,
            email=payload.email,
            display_name=payload.display_name,
            avatar_url=payload.avatar_url,
        )
    else:
        # Backfill display info if provider has fresher data.
        if payload.display_name and not user.display_name:
            user.display_name = payload.display_name
        if payload.avatar_url:
            user.avatar_url = payload.avatar_url

    # 2. Find or create auth-provider link.
    existing_auth = user_repo.find_auth_provider(
        db,
        provider=payload.provider,
        provider_user_id=payload.provider_user_id,
    )
    is_new_provider_link = existing_auth is None
    if is_new_provider_link:
        user_repo.create_auth_provider(
            db,
            user_id=user.id,
            provider=payload.provider,
            provider_user_id=payload.provider_user_id,
            email_verified=payload.email_verified,
        )

    # 3. Determine the user's primary organization.
    if is_new_user:
        # First-ever login: create a personal workspace + admin membership.
        org_name = get_personal_org_name(payload.display_name, payload.email)
        base_slug = slugify_org_name(org_name)
        org_slug = org_repo.ensure_unique_slug(db, base_slug)
        org = org_repo.create_personal_organization(
            db, creator=user, name=org_name, slug=org_slug,
        )
        org_repo.create_org_membership(
            db,
            organization_id=org.id,
            user_id=user.id,
            role="admin",
        )
    else:
        # Existing user: return their primary (first-joined) org.
        org = db.scalar(
            select(Organization)
            .join(OrgMember, OrgMember.organization_id == Organization.id)
            .where(OrgMember.user_id == user.id)
            .order_by(OrgMember.created_at)
            .limit(1)
        )
        if org is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"User {user.id} has no organization membership",
            )

    # 4. Update last_login_at.
    user_repo.touch_last_login(db, user)

    # 5. Atomic commit -- all changes succeed together or roll back together.
    db.commit()

    # 6. Issue JWT for the session.
    access_token = create_access_token(
        user_id=user.id,
        organization_id=org.id,
        email=user.email,
    )

    return AuthSyncResponse(
        user_id=user.id,
        organization_id=org.id,
        is_new_user=is_new_user,
        is_new_provider_link=is_new_provider_link,
        access_token=access_token,
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_api_key),
) -> RegisterResponse:
    """Create a new email/password account + personal organization.

    Fails with 409 if the email is already registered (by any provider).
    Frontend should then prompt the user to sign in with their existing method.
    """
    # 1. Reject duplicate email (regardless of provider).
    if user_repo.find_user_by_email(db, payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered. Try signing in instead.",
        )

    # 2. Create user.
    user = user_repo.create_user(
        db,
        email=payload.email,
        display_name=payload.display_name,
        avatar_url=None,
    )

    # 3. Create email auth provider link with bcrypt hash.
    user_repo.create_auth_provider(
        db,
        user_id=user.id,
        provider="email",
        provider_user_id=payload.email,
        email_verified=False,  # V1: no email verification flow
        password_hash=hash_password(payload.password),
    )

    # 4. Create personal organization + admin membership.
    org_name = get_personal_org_name(payload.display_name, payload.email)
    base_slug = slugify_org_name(org_name)
    org_slug = org_repo.ensure_unique_slug(db, base_slug)
    org = org_repo.create_personal_organization(
        db, creator=user, name=org_name, slug=org_slug,
    )
    org_repo.create_org_membership(
        db,
        organization_id=org.id,
        user_id=user.id,
        role="admin",
    )

    # 5. Atomic commit.
    db.commit()

    # 6. Issue JWT for the fresh session.
    access_token = create_access_token(
        user_id=user.id,
        organization_id=org.id,
        email=user.email,
    )

    return RegisterResponse(
        user_id=user.id,
        organization_id=org.id,
        access_token=access_token,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_api_key),
) -> LoginResponse:
    """Verify email/password credentials and return user info.

    Called by NextAuth's Credentials provider authorize() callback.
    Returns 401 on any failure (wrong email, wrong password, no email
    provider linked) -- generic message prevents email enumeration.
    """
    generic_401 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    # 1. Find the email/password auth provider link.
    auth = user_repo.find_auth_provider(
        db,
        provider="email",
        provider_user_id=payload.email,
    )
    if auth is None or auth.password_hash is None:
        raise generic_401

    # 2. Verify bcrypt hash.
    if not verify_password(payload.password, auth.password_hash):
        raise generic_401

    # 3. Load user + primary organization.
    user = db.get(User, auth.user_id)
    if user is None or not user.is_active:
        raise generic_401

    org = db.scalar(
        select(Organization)
        .join(OrgMember, OrgMember.organization_id == Organization.id)
        .where(OrgMember.user_id == user.id)
        .order_by(OrgMember.created_at)
        .limit(1)
    )
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User {user.id} has no organization membership",
        )

    # 4. Update last_login_at.
    user_repo.touch_last_login(db, user)
    db.commit()

    # 5. Issue JWT for the session.
    access_token = create_access_token(
        user_id=user.id,
        organization_id=org.id,
        email=user.email,
    )

    return LoginResponse(
        user_id=user.id,
        organization_id=org.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        access_token=access_token,
    )


# --- password reset (forgot + reset) ---------------------------------------

def _hash_token(token: str) -> str:
    """SHA-256 hex of a reset token (matches AgentToken hashing)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _reset_email_html(link: str) -> str:
    """Branded HTML body for the reset email (inline styles for mail clients)."""
    return (
        '<div style="font-family:system-ui,Segoe UI,Arial,sans-serif;'
        'max-width:480px;margin:0 auto;color:#0F1F35">'
        '<h2 style="color:#0F1F35;margin:0 0 12px">Reset your EnergyLens password</h2>'
        '<p style="color:#33415A;line-height:1.5;margin:0 0 18px">'
        'We received a request to reset your password. Click the button below to '
        'choose a new one. This link expires in 1 hour. If you did not request '
        'this, you can safely ignore this email.</p>'
        f'<p style="margin:0 0 18px"><a href="{link}" '
        'style="display:inline-block;background:#1D9E75;color:#ffffff;'
        'text-decoration:none;padding:11px 22px;border-radius:6px;font-weight:600">'
        'Reset password</a></p>'
        '<p style="color:#8895AA;font-size:12px;line-height:1.5;margin:0">'
        f'Or paste this link into your browser:<br>{link}</p>'
        '</div>'
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_api_key),
) -> ForgotPasswordResponse:
    """Email a password-reset link IF the address has an email/password account.

    Always returns ok:true regardless of whether the account exists, so the
    response can never be used to enumerate registered emails. Only 'email'
    provider accounts can reset; Google/Microsoft sign-ins have no password.
    """
    user = user_repo.find_user_by_email(db, payload.email)
    if user is not None and user.is_active:
        auth = user_repo.find_auth_provider(
            db, provider="email", provider_user_id=payload.email
        )
        if auth is not None and auth.password_hash is not None:
            # Keep only the latest link valid.
            pwreset_repo.invalidate_for_user(db, user_id=user.id)
            plaintext = secrets.token_urlsafe(32)
            pwreset_repo.create_token(
                db, user_id=user.id, token_hash=_hash_token(plaintext)
            )
            db.commit()
            base = os.getenv("FRONTEND_BASE_URL", "https://energylens.eu").rstrip("/")
            link = f"{base}/reset-password?token={plaintext}"
            send_email(
                to=payload.email,
                subject="Reset your EnergyLens password",
                html=_reset_email_html(link),
            )
    return ForgotPasswordResponse()


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_api_key),
) -> ResetPasswordResponse:
    """Set a new password using a valid, unused, unexpired reset token."""
    invalid = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This reset link is invalid or has expired. Request a new one.",
    )
    token = pwreset_repo.get_valid_by_hash(db, token_hash=_hash_token(payload.token))
    if token is None:
        raise invalid
    updated = user_repo.set_email_password(
        db, user_id=token.user_id, password_hash=hash_password(payload.password)
    )
    if not updated:
        raise invalid
    pwreset_repo.mark_used(db, token)
    db.commit()
    return ResetPasswordResponse()
