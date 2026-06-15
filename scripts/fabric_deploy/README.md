# Fabric scripted deploy (Yol 2)

Repo → Fabric synchronization via the Fabric REST API + a service principal — the
free, trial-compatible alternative to native Git integration (which needs paid F2+).

Reuses the **same service principal the bridge already uses** (`PBI_*` or
`FABRIC_BRIDGE_*` in `web-app/backend/.env`). No new credentials required if that
SP is a workspace Admin/Member and the tenant setting *"Service principals can call
Fabric public APIs"* is ON (it is).

## Prerequisites (one-time)

1. Service principal exists and is a **workspace Admin/Member** (the bridge SP qualifies).
2. Tenant setting **"Service principals can call Fabric public APIs" = Enabled** (done).
3. `web-app/backend/.env` has: `FABRIC_WORKSPACE_ID` + (`FABRIC_BRIDGE_*` or `PBI_*`)
   tenant/client/secret.

## Step 1 — Audit (READ-ONLY, run this first)

`fabric_audit.py` changes nothing. It:
- proves the SP can reach the workspace,
- lists live notebooks + data pipelines with their GUIDs,
- cross-checks the repo's `pipelines/batch/*.json` notebook refs against the live
  workspace → **drift report** (catches renamed/removed notebooks after the cleanup),
- fetches one live pipeline definition (so we learn the exact format for step 2),
- writes the `notebook ↔ GUID` registry to `docs/fabric-sync.md`.

```powershell
cd scripts\fabric_deploy
pip install -r requirements.txt

# load the bridge SP creds + workspace id from the backend .env into this shell:
Get-Content ..\..\web-app\backend\.env | Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } | ForEach-Object {
  $kv = $_ -split '=', 2
  Set-Item -Path "Env:$($kv[0].Trim())" -Value ($kv[1].Trim().Trim('"'))
}

python fabric_audit.py
```

Send the console output back — it tells us the live state, the drift, and the
pipeline definition format.

## Step 2 — Deploy (WRITE) — built after the audit

`fabric_deploy.py` (next) will, from a manifest:
- apply the runbook fixes to the batch pipeline JSONs (naming + external loaders),
- resolve each `notebookId` name → live GUID,
- create-or-update each data pipeline item in the workspace,
- refresh `docs/fabric-sync.md`.

Notebook **content** sync (plain `.py` → Fabric notebook format) is a later step,
folded into the item-3 parameterization (one notebook per step with an optional
`BUILDING_ID`).
