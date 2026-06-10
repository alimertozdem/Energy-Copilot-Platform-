#!/usr/bin/env bash
# EnergyLens backend startup: best-effort migrations, then serve.
set -euo pipefail

echo "[start] alembic upgrade head (best-effort)..."
alembic upgrade head || echo "[start] WARN: alembic upgrade failed; continuing (Supabase may already be at head)."

echo "[start] launching uvicorn on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
