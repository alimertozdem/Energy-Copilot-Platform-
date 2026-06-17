#!/usr/bin/env python3
"""
Export the Fabric semantic model definition (TMDL) into the repo so it becomes
reviewable file-by-file. READ-ONLY - writes nothing to Fabric. Auto-loads .env.

  python fabric_model_export.py

Writes: semantic-model/_model_export/<model>/...
  -> tables (columns, data types, storage mode), relationships, measures, partitions.
Reuses the same service principal as the bridge / audit / deploy tools.
"""
from __future__ import annotations

import base64
import sys
import time

import requests

from fabric_audit import FABRIC_API, REPO_ROOT, _env, _load_env_file, api_list, get_token


def _hdr(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def get_definition(tok: str, ws: str, mid: str) -> list:
    """getDefinition (TMDL). Handles the 202 long-running-operation pattern."""
    url = f"{FABRIC_API}/workspaces/{ws}/semanticModels/{mid}/getDefinition?format=TMDL"
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

    models = api_list(tok, f"/workspaces/{ws}/semanticModels")
    if not models:
        sys.exit("No semantic models found in the workspace.")
    print(f"Semantic models ({len(models)}):")
    for m in models:
        print(f"  {m['displayName']}  ->  {m['id']}")

    base = REPO_ROOT / "semantic-model" / "_model_export"
    for m in models:
        safe = "".join(c if (c.isalnum() or c in "-_ .") else "_" for c in m["displayName"]).strip()
        print(f"\nExporting '{m['displayName']}' (TMDL) ...")
        try:
            parts = get_definition(tok, ws, m["id"])
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
        print(f"  wrote {n} files -> semantic-model/_model_export/{safe}/")

    print("\nDone (read-only). Model TMDL is now in semantic-model/_model_export/.")


if __name__ == "__main__":
    main()
