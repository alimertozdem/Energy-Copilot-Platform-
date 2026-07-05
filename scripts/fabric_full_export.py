#!/usr/bin/env python3
"""
Fabric FULL EXPORT - rescue script before trial capacity expiry.

Exports ALL item definitions the signed-in user can reach via Fabric REST API:
  - Notebooks (.ipynb)
  - Semantic models (TMDL parts - includes ALL measures, roles, partitions)
  - Reports (PBIR parts - layout + report-level measures)
  - Data pipelines, Spark job definitions, Eventstreams, KQL items, etc.
Optionally (--data) downloads Lakehouse Tables/ and Files/ raw content via OneLake DFS API.

Usage (local machine, needs your browser login):
  pip install msal requests
  python fabric_full_export.py
  python fabric_full_export.py --data

Output: ./fabric_backup_<UTC timestamp>/<workspace>/<ItemType>_<ItemName>/...
Every error is PRINTED (no silent except) and the script continues to the next item.
"""
import argparse
import base64
import datetime
import json
import os
import re
import sys
import time

import requests
import msal

CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"  # well-known Azure CLI public client id
AUTHORITY = "https://login.microsoftonline.com/organizations"
FABRIC_SCOPE = ["https://api.fabric.microsoft.com/.default"]
STORAGE_SCOPE = ["https://storage.azure.com/.default"]
API = "https://api.fabric.microsoft.com/v1"
ONELAKE = "https://onelake.dfs.fabric.microsoft.com"

_app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)


def get_token(scopes):
    for acct in _app.get_accounts():
        r = _app.acquire_token_silent(scopes, account=acct)
        if r and "access_token" in r:
            return r["access_token"]
    flow = _app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        raise RuntimeError("Device flow failed: %s" % json.dumps(flow))
    print("\n>>> " + flow["message"] + "\n", flush=True)
    r = _app.acquire_token_by_device_flow(flow)
    if "access_token" not in r:
        raise RuntimeError("Auth failed: %s" % r.get("error_description"))
    return r["access_token"]


def req(method, url, token, **kw):
    """Request with 429/throttle retry. Raises on other errors."""
    for attempt in range(6):
        resp = requests.request(method, url, headers={"Authorization": "Bearer " + token}, timeout=120, **kw)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "10"))
            print("  throttled, waiting %ss" % wait, flush=True)
            time.sleep(wait)
            continue
        return resp
    return resp


def lro_result(resp, token):
    """Follow Fabric long-running operation until result JSON is available."""
    while resp.status_code == 202:
        loc = resp.headers.get("Location")
        time.sleep(int(resp.headers.get("Retry-After", "3")))
        resp = req("GET", loc, token)
        if resp.status_code == 200:
            body = resp.json()
            if body.get("status") in ("Succeeded",):
                r2 = req("GET", loc + "/result", token)
                r2.raise_for_status()
                return r2.json()
            if body.get("status") in ("Failed", "Cancelled"):
                raise RuntimeError("LRO failed: %s" % json.dumps(body)[:500])
            resp.status_code = 202  # keep polling
    resp.raise_for_status()
    return resp.json()


def safe(name):
    return re.sub(r'[^A-Za-z0-9._ -]+', '_', name).strip() or "unnamed"


def write_parts(definition, dest):
    for part in definition.get("definition", {}).get("parts", []):
        path = os.path.join(dest, *part["path"].split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(base64.b64decode(part["payload"]))


def export_definitions(token, outdir):
    ws_list = req("GET", API + "/workspaces", token).json()["value"]
    print("Workspaces: %d" % len(ws_list), flush=True)
    for ws in ws_list:
        wdir = os.path.join(outdir, safe(ws["displayName"]))
        os.makedirs(wdir, exist_ok=True)
        items = req("GET", API + "/workspaces/%s/items" % ws["id"], token).json()["value"]
        with open(os.path.join(wdir, "_item_inventory.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        print("\n[%s] %d items" % (ws["displayName"], len(items)), flush=True)
        for it in items:
            label = "%s_%s" % (it["type"], safe(it["displayName"]))
            fmt = "?format=ipynb" if it["type"] == "Notebook" else ""
            url = API + "/workspaces/%s/items/%s/getDefinition%s" % (ws["id"], it["id"], fmt)
            try:
                resp = req("POST", url, token)
                if resp.status_code in (400, 403, 404):
                    print("  SKIP %-55s (no definition export: HTTP %d)" % (label, resp.status_code), flush=True)
                    continue
                definition = lro_result(resp, token)
                write_parts(definition, os.path.join(wdir, label))
                print("  OK   %s" % label, flush=True)
            except Exception as e:
                print("  FAIL %-55s %s" % (label, repr(e)[:300]), flush=True)


def onelake_walk(token, ws_id, item_prefix):
    url = "%s/%s?resource=filesystem&recursive=true&directory=%s" % (ONELAKE, ws_id, item_prefix)
    cont, paths = None, []
    while True:
        u = url + (("&continuation=" + requests.utils.quote(cont)) if cont else "")
        resp = req("GET", u, token)
        if resp.status_code != 200:
            print("  LIST FAIL %s HTTP %d %s" % (item_prefix, resp.status_code, resp.text[:200]), flush=True)
            return paths
        paths += resp.json().get("paths", [])
        cont = resp.headers.get("x-ms-continuation")
        if not cont:
            return paths


def export_data(token, outdir):
    fabric_tok = get_token(FABRIC_SCOPE)
    ws_list = req("GET", API + "/workspaces", fabric_tok).json()["value"]
    for ws in ws_list:
        items = req("GET", API + "/workspaces/%s/items" % ws["id"], fabric_tok).json()["value"]
        for it in [i for i in items if i["type"] == "Lakehouse"]:
            print("\n[data] %s / %s" % (ws["displayName"], it["displayName"]), flush=True)
            for area in ("Tables", "Files"):
                prefix = "%s/%s" % (it["id"], area)
                for p in onelake_walk(token, ws["id"], prefix):
                    if p.get("isDirectory") == "true":
                        continue
                    rel = p["name"]
                    dest = os.path.join(outdir, "_onelake", safe(ws["displayName"]), safe(it["displayName"]), *rel.split("/")[1:])
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    resp = req("GET", "%s/%s/%s" % (ONELAKE, ws["id"], rel), token)
                    if resp.status_code == 200:
                        with open(dest, "wb") as f:
                            f.write(resp.content)
                    else:
                        print("  DL FAIL %s HTTP %d" % (rel, resp.status_code), flush=True)
                print("  %s/%s done" % (it["displayName"], area), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", action="store_true", help="also download Lakehouse Tables/Files via OneLake")
    args = ap.parse_args()
    outdir = "fabric_backup_" + datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    os.makedirs(outdir, exist_ok=True)
    print("Output: %s" % os.path.abspath(outdir), flush=True)
    token = get_token(FABRIC_SCOPE)
    export_definitions(token, outdir)
    if args.data:
        storage_tok = get_token(STORAGE_SCOPE)
        export_data(storage_tok, outdir)
    print("\nDONE. Verify folder sizes, then commit definitions to git (NOT the _onelake data).", flush=True)


if __name__ == "__main__":
    main()
