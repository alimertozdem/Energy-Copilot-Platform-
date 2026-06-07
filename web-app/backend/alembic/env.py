"""Alembic migration environment.

Reads DATABASE_URL from .env and binds Base.metadata so autogenerate
sees all our ORM models.
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Make 'app.*' importable when alembic runs from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Load .env BEFORE importing app modules (DATABASE_URL must exist).
load_dotenv()

from app.db.database import Base  # noqa: E402
from app.db import models  # noqa: E402, F401  -- registers all models on Base

# Alembic Config object -- access to alembic.ini values.
config = context.config

# Override the dummy sqlalchemy.url in alembic.ini with the real one from .env
# (and apply the psycopg3 driver prefix).
_raw_url = os.getenv("DATABASE_URL")
if not _raw_url:
    raise RuntimeError("DATABASE_URL is not set in .env")
if _raw_url.startswith("postgresql://"):
    _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
config.set_main_option("sqlalchemy.url", _raw_url)

# Python logging from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata target for autogenerate -- ALL our models.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL only, no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the live database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
