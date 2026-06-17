#!/usr/bin/env python3
"""
Trim dead measures from the semantic model (DirectLake) via updateDefinition.

DRY-RUN by default: reads semantic-model/dead_measures_2026-06-15.txt, removes those
measure blocks from the exported model TMDL, and reports per-table what WOULD change.
Writes nothing to Fabric. Use --apply to push the trimmed model.

  python fabric_model_trim.py            # dry-run
  python fabric_model_trim.py --apply    # push updateDefinition

Reversible: the original model is in semantic-model/_model_export/ (git). To restore,
re-run getDefinition (fabric_model_export.py) before, or re-apply the original parts.
Fabric validates the TMDL on updateDefinition, so a malformed payload is rejected (safe).
"""
from __future__ import annotations

import argparse
import base64
import re
import sys

import requests

from fabric_audit import FABRIC_API, REPO_ROOT, _env, _load_env_file, api_list, get_token

EXPORT = REPO_ROOT / "semantic-model" / "_model_export" / "EnergyCopilotModel"
DEADLIST = REPO_ROOT / "semantic-model" / "dead_measures_2026-06-15.txt"
MODEL_NAME = "EnergyCopilotModel"
_CHILD = re.compile(r"^\t(measure|column|partition|hierarchy|calculationGroup)\b")


def _hdr(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def load_deadset() -> set:
    out = set()
    for ln in DEADLIST.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            out.add(s)
    return out


def trim_table(text: str, dead: set) -> tuple[str, list]:
    lines = text.split("\n")
    out, removed, i, n = [], [], 0, len(lines)
    while i < n:
        ln = lines[i]
        m = re.match(r"^\tmeasure\s+('([^']*)'|([^\s=]+))", ln)
        if m:
            name = m.group(2) if m.group(2) is not None else m.group(3)
            j = i + 1
            while j < n:
                nxt = lines[j]
                if _CHILD.match(nxt):
                    break
                if nxt and not nxt.startswith("\t") and nxt.strip() != "":
                    break
                j += 1
            if name in dead:
                removed.append(name)
                i = j
                continue
            out.extend(lines[i:j])
            i = j
            continue
        out.append(ln)
        i += 1
    return "\n".join(out), removed


def build_parts(dead: set) -> tuple[list, dict]:
    parts, report = [], {}
    for f in sorted(EXPORT.rglob("*")):
        if f.is_dir():
            continue
        rel = str(f.relative_to(EXPORT)).replace("\\", "/")
        if rel == ".platform":
            continue
        data = f.read_bytes()
        if rel.startswith("definition/tables/") and rel.endswith(".tmdl"):
            new, removed = trim_table(data.decode("utf-8"), dead)
            if removed:
                report[rel.split("/")[-1]] = removed
                data = new.encode("utf-8")
        parts.append({"path": rel, "payload": base64.b64encode(data).decode(), "payloadType": "InlineBase64"})
    return parts, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not EXPORT.exists():
        sys.exit("Run fabric_model_export.py first (model TMDL not found).")
    dead = load_deadset()
    parts, report = build_parts(dead)

    total_removed = sum(len(v) for v in report.values())
    print(f"=== MODEL TRIM (dry-run{' OFF' if args.apply else ''}) ===")
    print(f"dead-list size: {len(dead)} | measures removed: {total_removed}\n")
    for tbl, ms in sorted(report.items()):
        print(f"  {tbl}: -{len(ms)}")
        for m in ms:
            print(f"       - {m}")
    not_found = dead - {m for ms in report.values() for m in ms}
    if not_found:
        print(f"\n  NOTE: {len(not_found)} list entries not found in any table (already gone / renamed):")
        for m in sorted(not_found):
            print(f"       ? {m}")

    if not args.apply:
        print("\nDRY-RUN. Nothing pushed. Review, then re-run with --apply.")
        return

    _load_env_file(REPO_ROOT / "web-app" / "backend" / ".env")
    _load_env_file(REPO_ROOT / ".env")
    ws = _env("FABRIC_WORKSPACE_ID")
    tok = get_token()
    models = {m["displayName"]: m["id"] for m in api_list(tok, f"/workspaces/{ws}/semanticModels")}
    mid = models.get(MODEL_NAME)
    if not mid:
        sys.exit(f"Model '{MODEL_NAME}' not found.")
    print(f"\nPushing updateDefinition to '{MODEL_NAME}' ({mid}) ...")
    r = requests.post(
        f"{FABRIC_API}/workspaces/{ws}/semanticModels/{mid}/updateDefinition",
        headers=_hdr(tok), json={"definition": {"parts": parts}}, timeout=180,
    )
    if r.status_code in (200, 201):
        print("OK — model updated. Refresh Power BI to see the trimmed measure list.")
    elif r.status_code == 202:
        print(f"Accepted (202, long-running): {r.headers.get('Location','(portal)')}")
    else:
        print(f"FAILED ({r.status_code}): {r.text[:500]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
