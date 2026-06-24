"""Pydantic schemas for /auth/sync endpoint."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class AuthSyncRequest(BaseModel):
    """Payload sent by NextAuth signIn callback when a user logs in.

    The frontend sends user info pulled from the OAuth provider response.
    The backend upserts User + UserAuthProvider + (if new) personal Org.
    """

    email: EmailStr
    display_name: str | None = None
    avatar_url: str | None = None
    # 'microsoft' | 'google' | 'email' (V1 supported set)
    provider: Literal["microsoft", "google", "email"]
    # Microsoft: Azure AD object id. Google: 'sub' claim. Email: user's email.
    provider_user_id: str = Field(min_length=1, max_length=255)
    email_verified: bool = False


class AuthSyncResponse(BaseModel):
    """Result of an /auth/sync call -- tells the frontend what happened."""

    user_id: UUID
    organization_id: UUID
    # True if this call created the user row (first login ever).
    is_new_user: bool
    # True if this call linked a new provider to an existing user
    # (e.g. user signed up with Microsoft, now linking Google for the first time).
    is_new_provider_link: bool
    # JWT for subsequent API calls (NextAuth stores in session, frontend
    # forwards as Authorization: Bearer <token> on every protected request).
    access_token: str


# ---------------------------------------------------------------------------
# Email/password registration + login (Credentials provider support)
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """Sign-up payload: email + password + display name.

    Password policy (V1): >= 8 chars AND contains at least one digit.
    Email verification deferred to V1.5 (SendGrid integration).
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def password_must_contain_digit(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class RegisterResponse(BaseModel):
    """Result of a successful sign-up."""

    user_id: UUID
    organization_id: UUID
    # JWT for the freshly-created session.
    access_token: str


class LoginRequest(BaseModel):
    """Sign-in payload for the email/password provider."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """User info returned to NextAuth's authorize() callback on success.

    NextAuth uses these fields to populate the JWT session payload.
    """

    user_id: UUID
    organization_id: UUID
    email: EmailStr
    display_name: str | None
    avatar_url: str | None
    # JWT for subsequent backend API calls.
    access_token: str


class ForgotPasswordRequest(BaseModel):
    """Request a password-reset link for an email/password account."""

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Always-ok response -- never reveals whether the account exists."""

    ok: bool = True


class ResetPasswordRequest(BaseModel):
    """Complete a reset with the emailed token + a new password.

    Same password policy as registration (>= 8 chars, contains a digit).
    """

    token: str = Field(min_length=16, max_length=256)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_must_contain_digit(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ResetPasswordResponse(BaseModel):
    """Result of a successful password reset."""

    ok: bool = True
