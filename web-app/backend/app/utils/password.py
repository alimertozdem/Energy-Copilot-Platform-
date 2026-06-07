"""Password hashing helpers using bcrypt.

bcrypt parameters:
    cost factor = 12 (default) -- ~250ms per hash on modern CPU,
                                    strong against brute-force, weak against
                                    GPU farms (mitigated by login rate-limit,
                                    deferred to V1.5).
    bcrypt internally generates a per-password random 16-byte salt and embeds
    it in the resulting hash string -- no separate salt storage needed.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password -- returns a bcrypt hash string (60 chars).

    The output already includes the algorithm, cost, and salt prefix
    (e.g. "$2b$12$...") so it can be stored as a single Text column.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Constant-time compare plaintext against a stored bcrypt hash.

    Returns True on match, False otherwise. Never raises on mismatch --
    only on malformed input (caller treats any exception as failed auth).
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # Malformed hash string -- fail closed.
        return False
