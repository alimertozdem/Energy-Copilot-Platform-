#!/usr/bin/env python3
"""
Fabric workspace audit + drift report + GUID registry  (READ-ONLY).

Yol 2 - step 1. Authenticates as the service principal (same SP the bridge uses),
lists the live Fabric items, cross-checks the repo's batch pipeline JSONs against
the live notebooks (drift report), writes the notebook<->GUID registry, and fetches
one live pipeline definition so we learn the exact deploy format for step 2.

This script CREATES / CHANGES NOTHING in Fabric. Safe to run anytime.

Credentials (reuses the bridge SP - set in web-app/backend/.env):
  FABRIC_BRIDGE_TENANT_ID / _CLIENT_ID / _CLIENT_SECRET
    (fallback: PBI_TENANT_ID / PBI_CLIENT_ID / PBI_CLIENT_SECRET)
  FABRIC_WORKSPACE_ID

Run:
  pip install -r requirements.txt
  python fabric_audit.py            # auto-loads web-app/backend/.env
"""
from __future__ import annotations

import base64
import datetime as dt
import glob
import json
import os
import pathlib
import sys

import msal
import requests

FABRIC_API = "https://api.fabric.microsoft.com/v1"
SCOPE = "https://api.fabric.microsoft.com/.default"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _env(*names: str) -> str | None:
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return None


def _load_env_file(path: pathlib.Path) -> None:
    """Minimal .env loader: KEY=VALUE lines; ignores #/blank; first '=' only,
    so secrets containing '=' survive. Does not override the real environment."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def get_token() -> str:
    tenant = _env("FABRIC_BRIDGE_TENANT_ID", "PBI_TENANT_ID")
    client = _env("FABRIC_BRIDGE_CLIENT_ID", "PBI_CLIENT_ID")
    secret = _env("FABRIC_BRIDGE_CLIENT_SECRET", "PBI_CLIENT_SECRET")
    if not all([tenant, client, secret]):
        sys.exit("Missing SP credentials (FABRIC_BRIDGE_* or PBI_*).")
    app = msal.ConfidentialClientApplication(
        client_id=client,
        client_credential=secret,
        authority=f"https://login.microsoftonline.com/{tenant}",
    )
    res = app.acquire_token_for_client(scopes=[SCOPE])
    if "access_token" not in res:
        sys.exit(f"Token request failed: {res.get('error_description') or res}")
    return res["access_token"]


def api_list(tok: str, path: str) -> list[dict]:
    """GET a list endpoint, following Fabric continuation paging."""
    url = f"{FABRIC_API}{path}"
    out: list[dict] = []
    while url:
        r = requests.get(url, headers={"Authorization": f"Bearer {tok}"}, timeout=60)
        if r.status_code in (401, 403):
            sys.exit(
                f"{r.status_code} on {path}. SP authenticated but not authorised. "
                "Check: (1) 'Service principals can call Fabric public APIs' ON, "
                "(2) SP added to the workspace as Admin/Member."
            )
        r.raise_for_status()
        j = r.json()
        out.extend(j.get("value", []))
        url = j.get("continuationUri")
    return out


def main() -> None:
    _load_env_file(REPO_ROOT / "web-app" / "backend" / ".env")
    _load_env_file(REPO_ROOT / ".env")

    ws = _env("FABRIC_WORKSPACE_ID")
    if not ws:
        sys.exit("Set FABRIC_WORKSPACE_ID (not found in env or .env).")
    tok = get_token()
    print(f"Workspace: {ws}\n")

    notebooks = api_list(tok, f"/workspaces/{ws}/notebooks")
    pipelines = api_list(tok, f"/workspaces/{ws}/dataPipelines")
    nb_by_name = {n["displayName"]: n["id"] for n in notebooks}
    pl_by_name = {p["displayName"]: p["id"] for p in pipelines}

    print(f"=== Live notebooks ({len(notebooks)}) ===")
    for name, gid in sorted(nb_by_name.items()):
        print(f"  {name}  ->  {gid}")
    print(f"\n=== Live data pipelines ({len(pipelines)}) ===")
    for name, gid in sorted(pl_by_name.items()):
        print(f"  {name}  ->  {gid}")

    print("\n=== DRIFT: repo pipeline notebook refs vs live workspace ===")
    missing: set[str] = set()
    for f in sorted(glob.glob(str(REPO_ROOT / "pipelines" / "batch" / "*.json"))):
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"  (skip {os.path.basename(f)}: {e})")
            continue
        acts = data.get("properties", {}).get("activities", [])
        refs = [
            a.get("typeProperties", {}).get("notebookId")
            for a in acts
            if a.get("type") == "TridentNotebook"
        ]
        refs = [x for x in refs if x]
        if not refs:
            continue
        print(f"\n  {os.path.basename(f)}")
        for ref in refs:
            ok = ref in nb_by_name
            if not ok:
                missing.add(ref)
            tag = "OK     " if ok else "MISSING"
            hint = "" if ok else "   <-- not a live notebook (rename / cleanup drift)"
            print(f"     {tag}  {ref}{hint}")
    if missing:
        print(f"\n  WARNING unresolved notebook refs: {sorted(missing)}")
        print("  -> these pipeline activities would fail to bind on a run.")
    else:
        print("\n  OK: every repo pipeline notebook ref resolves to a live notebook.")

    if pipelines:
        p0 = pipelines[0]
        print(f"\n=== Sample live pipeline definition: {p0['displayName']} ===")
        try:
            r = requests.post(
                f"{FABRIC_API}/workspaces/{ws}/dataPipelines/{p0['id']}/getDefinition",
                headers={"Authorization": f"Bearer {tok}"},
                timeout=60,
            )
            if r.status_code == 200:
                for prt in r.json().get("definition", {}).get("parts", []):
                    print(f"   part: {prt.get('path')}  ({prt.get('payloadType')})")
                    if prt.get("path", "").endswith(".json") and prt.get("payloadType") == "InlineBase64":
                        decoded = base64.b64decode(prt["payload"]).decode("utf-8", "replace")
                        print("   --- first 700 chars of decoded pipeline-content ---")
                        print("   " + decoded[:700].replace("\n", "\n   "))
            else:
                print(f"   getDefinition -> {r.status_code} (likely long-running); skip.")
        except requests.RequestException as e:
            print(f"   getDefinition error (non-fatal): {e}")

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    lines = [
        "# Fabric Sync Registry",
        "",
        f"_Auto-generated by scripts/fabric_deploy/fabric_audit.py - {ts}_",
        "",
        f"Workspace: {ws}",
        "",
        "## Notebooks",
        "",
        "| Name | GUID |",
        "|---|---|",
        *[f"| {n} | {g} |" for n, g in sorted(nb_by_name.items())],
        "",
        "## Data pipelines",
        "",
        "| Name | GUID |",
        "|---|---|",
        *[f"| {n} | {g} |" for n, g in sorted(pl_by_name.items())],
        "",
    ]
    (REPO_ROOT / "docs" / "fabric-sync.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nOK: registry written -> docs/fabric-sync.md")


if __name__ == "__main__":
    main()
