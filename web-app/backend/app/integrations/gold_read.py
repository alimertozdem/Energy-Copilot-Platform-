"""Gold reader — Postgres-materialized first, Fabric SQL fallback.

Services call gold_read.query()/scalar() with their standard query.
This stabilized version safely translates table references and T-SQL idioms
to the materialized mv_ PostgreSQL tables without brittle regex crashes.
"""
import logging
import re
from typing import Any

from app.integrations import fabric_sql, pg_gold

logger = logging.getLogger("energylens.gold_read")

_TBL = re.compile(r"\[dbo\]\.\[(?:gold|silver)_([a-z0-9_]+)\]", re.IGNORECASE)
_DATE = re.compile(r"\[date\]", re.IGNORECASE)
_BRACKET = re.compile(r"\[([a-zA-Z_][a-zA-Z0-9_]*)\]")
_TOP = re.compile(r"select\s+top\s*\(\s*(\?|\d+)\s*\)", re.IGNORECASE)
_ISNULL = re.compile(r"\bISNULL\s*\(", re.IGNORECASE)
_AS_BIT = re.compile(r"\bAS\s+bit\s*\)", re.IGNORECASE)
_BOOL_FLAG = re.compile(r'"?\b((?:is|has)_[a-z0-9_]+)\b"?\s*=\s*([01])\b', re.IGNORECASE)


def _bool_flag_sub(m: "re.Match[str]") -> str:
    return f"{m.group(1)} = {'true' if m.group(2) == '1' else 'false'}"


def _translate(sql: str, params: tuple) -> tuple[str, tuple]:
    sql = _TBL.sub(lambda m: "mv_" + m.group(1), sql)
    sql = _DATE.sub('("date"::date)', sql)
    sql = _BRACKET.sub(lambda m: '"' + m.group(1) + '"', sql)
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
    except Exception as e:
        logger.warning("Postgres mv_ query translation failed (%s), attempting Fabric fallback", e)
        try:
            return fabric_sql.execute_query(sql, params)
        except Exception as f_err:
            logger.error("Fabric fallback also failed: %s", f_err)
            return []


def scalar(sql: str, params: tuple = ()) -> Any:
    rows = query(sql, params)
    if not rows:
        return None
    return next(iter(rows[0].values()))
