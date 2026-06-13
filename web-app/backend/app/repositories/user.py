"""DB operations for User and UserAuthProvider models.

Repository pattern: thin functions that wrap SQLAlchemy queries.
Callers (endpoints, services) compose these into business workflows
and are responsible for the final db.commit().
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User, UserAuthProvider


def find_user_by_email(db: Session, email: str) -> User | None:
    """Return the User row matching this email, or None."""
    return db.scalar(select(User).where(User.email == email))


def create_user(
    db: Session,
    *,
    email: str,
    display_name: str | None,
    avatar_url: str | None,
) -> User:
    """Insert a new User row. Caller must commit."""
    user = User(
        email=email,
        display_name=display_name,
        avatar_url=avatar_url,
    )
    db.add(user)
    db.flush()  # populates user.id without committing
    return user


def find_auth_provider(
    db: Session,
    *,
    provider: str,
    provider_user_id: str,
) -> UserAuthProvider | None:
    """Find an auth-provider link by (provider, provider_user_id) pair."""
    return db.scalar(
        select(UserAuthProvider).where(
            UserAuthProvider.provider == provider,
            UserAuthProvider.provider_user_id == provider_user_id,
        )
    )


def create_auth_provider(
    db: Session,
    *,
    user_id: UUID,
    provider: str,
    provider_user_id: str,
    email_verified: bool,
    password_hash: str | None = None,
) -> UserAuthProvider:
    """Insert a new auth-provider link for a User. Caller must commit."""
    auth = UserAuthProvider(
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        email_verified=email_verified,
        password_hash=password_hash,
    )
    db.add(auth)
    db.flush()
    return auth


def touch_last_login(db: Session, user: User) -> None:
    """Update user.last_login_at = NOW() (Python-side UTC timestamp)."""
    user.last_login_at = datetime.now(timezone.utc)


def get_show_sample_data(db: Session, user_id: UUID) -> bool:
    """Return the user's sample/demo visibility flag (default True)."""
    val = db.scalar(select(User.show_sample_data).where(User.id == user_id))
    return bool(val) if val is not None else True


def set_show_sample_data(db: Session, user_id: UUID, enabled: bool) -> None:
    """Set the user's sample/demo visibility flag. Commits."""
    user = db.scalar(select(User).where(User.id == user_id))
    if user is not None:
        user.show_sample_data = enabled
        db.commit()


def is_platform_admin(db: Session, user_id: UUID) -> bool:
    """Whether the user is a platform admin (founder)."""
    val = db.scalar(select(User.is_platform_admin).where(User.id == user_id))
    return bool(val)


def get_email(db: Session, user_id: UUID) -> str | None:
    """The user's email -- used to flag shared demo/test accounts."""
    return db.scalar(select(User.email).where(User.id == user_id))
