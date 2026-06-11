"""
Fabric Lakehouse SQL Analytics Endpoint client.

Service principal connects via ODBC Driver 18 (TDS protocol). Workspace
Member role grants automatic SQL endpoint access — no ExecuteQueries
permissions, no dataset Build, no tenant setting gymnastics. See
`feedback_fabric_executequeries_sp.md` in memory for the history.

Reads use parameterized queries (`?` placeholders) to keep the query plan
cache hot and to prevent SQL injection.
"""

import logging
import os
import threading
import time
from typing import Any, Iterable

import pyodbc

logger = logging.getLogger(__name__)

# pyodbc native connection pooling is on by default. Set explicitly so
# the behavior survives a future driver default change.
pyodbc.pooling = True

# --- Optional short-TTL read cache (perf) -----------------------------------
# The SQL Analytics Endpoint (DirectLake over ODBC) can be slow on cold queries,
# and every page blocks on it server-side. This caches SELECT results in-process
# for FABRIC_SQL_CACHE_TTL seconds so repeat navigations (portfolio → building →
# back) are instant. The cache key includes the params tuple, which carries the
# caller's RLS scope (the building-id IN-list) — so two users with different
# visible buildings never share a cache entry. Status overlays live in Postgres
# (not cached here), so they still reflect immediately.
#
# Default 0 = DISABLED (no behaviour change). Set e.g. FABRIC_SQL_CACHE_TTL=45
# in .env to enable, then measure. Stale window is bounded by the TTL.
_CACHE_LOCK = threading.Lock()
_CACHE: dict[tuple[str, tuple], tuple[float, list]] = {}
_CACHE_MAX = 256  # hard cap on distinct cached queries (cheap memory guard)


def _cache_ttl() -> float:
    try:
        return float(os.getenv("FABRIC_SQL_CACHE_TTL", "0") or 0)
    except ValueError:
        return 0.0


# The Fabric SQL Analytics Endpoint resumes from idle on the first connection,
# which can take ~20s. pyodbc's default login timeout is 15s, so a cold endpoint
# surfaces as 'Login timeout expired (SQLDriverConnect)'. We therefore set the
# login timeout explicitly in get_connection(). Overridable via env for tuning.
_DEFAULT_LOGIN_TIMEOUT = 90


def _login_timeout() -> int:
    try:
        return int(os.getenv("FABRIC_SQL_LOGIN_TIMEOUT", "") or _DEFAULT_LOGIN_TIMEOUT)
    except ValueError:
        return _DEFAULT_LOGIN_TIMEOUT


