"""
Smoke test for Fabric Lakehouse SQL Analytics Endpoint via ODBC.

Validates that:
  1. ODBC Driver 18 is installed correctly.
  2. The service principal can authenticate against the Lakehouse SQL endpoint
     (workspace Member role grants SQL endpoint access automatically — no
     dataset Build permission needed, no ExecuteQueries tenant settings).
  3. We can discover the schema (dbo vs custom schema).
  4. We can SELECT from silver_building_master.

Run:
    cd web-app/backend
    .\\venv\\Scripts\\Activate.ps1
    python -m scripts.smoke_sql
"""

import os
import sys
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=True)

# Existing PBI service principal credentials are reused (same SP, same tenant)
TENANT_ID = os.environ["PBI_TENANT_ID"]
CLIENT_ID = os.environ["PBI_CLIENT_ID"]
CLIENT_SECRET = os.environ["PBI_CLIENT_SECRET"]

# New Fabric SQL endpoint variables
SERVER = os.environ["FABRIC_SQL_SERVER"]
DATABASE = os.environ["FABRIC_SQL_DATABASE"]
DRIVER = os.environ.get("FABRIC_SQL_DRIVER", "ODBC Driver 18 for SQL Server")


def build_connection_string() -> str:
    """
    Build ODBC connection string for service principal authentication
    against the Fabric SQL Analytics Endpoint.

    Authentication=ActiveDirectoryServicePrincipal — uses UID (client_id)
    and PWD (client_secret); the driver derives the tenant from the audience.
    Authority Id is supplied explicitly for cross-tenant safety.
    """
    return (
        f"Driver={{{DRIVER}}};"
        f"Server={SERVER};"
        f"Database={DATABASE};"
        f"Authentication=ActiveDirectoryServicePrincipal;"
        f"UID={CLIENT_ID};"
        f"PWD={CLIENT_SECRET};"
        f"Authority Id={TENANT_ID};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )


def main() -> int:
    print("[1/4] Verifying ODBC driver...")
    drivers = pyodbc.drivers()
    if DRIVER not in drivers:
        print(f"      ❌ '{DRIVER}' NOT installed.")
        print(f"      Installed ODBC drivers: {drivers}")
        return 1
    print(f"      ✅ '{DRIVER}' is installed")

    print(f"\n[2/4] Connecting to Fabric SQL endpoint...")
    print(f"      Server:   {SERVER}")
    print(f"      Database: {DATABASE}")
    print(f"      Auth:     ActiveDirectoryServicePrincipal (SP: {CLIENT_ID[:8]}...)")
    try:
        conn = pyodbc.connect(build_connection_string())
    except pyodbc.Error as e:
        print(f"      ❌ Connection failed: {e}")
        return 1
    print("      ✅ Connected")

    cur = conn.cursor()

    print("\n[3/4] Schema discovery — listing tables...")
    cur.execute(
        """
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
    )
    tables = cur.fetchall()
    print(f"      Found {len(tables)} table(s):")
    print(f"      {'SCHEMA':<20} {'NAME':<45} TYPE")
    print(f"      {'-' * 20} {'-' * 45} ----")
    for schema, name, ttype in tables:
        print(f"      {schema:<20} {name:<45} {ttype}")

    # Detect the schema that contains silver_building_master
    target_schema = None
    for schema, name, _ in tables:
        if name == "silver_building_master":
            target_schema = schema
            break

    if not target_schema:
        print("\n      ⚠️  silver_building_master not found in any schema.")
        return 2

    print(f"\n      → silver_building_master lives in schema: '{target_schema}'")

    print("\n[4/4] SELECT TOP 5 silver_building_master ...")
    cur.execute(
        f"SELECT TOP 5 * FROM [{target_schema}].[silver_building_master]"
    )
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()

    print(f"      Columns ({len(columns)}): {columns}")
    print(f"      Rows returned: {len(rows)}")
    print()
    for i, row in enumerate(rows, 1):
        print(f"      Row {i}:")
        for col, val in zip(columns, row):
            print(f"        {col:30s} = {val}")
        print()

    conn.close()
    print("✅ Smoke test passed. Plan B is viable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
