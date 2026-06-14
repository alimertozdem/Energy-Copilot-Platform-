"""One-off: grant platform-admin (founder) to an EXISTING user → unlocks /admin.

The /admin page + the admin API are gated on users.is_platform_admin (read from
the DB per request). A Google/email account starts with this flag False, so /admin
returns 403 and no admin UI shows. This flips the flag for one user. Idempotent.

Run from web-app/backend with the backend venv active:
    python set_platform_admin.py
It prompts for the email (default below). Then SIGN OUT and SIGN IN again so the
session refreshes, and open http://localhost:3000/admin (there is no nav link —
reach it by URL).
"""
import sys

from app.db.database import SessionLocal
from app.repositories import user as user_repo

DEFAULT_EMAIL = "alimertozdem@gmail.com"


def main() -> None:
    email = input(f"Email [{DEFAULT_EMAIL}]: ").strip() or DEFAULT_EMAIL

    db = SessionLocal()
    try:
        user = user_repo.find_user_by_email(db, email)
        if user is None:
            sys.exit(
                f"No user found for {email}. Sign in once (any method) so the "
                "account exists first, then re-run this."
            )
        if user.is_platform_admin:
            print(f"Already a platform admin: {user.id} ({email}). Nothing to do.")
            return
        user.is_platform_admin = True
        db.commit()
        print(f"\nOK — {email} is now a platform admin (user {user.id}).")
        print("Sign OUT and sign IN again, then open http://localhost:3000/admin")
    finally:
        db.close()


if __name__ == "__main__":
    main()