def _build_connection_string() -> str:
    """
    Compose the ODBC connection string from environment variables.

    Required env vars:
      FABRIC_SQL_SERVER     — Lakehouse SQL endpoint hostname
      FABRIC_SQL_DATABASE   — Lakehouse name
      FABRIC_SQL_DRIVER     — Optional, defaults to 'ODBC Driver 18 for SQL Server'
      PBI_TENANT_ID         — Reused from existing Power BI service principal
      PBI_CLIENT_ID         — Reused
      PBI_CLIENT_SECRET     — Reused

    The login timeout is NOT set here: the "Connection Timeout=" keyword is a
    SqlClient (ADO.NET) keyword that the ODBC driver ignores. It is passed to
    pyodbc.connect() as the `timeout` argument instead (see get_connection).
    """
    server = os.environ["FABRIC_SQL_SERVER"]
    database = os.environ["FABRIC_SQL_DATABASE"]
    driver = os.environ.get("FABRIC_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    tenant_id = os.environ["PBI_TENANT_ID"]
    client_id = os.environ["PBI_CLIENT_ID"]
    client_secret = os.environ["PBI_CLIENT_SECRET"]
    return (
        f"Driver={{{driver}}};"
        f"Server={server};"
        f"Database={database};"
        f"Authentication=ActiveDirectoryServicePrincipal;"
        f"UID={client_id};"
        f"PWD={client_secret};"
        f"Authority Id={tenant_id};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )


# Module-level cached connection string. Lazy — built on first call so that
# dotenv has time to load when this module is imported during app startup.
_CONN_STRING: str | None = None


def _get_connection_string() -> str:
    global _CONN_STRING
    if _CONN_STRING is None:
        _CONN_STRING = _build_connection_string()
    return _CONN_STRING


def get_connection() -> pyodbc.Connection:
    """
    Open a connection (or pull one from the pyodbc native pool).

    Callers should use the `with` context manager so the connection is
    released back to the pool on exit:

        with fabric_sql.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)

    `timeout` sets the ODBC login timeout (SQL_ATTR_LOGIN_TIMEOUT) so a cold
    Fabric SQL endpoint resuming from idle (~20s) doesn't trip the 15s default.
    """
    return pyodbc.connect(_get_connection_string(), timeout=_login_timeout())


def execute_query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """
    Run a SELECT and return rows as a list of dicts (column_name -> value).

    Use `?` placeholders for every caller-supplied value — never f-strings.
    The driver handles SQL escaping; building queries with string interpolation
    risks injection AND breaks the query plan cache.

    Retries once on OperationalError (transient connection failures).
    ProgrammingError (SQL syntax / schema mismatch) is surfaced immediately
    since that means a bug in our code, not a flaky network.

    When FABRIC_SQL_CACHE_TTL > 0, identical (sql, params) reads are served from
    an in-process cache for that many seconds (see module note above).
    """
    ttl = _cache_ttl()
    cache_key = (sql, tuple(params))
    if ttl > 0:
        now = time.time()
        with _CACHE_LOCK:
            hit = _CACHE.get(cache_key)
            if hit is not None and hit[0] > now:
                # Return a copy so callers can't mutate the cached list.
                return [dict(r) for r in hit[1]]

    last_error: Exception | None = None
    for attempt in (1, 2):
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                columns = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows]
                if ttl > 0:
                    with _CACHE_LOCK:
                        if len(_CACHE) >= _CACHE_MAX:
                            _CACHE.clear()  # simplest bounded eviction
                        _CACHE[cache_key] = (time.time() + ttl, result)
                return [dict(r) for r in result] if ttl > 0 else result
        except pyodbc.OperationalError as e:
            last_error = e
            logger.warning(
                "Fabric SQL connection failure (attempt %d/2): %s",
                attempt, e,
            )
            if attempt == 2:
                raise
        except pyodbc.ProgrammingError:
            # SQL/schema bug on our side — don't retry, surface immediately.
            raise
    # Defensive: loop always returns or raises; this satisfies type checkers.
    raise last_error  # type: ignore[misc]


def execute_scalar(sql: str, params: tuple = ()) -> Any:
    """
    Run a query and return the first column of the first row.

    Returns None when the result set is empty. Useful for single-value
    aggregates: SELECT SUM(...), SELECT COUNT(*), etc.
    """
    rows = execute_query(sql, params)
    if not rows:
        return None
    first_row = rows[0]
    return next(iter(first_row.values()))


def format_in_clause(values: Iterable[Any]) -> tuple[str, tuple]:
    """
    Build a SQL `?, ?, ?` placeholder block plus a matching params tuple
    for use inside an `IN (...)` clause.

    Empty input maps to `NULL` which makes the IN clause always false —
    safer than emitting `IN ()` (which is invalid SQL).

    Usage:
        ph, params = format_in_clause(["B001", "B003"])
        sql = f"SELECT * FROM [dbo].[gold_kpi_daily] WHERE building_id IN ({ph})"
        rows = fabric_sql.execute_query(sql, params)
    """
    values_tuple = tuple(values)
    if not values_tuple:
        return "NULL", ()
    placeholders = ", ".join(["?"] * len(values_tuple))
    return placeholders, values_tuple
