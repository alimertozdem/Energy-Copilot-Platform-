#!/usr/bin/env python3
"""
Fabric scripted deploy (Yol 2, step 2) - CONSOLIDATED pipeline.

Default = DRY-RUN: resolve repo stages -> live GUIDs (whitespace-tolerant; handles
drifted names via RENAME_MAP), assemble ONE consolidated pipeline (sequential =
F4-safe), print the plan, write pipeline-content.json locally. Writes NOTHING to Fabric.

  python fabric_deploy.py            # dry-run plan
  python fabric_deploy.py --apply    # create/update the pipeline (NO schedule)

--apply deploys as a NEW pipeline 'energy_copilot_clean' (the existing
'energy_copilot_master' is left untouched), WITHOUT a schedule. Validate it with a
manual run in Fabric, then add the 02:00 schedule in the UI.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys

import requests

from fabric_audit import FABRIC_API, REPO_ROOT, _env, _load_env_file, api_list, get_token

TARGET = "energy_copilot_clean"

# repo-canonical notebook name -> current LIVE displayName (drift from the audit).
RENAME_MAP = {
    "01_bronze_ingestion": "Bronz",                          # [TAHMIN]
    "10_crrem_pathway_loader": "10_crrem_pathway",
    "anomaly_detection": "07_Anomaly detection_engine",      # [TAHMIN]
    "09_ghg_scope_engine": "09_ghg_scope_engine.py",
    "11_hvac_analytics_engine": "11_hvac_analytics_engine.py",
    "07_consumption_forecast": "gold_consumption_forecast",  # [TAHMIN]
    "08_occupancy_prediction": "08_occupancy_prediction.",
}
TAHMIN = {"01_bronze_ingestion", "anomaly_detection", "07_consumption_forecast"}

# Consolidated DAG, linear (F4 trial = one at a time, avoids 430). soft=failure won't abort chain.
STAGES = [
    ("00_reference_data_loader", False),
    ("01_bronze_ingestion", False),
    ("02_openmeteo_weather_loader", True),
    ("03_entsoe_price_loader", True),
    ("05_electricitymaps_co2_loader", True),
    ("02_silver_transformation", False),
    ("08_occupancy_prediction", True),
    ("03_gold_kpi_engine", False),
    ("04_simulation_engine", False),
    ("09_ghg_scope_engine", False),
    ("10_crrem_pathway_loader", False),
    ("anomaly_detection", False),
    ("05_compliance_checker", False),
    ("06_recommendation_engine", False),
    ("11_hvac_analytics_engine", False),
    ("07_consumption_forecast", True),
]


def _hdr(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def build_plan(ws: str, by_name: dict) -> tuple[list, list, list]:
    activities, missing, tahmin_used = [], [], []
    prev_name, prev_soft = None, False
    for canon, soft in STAGES:
        live = RENAME_MAP.get(canon, canon).strip()
        gid = by_name.get(live)
        if canon in TAHMIN and gid is not None:
            tahmin_used.append(f"{canon} -> '{live}'")
        if gid is None:
            missing.append(f"{canon} (looked for '{live}')")
            print(f"  SKIP(missing)  {canon} -> '{live}'  {'soft' if soft else 'HARD'}")
            continue
        name = canon[:55]
        act = {
            "name": name,
            "type": "TridentNotebook",
            "dependsOn": [],
            "policy": {"timeout": "0.02:00:00", "retry": 2, "retryIntervalInSeconds": 120},
            "typeProperties": {"notebookId": gid, "workspaceId": ws},
        }
        if prev_name:
            cond = ["Succeeded", "Failed", "Skipped"] if prev_soft else ["Succeeded"]
            act["dependsOn"] = [{"activity": prev_name, "dependencyConditions": cond}]
        activities.append(act)
        print(f"  OK   {canon} -> {gid}{' [TAHMIN]' if canon in TAHMIN else ''}{'  (soft)' if soft else ''}")
        prev_name, prev_soft = name, soft
    return activities, missing, tahmin_used


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually create/update the pipeline")
    args = ap.parse_args()

    _load_env_file(REPO_ROOT / "web-app" / "backend" / ".env")
    _load_env_file(REPO_ROOT / ".env")
    ws = _env("FABRIC_WORKSPACE_ID")
    if not ws:
        sys.exit("Set FABRIC_WORKSPACE_ID.")
    tok = get_token()
    by_name = {n["displayName"].strip(): n["id"] for n in api_list(tok, f"/workspaces/{ws}/notebooks")}

    print("=== CONSOLIDATED PIPELINE PLAN ===\n")
    acts, missing, tahmin_used = build_plan(ws, by_name)
    content = {"properties": {"activities": acts}}
    (REPO_ROOT / "scripts" / "fabric_deploy" / "_plan_consolidated_pipeline.json").write_text(
        json.dumps(content, indent=2), encoding="utf-8"
    )
    print(f"\nResolved {len(acts)} stages | missing {len(missing)}")
    for m in missing:
        print(f"  MISSING: {m}  (soft-skipped; deploy later)")
    if tahmin_used:
        print("  CONFIRM these [TAHMIN] mappings before --apply:")
        for t in tahmin_used:
            print(f"    - {t}")

    if not args.apply:
        print("\nDRY-RUN. Nothing written to Fabric. Re-run with --apply after confirming [TAHMIN].")
        return

    pipes = {p["displayName"].strip(): p["id"] for p in api_list(tok, f"/workspaces/{ws}/dataPipelines")}
    part = {
        "path": "pipeline-content.json",
        "payload": base64.b64encode(json.dumps(content).encode()).decode(),
        "payloadType": "InlineBase64",
    }
    if TARGET in pipes:
        pid = pipes[TARGET]
        print(f"\nUpdating '{TARGET}' ({pid}) ...")
        r = requests.post(
            f"{FABRIC_API}/workspaces/{ws}/dataPipelines/{pid}/updateDefinition",
            headers=_hdr(tok), json={"definition": {"parts": [part]}}, timeout=120,
        )
    else:
        print(f"\nCreating '{TARGET}' ...")
        r = requests.post(
            f"{FABRIC_API}/workspaces/{ws}/dataPipelines",
            headers=_hdr(tok), json={"displayName": TARGET, "definition": {"parts": [part]}}, timeout=120,
        )
    if r.status_code in (200, 201):
        body = r.json() if r.text else {}
        print(f"OK ({r.status_code}). Pipeline id: {body.get('id', '(see portal)')}")
    elif r.status_code == 202:
        print(f"Accepted (202, long-running). Location: {r.headers.get('Location', '(portal)')}")
    else:
        print(f"FAILED ({r.status_code}): {r.text[:400]}")
        sys.exit(1)
    print("\nDeployed WITHOUT a schedule (safe). Run it once manually in Fabric to validate, "
          "then add the 02:00 schedule in the pipeline Schedule settings.")


if __name__ == "__main__":
    main()
