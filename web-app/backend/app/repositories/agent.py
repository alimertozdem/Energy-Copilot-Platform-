"""Repository for agent_tokens (edge-agent credentials, stored hashed)."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.agent import AgentToken


def create_token(
    db: Session, *, building_id: UUID, name: str, token_hash: str, token_prefix: str
) -> AgentToken:
    """Create a token row (caller passes the already-hashed value). Caller commits."""
    tok = AgentToken(
        building_id=building_id,
        name=name,
        token_hash=token_hash,
        token_prefix=token_prefix,
    )
    db.add(tok)
    db.flush()
    return tok


def list_tokens(db: Session, *, building_id: UUID) -> list[AgentToken]:
    return list(
        db.scalars(
            select(AgentToken)
            .where(AgentToken.building_id == building_id)
            .order_by(AgentToken.created_at.desc())
        ).all()
    )


def get_for_building(
    db: Session, *, building_id: UUID, token_id: UUID
) -> AgentToken | None:
    return db.scalar(
        select(AgentToken).where(
            AgentToken.id == token_id, AgentToken.building_id == building_id
        )
    )


def get_active_by_hash(db: Session, *, token_hash: str) -> AgentToken | None:
    """Resolve a presented token (by its hash) to an ACTIVE (non-revoked) row."""
    return db.scalar(
        select(AgentToken).where(
            AgentToken.token_hash == token_hash,
            AgentToken.revoked_at.is_(None),
        )
    )


def revoke(db: Session, *, token: AgentToken) -> AgentToken:
    token.revoked_at = datetime.now(timezone.utc)
    return token


def touch(db: Session, *, token: AgentToken) -> None:
    token.last_used_at = datetime.now(timezone.utc)
