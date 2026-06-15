"""Postgres reader for materialized Fabric gold (mv_ tables).

The Azure backend cannot reach the Fabric SQL endpoint, so a Fabric notebook
materializes the gold columns the app needs into Supabase mv_ tables. This module
reads them through the app's existing SQLAlchemy engine and exposes the SAME helper
API as fabric_sql (execute_query / execute_scalar / format_in_clause), so a service
can run one SQL skeleton against either source. Placeholders use '?' (translated to
psycopg '%s'); identical to fabric_sql.
"""
from typing import Any, Iterable

from app.db.database import engine


def execute_query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    pg_sql = sql.replace("?", "%s")
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute(pg_sql, params)
        if cur.description is None:
            return []
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        raw.close()


def execute_scalar(sql: str, params: tuple = ()) -> Any:
    rows = execute_query(sql, params)
    if not rows:
        return None
    return next(iter(rows[0].values()))


def format_in_clause(values: Iterable[Any]) -> tuple[str, tuple]:
    values_tuple = tuple(values)
    if not values_tuple:
        return "NULL", ()
    placeholders = ", ".join(["?"] * len(values_tuple))
    return placeholders, values_tuple
