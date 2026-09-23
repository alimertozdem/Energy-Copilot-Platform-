"""02_run_pipeline.py -- execute the SQL layers in order against DuckDB."""
import duckdb, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SQL  = HERE.parent / "sql"
# Override with  DUCKDB_PATH=/some/where/energy.duckdb  if your output folder is
# on a synced drive (OneDrive/Dropbox lock the write-ahead log and DuckDB fails).
import os
DB   = Path(os.environ.get("DUCKDB_PATH", HERE.parent / "output" / "energy.duckdb"))
DB.parent.mkdir(exist_ok=True, parents=True)

STEPS = ["01_bronze.sql", "02_silver.sql", "03_gold.sql"]
if len(sys.argv) > 1:
    STEPS = sys.argv[1:]

con = duckdb.connect(str(DB))
con.execute("SET TimeZone='UTC'")
os.chdir(SQL)          # so the relative ../data/ paths resolve

for f in STEPS:
    p = SQL / f
    if not p.exists():
        print(f"  skip {f} (not found)"); continue
    t0 = time.time()
    con.execute(p.read_text())
    print(f"  ran {f:18s} in {time.time()-t0:5.2f}s")

tables = con.execute("""
    SELECT table_name, estimated_size FROM duckdb_tables()
    ORDER BY CASE WHEN table_name LIKE 'bronze%' THEN 1
                  WHEN table_name LIKE 'silver%' THEN 2
                  WHEN table_name LIKE 'qa%'     THEN 3
                  ELSE 4 END, table_name""").fetchall()
print("\n  LAYER TABLES")
for t, n in tables:
    print(f"    {t:28s} {int(n):>10,d} rows")
con.close()
