"""Estimation Engine (Tier A) — deterministic, Postgres-only, €0.

The free, transparent data-estimation engine that is the shared core under all
three commercial pillars. Pure functions over an assembled ``EngineInput`` (no
DB, no Fabric, no network), so the energy math is trivially unit-testable.

Design: docs/architecture/estimation-engine-{architecture,data,logic}.md
Energy assumptions A1-A9 signed off by the product owner on 2026-06-17.
"""
