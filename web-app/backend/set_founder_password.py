"""One-off: enable email/password login for an EXISTING user.

Why: a founder account created via Google has no `email` auth-provider row, so
`/auth/login` (which checks provider="email" + a bcrypt hash) can't authenticate
it. When the Google OAuth round-trip is unavailable (e.g. the Next.js server
can't reach Google's token endpoint), email/password is a Google-free way in —
it only calls the local backend (127.0.0.1), never Google.

This attaches (or resets) an `email` auth-provider row with a bcrypt password to
an already-existing user. It does NOT create a new user or org. Idempotent.

Run from web-app/backend with the backend venv active:
    python set_founder_password.py
It prompts for the email (default below) and a password (entered twice, hidden).
Then sign in at http://localhost:3000/login with that email + password.
"""
import getpass
import sys

from app.db.database import SessionLocal
from app.repositories import user as user_repo
from app.utils.password import hash_password

DEFAULT_EMAIL = "alimertozdem@gmail.com"


def main() -> None:
    email = input(f"Email [{DEFAULT_EMAIL}]: ").strip() or DEFAULT_EMAIL
    pw1 = getpass.getpass("New password: ")
    pw2 = getpass.getpass("Confirm password: ")
    if not pw1:
        sys.exit("Empty password — aborted.")
    if pw1 != pw2:
        sys.exit("Passwords do not match — aborted.")
    if len(pw1.encode("utf-8")) > 72:
        sys.exit("Password too long (bcrypt limit is 72 bytes) — pick a shorter one.")

    db = SessionLocal()
    try:
        user = user_repo.find_user_by_email(db, email)
        if user is None:
            sys.exit(
                f"No user found for {email}. Sign in once (any method) so the "
                "account exists first, then re-run this."
            )

        auth = user_repo.find_auth_provider(
            db, provider="email", provider_user_id=email
        )
        if auth is None:
            user_repo.create_auth_provider(
                db,
                user_id=user.id,
                provider="email",
                provider_user_id=email,
                email_verified=True,
                password_hash=hash_password(pw1),
            )
            action = "created"
        else:
            auth.password_hash = hash_password(pw1)
            action = "reset"

        db.commit()
        print(f"\nOK — email login {action} for user {user.id} ({email}).")
        print("Now sign in at http://localhost:3000/login with this email + password.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
