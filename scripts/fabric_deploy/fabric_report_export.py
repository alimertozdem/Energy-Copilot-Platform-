#!/usr/bin/env python3
"""
Export Power BI report definition(s) (PBIR) into the repo so visual -> measure /
table usage becomes inspectable. READ-ONLY. Auto-loads .env.

  python fabric_report_export.py

Writes: report-design/_report_export/<report>/...  (report.json + per-page/visual JSON
that reference the measures + columns each visual actually binds to). This is what
lets us detect genuinely-unused measures and unused (battery) tables safely.
"""
from __future__ import annotations

import base64
import sys
import time

import requests

from fabric_audit import FABRIC_API, REPO_ROOT, _env, _load_env_file, api_list, get_token


def _hdr(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def get_definition(tok: str, ws: str, rid: str) -> list:
    url = f"{FABRIC_API}/workspaces/{ws}/reports/{rid}/getDefinition"
    r = requests.post(url, headers=_hdr(tok), timeout=120)
    if r.status_code == 200:
        return r.json()["definition"]["parts"]
    if r.status_code == 202:
        op = r.headers.get("Location")
        for _ in range(40):
            time.sleep(float(r.headers.get("Retry-After", 3) or 3))
            s = requests.get(op, headers=_hdr(tok), timeout=60)
            if s.status_code != 200:
                continue
            st = (s.json() or {}).get("status", "")
            if st == "Succeeded":
                res = requests.get(op.rstrip("/") + "/result", headers=_hdr(tok), timeout=120)
                res.raise_for_status()
                return res.json()["definition"]["parts"]
            if st in ("Failed", "Undeliverable", "Cancelled"):
                raise SystemExit(f"getDefinition {st}: {s.text[:300]}")
        raise SystemExit("getDefinition timed out")
    raise SystemExit(f"getDefinition HTTP {r.status_code}: {r.text[:400]}")


def main() -> None:
    _load_env_file(REPO_ROOT / "web-app" / "backend" / ".env")
    _load_env_file(REPO_ROOT / ".env")
    ws = _env("FABRIC_WORKSPACE_ID")
    if not ws:
        sys.exit("Set FABRIC_WORKSPACE_ID.")
    tok = get_token()

    reports = api_list(tok, f"/workspaces/{ws}/reports")
    if not reports:
        sys.exit("No reports found in the workspace.")
    print(f"Reports ({len(reports)}):")
    for r in reports:
        print(f"  {r['displayName']}  ->  {r['id']}")

    base = REPO_ROOT / "report-design" / "_report_export"
    for rep in reports:
        safe = "".join(c if (c.isalnum() or c in "-_ .") else "_" for c in rep["displayName"]).strip()
        print(f"\nExporting '{rep['displayName']}' ...")
        try:
            parts = get_definition(tok, ws, rep["id"])
        except SystemExit as e:
            print(f"  skip: {e}")
            continue
        n = 0
        for prt in parts:
            if prt.get("payloadType") != "InlineBase64":
                continue
            dest = base / safe / prt.get("path", "unknown")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(base64.b64decode(prt["payload"]))
            n += 1
        print(f"  wrote {n} files -> report-design/_report_export/{safe}/")

    print("\nDone (read-only). Report PBIR is now in report-design/_report_export/.")


if __name__ == "__main__":
    main()
