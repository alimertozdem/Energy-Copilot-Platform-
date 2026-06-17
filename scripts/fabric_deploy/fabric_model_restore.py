#!/usr/bin/env python3
"""
RESTORE EnergyCopilotModel to the pre-trim definition in
semantic-model/_model_export/EnergyCopilotModel/ (the original, untrimmed model).

Pushes every original TMDL part via updateDefinition. Default dry-run; --apply pushes.
AFTER --apply: re-run the DirectLake rebind (notebooks/gold/91_rebind_directlake.py)
because updateDefinition unbinds the lakehouse connection.

  python fabric_model_restore.py            # show what will be pushed
  python fabric_model_restore.py --apply    # restore the original model
"""
from __future__ import annotations

import argparse
import base64
import sys

import requests

from fabric_audit import FABRIC_API, REPO_ROOT, _env, _load_env_file, api_list, get_token

EXPORT = REPO_ROOT / "semantic-model" / "_model_export" / "EnergyCopilotModel"
MODEL_NAME = "EnergyCopilotModel"


def _hdr(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def build_parts() -> list:
    parts = []
    for f in sorted(EXPORT.rglob("*")):
        if f.is_dir():
            continue
        rel = str(f.relative_to(EXPORT)).replace("\\", "/")
        if rel == ".platform":
            continue
        parts.append({
            "path": rel,
            "payload": base64.b64encode(f.read_bytes()).decode(),
            "payloadType": "InlineBase64",
        })
    return parts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not EXPORT.exists():
        sys.exit("Original model export not found at semantic-model/_model_export/.")
    parts = build_parts()
    print(f"Original parts to restore: {len(parts)}")
    for p in parts:
        print(f"   {p['path']}")
    if not args.apply:
        print("\nDRY-RUN. Re-run with --apply to restore.")
        return

    _load_env_file(REPO_ROOT / "web-app" / "backend" / ".env")
    _load_env_file(REPO_ROOT / ".env")
    ws = _env("FABRIC_WORKSPACE_ID")
    tok = get_token()
    models = {m["displayName"]: m["id"] for m in api_list(tok, f"/workspaces/{ws}/semanticModels")}
    mid = models.get(MODEL_NAME)
    if not mid:
        sys.exit(f"Model '{MODEL_NAME}' not found.")
    print(f"\nRestoring original definition to '{MODEL_NAME}' ({mid}) ...")
    r = requests.post(
        f"{FABRIC_API}/workspaces/{ws}/semanticModels/{mid}/updateDefinition",
        headers=_hdr(tok), json={"definition": {"parts": parts}}, timeout=180,
    )
    if r.status_code in (200, 201):
        print("OK — original model restored.")
    elif r.status_code == 202:
        print(f"Accepted (202, long-running): {r.headers.get('Location','(portal)')}")
    else:
        print(f"FAILED ({r.status_code}): {r.text[:500]}")
        sys.exit(1)
    print("\nNEXT: re-run the rebind cell (notebooks/gold/91_rebind_directlake.py) to reconnect the lakehouse,")
    print("then the model is back to its pre-trim working state (298 measures, working RLS).")


if __name__ == "__main__":
    main()
