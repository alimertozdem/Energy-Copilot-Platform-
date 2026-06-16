"""Gold reader — Postgres-materialized first, Fabric SQL fallback.

Services call gold_read.query()/scalar() with their normal Fabric (T-SQL) query.
On Azure the Fabric SQL endpoint is unreachable, so we translate the query to the
materialized mv_ Postgres tables and run it there; on any failure we fall back to
the original Fabric query (still works in local dev). format_in_clause stays in
fabric_sql.

Translation (T-SQL -> Postgres):
  * [dbo].[gold_X] / [dbo].[silver_X]  -> mv_X
  * [date]                             -> ("date"::date)   (date col is ISO text)
  * [other_col]                        -> "other_col"      (T-SQL bracket-quoting)
  * SELECT TOP (n) ...                 -> ... LIMIT n
  * ISNULL(a, b)                       -> COALESCE(a, b)
  * CAST(x AS bit)                     -> CAST(x AS boolean)
  * is_*/has_* = 0 | 1                 -> = false | true   (bit col -> pg boolean)
  * '?' placeholders                   -> '%s'  (inside pg_gold)

The Fabric fallback always runs the ORIGINAL T-SQL, so these rewrites only ever
affect the Postgres path.
"""
import re
from typing import Any

from app.integrations import fabric_sql, pg_gold

_TBL = re.compile(r"\[dbo\]\.\[(?:gold|silver)_([a-z0-9_]+)\]", re.IGNORECASE)
_DATE = re.compile(r"\[date\]", re.IGNORECASE)
_BRACKET = re.compile(r"\[([a-zA-Z_][a-zA-Z0-9_]*)\]")
_TOP = re.compile(r"select\s+top\s*\(\s*(\?|\d+)\s*\)", re.IGNORECASE)
# T-SQL -> pg compatibility (mv_ columns are real pg types: numeric, boolean, ...)
_ISNULL = re.compile(r"\bISNULL\s*\(", re.IGNORECASE)
_AS_BIT = re.compile(r"\bAS\s+bit\s*\)", re.IGNORECASE)
# is_*/has_* flags are bit (0/1) in T-SQL but boolean in the mv_ tables; an
# integer comparison errors on Postgres ("operator does not exist: boolean = integer").
_BOOL_FLAG = re.compile(r'"?\b((?:is|has)_[a-z0-9_]+)\b"?\s*=\s*([01])\b', re.IGNORECASE)


def _bool_flag_sub(m: "re.Match[str]") -> str:
    return f"{m.group(1)} = {'true' if m.group(2) == '1' else 'false'}"


def _translate(sql: str, params: tuple) -> tuple[str, tuple]:
    sql = _TBL.sub(lambda m: "mv_" + m.group(1), sql)
    # date column is materialized as ISO text -> cast so range/year ops work
    # (a no-op if the column is already a real date type).
    sql = _DATE.sub('("date"::date)', sql)
    sql = _BRACKET.sub(lambda m: '"' + m.group(1) + '"', sql)
    # T-SQL function / type / boolean-literal compatibility.
    sql = _ISNULL.sub("COALESCE(", sql)
    sql = _AS_BIT.sub("AS boolean)", sql)
    sql = _BOOL_FLAG.sub(_bool_flag_sub, sql)
    m = _TOP.search(sql)
    if m:
        sql = _TOP.sub("SELECT", sql, count=1)
        if m.group(1) == "?":
            sql = sql.rstrip().rstrip(";") + " LIMIT ?"
            params = tuple(params[1:]) + (params[0],)
        else:
            sql = sql.rstrip().rstrip(";") + f" LIMIT {m.group(1)}"
    return sql, params


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    try:
        psql, pparams = _translate(sql, params)
        return pg_gold.execute_query(psql, pparams)
    except Exception:
        return fabric_sql.execute_query(sql, params)


def scalar(sql: str, params: tuple = ()) -> Any:
    rows = query(sql, params)
    if not rows:
        return None
    return next(iter(rows[0].values()))
