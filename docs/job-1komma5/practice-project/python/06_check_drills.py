"""
06_check_drills.py -- instant feedback on the SQL drills.

Runs each statement from drills/my_answers.sql, runs the matching statement from
drills/reference_solutions.sql, and compares. Expected answers are DERIVED at
runtime, so they always match your regenerated data.

Comparison is deliberately forgiving about column names and column order, and
strict about the numbers and the row count -- i.e. it grades the logic, not the
cosmetics.
"""
import duckdb, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRILLS = HERE.parent / "drills"
DB = Path(os.environ.get("DUCKDB_PATH", HERE.parent / "output" / "energy.duckdb"))

HINTS = {
 "D1": "Group by the business key and keep only groups with COUNT(*) > 1, then count those groups.",
 "D2": "You cannot find a missing row in the rows you have. Start FROM silver_calendar and LEFT JOIN the meter, then keep the NULLs.",
 "D3": "Volume-weighted means SUM(price*volume)/SUM(volume). AVG(price) is the wrong one -- return both so you can see the gap.",
 "D4": "silver_prices already has ts_local. ORDER BY price DESC LIMIT 5.",
 "D5": "DATE_TRUNC('month', local_date) to bucket, COUNT(*) FILTER (WHERE is_negative_price) to count, HAVING to drop empty months.",
 "D6": "gold_mako_funnel has reject_count and days_to_supply. Filter reject_count > 0.",
 "D7": "100.0 * COUNT(*) FILTER (WHERE reject_count = 0) / COUNT(*), grouped by dso_name.",
 "D8": "MAX(spot) - MIN(spot) per local_date, ORDER BY that DESC LIMIT 10.",
 "D9": "Aggregate to daily in a CTE first, then AVG(daily) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW).",
 "D10":"Three columns, not three rows: AVG(saving_pct) FILTER (WHERE month = DATE '2025-02-01') and so on.",
}

def split_blocks(text):
    out, cur, key = {}, [], None
    for line in text.splitlines():
        m = re.match(r"^\s*--\s*(D\d+)\s*$", line)
        if m:
            if key: out[key] = "\n".join(cur).strip()
            key, cur = m.group(1), []
        elif key is not None:
            cur.append(line)
    if key: out[key] = "\n".join(cur).strip()
    return {k: re.sub(r"--.*", "", v).strip() for k, v in out.items()}

def signature(df):
    """Canonical form: row count + every numeric cell rounded, sorted; plus any
    text/date cells sorted. Ignores column names and column order."""
    nums, txts = [], []
    for col in df.columns:
        for v in df[col].tolist():
            if isinstance(v, bool): txts.append(str(v))
            elif isinstance(v, (int, float)) and v == v: nums.append(round(float(v), 2))
            elif v is None: txts.append("NULL")
            else: txts.append(str(v)[:19])
    return (len(df), tuple(sorted(nums)), tuple(sorted(txts)))

mine = split_blocks((DRILLS / "my_answers.sql").read_text())
ref  = split_blocks((DRILLS / "reference_solutions.sql").read_text())

con = duckdb.connect(str(DB), read_only=True); con.execute("SET TimeZone='UTC'")
order = sorted(ref, key=lambda k: int(k[1:]))
passed = attempted = 0
print("=" * 72)
for k in order:
    want_df = con.execute(ref[k]).df()
    got = mine.get(k, "").strip().rstrip(";").strip()
    if not got:
        print(f"  {k}  ..  not attempted yet")
        continue
    attempted += 1
    try:
        got_df = con.execute(got).df()
    except Exception as e:
        print(f"  {k}  FAIL  SQL error: {str(e).splitlines()[0][:80]}")
        print(f"          hint: {HINTS[k]}")
        continue
    if signature(got_df) == signature(want_df):
        passed += 1
        print(f"  {k}  PASS  ({len(got_df)} row{'s' if len(got_df)!=1 else ''})")
    else:
        gr, wr = len(got_df), len(want_df)
        why = (f"row count {gr}, expected {wr}" if gr != wr
               else "right shape, wrong numbers")
        print(f"  {k}  FAIL  {why}")
        print(f"          hint: {HINTS[k]}")
        if gr <= 12 and wr <= 12:
            print(f"          yours:    {got_df.to_string(index=False)[:300]}")
            print(f"          expected: {want_df.to_string(index=False)[:300]}")
con.close()
print("=" * 72)
print(f"  {passed}/{len(order)} passed   ({attempted} attempted)")
if passed == len(order):
    print("  All ten. You can write this from scratch now -- that is the point.")
