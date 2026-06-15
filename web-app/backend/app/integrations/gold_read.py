"""Gold reader — Postgres-materialized first, Fabric SQL fallback.

Services call gold_read.query()/scalar() with their normal Fabric (T-SQL) query.
On Azure the Fabric SQL endpoint is unreachable, so we translate the query to the
materialized mv_ Postgres tables (reachable + fast) and run it there; if that
fails (table not yet materialized / pg error) we fall back to the original Fabric
query (which still works in local dev). format_in_clause stays in fabric_sql.

Translation (the services use only these T-SQL-isms):
  * [dbo].[gold_X] / [dbo].[silver_X]  -> mv_X     (strip gold_/silver_, prefix mv_)
  * SELECT TOP (n) ...                 -> ... LIMIT n   (param moved to the end)
  * '?' placeholders                   -> '%s'          (done inside pg_gold)
"""
import re
from typing import Any

from app.integrations import fabric_sql, pg_gold

_TBL = re.compile(r"\[dbo\]\.\[(?:gold|silver)_([a-z0-9_]+)\]", re.IGNORECASE)
_TOP = re.compile(r"select\s+top\s*\(\s*(\?|\d+)\s*\)", re.IGNORECASE)


def _translate(sql: str, params: tuple) -> tuple[str, tuple]:
    sql = _TBL.sub(lambda m: "mv_" + m.group(1), sql)
    m = _TOP.search(sql)
    if m:
        sql = _TOP.sub("SELECT", sql, count=1)
        if m.group(1) == "?":
            sql = sql.rstrip().rstrip(";") + " LIMIT ?"
            params = tuple(params[1:]) + (params[0],)  # TOP(?) is the first placeholder
        else:
            sql = sql.rstrip().rstrip(";") + f" LIMIT {m.group(1)}"
    return sql, params


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    try:
        psql, pparams = _translate(sql, params)
        return pg_gold.execute_query(psql, pparams)
    except Exception:
        # mv_ table missing / pg error -> Fabric (works locally; unreachable on Azure)
        return fabric_sql.execute_query(sql, params)


def scalar(sql: str, params: tuple = ()) -> Any:
    rows = query(sql, params)
    if not rows:
        return None
    return next(iter(rows[0].values()))
