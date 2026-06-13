"""FabricBridgeOrchestrator — automated self-serve bridging (Layer 3, Phase 3.2).

Turns a *pending* building (Postgres-only baseline) into a *bridged* one (live in
Fabric) without the founder running notebooks by hand. Driven from the /admin
bridge queue as an **armed one-click** action: the backend performs every step,
the founder presses Go.

Five steps (see docs/architecture/self-serve-fabric-bridging.md §2):
  1. provision id        — mint the next free fabric_building_id (or use override)
  2. land bronze         — write the building's consumption CSV to OneLake
  3. run job             — trigger the parameterised bridge notebook + poll
  4. refresh model + RLS — best-effort semantic-model framing (DirectLake auto-
                           reflects gold; RLS for a real customer org is a
                           documented follow-up — see _refresh_semantic_model)
  5. write-back          — set buildings.fabric_building_id, mark request fulfilled

Three operating modes:
  * automation OFF  (BRIDGE_AUTOMATION_ENABLED falsey) -> raises BridgeDisabled so
    the endpoint cleanly falls back to the manual Phase-3.1 "Fulfil & go live".
  * dry-run         -> executes steps 1-2 planning WITHOUT calling Fabric/OneLake,
    returns the plan + parameters. €0, no capacity needed. For verification.
  * live            -> full run. Needs an active Fabric capacity (§6 of setup doc).

Every step appends to a `steps` result list and writes an audit event, so a
partial failure is fully traceable in /admin. The orchestrator never raises past
the caller for an *operational* failure (capacity down, job failed); it returns
ok=False with the failing step. It only raises BridgeDisabled / ValueError for
*programmer/config* errors.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Building
from app.repositories import admin as admin_repo
from app.repositories import audit as audit_repo
from app.repositories import bridge as bridge_repo
from app.repositories import consumption as consumption_repo

logger = logging.getLogger(__name__)


class BridgeDisabled(RuntimeError):
    """Automation is turned off — caller should fall back to manual fulfilment."""


def automation_enabled() -> bool:
    return os.getenv("BRIDGE_AUTOMATION_ENABLED", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


# Report notebooks chained AFTER the baseline, each scoped to the bridged building
# via the notebook's BRIDGE_BUILDING_ID parameter. (env var holding the Fabric
# notebook id, step name, human label). Best-effort: a failure here is recorded as
# a warning and the bridge still goes live with the baseline + whatever succeeded —
# the building's Data Score / readiness map then shows which reports are available.
# A notebook whose env id is unset is cleanly skipped (lets Mert wire ids over time).
_REPORT_CHAIN = [
    ("FABRIC_GHG_NOTEBOOK_ID", "run_ghg", "GHG inventory (09)"),
    ("FABRIC_COMPLIANCE_NOTEBOOK_ID", "run_compliance", "GEG / compliance (05)"),
    ("FABRIC_RECOMMENDATION_NOTEBOOK_ID", "run_recommendations", "recommendations (06)"),
]


def next_free_fabric_id(db: Session) -> str:
    """Mint the next free `B0NN` id by scanning existing assignments.

    Demo buildings occupy B001-B010; customer bridges continue from the max+1.
    Falls back to B011 when none match the pattern.
    """
    rows = db.scalars(
        select(Building.fabric_building_id).where(
            Building.fabric_building_id.is_not(None)
        )
    ).all()
    max_n = 0
    for fid in rows:
        m = re.fullmatch(r"B(\d{3,})", (fid or "").strip())
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"B{max(max_n + 1, 11):03d}"


def _building_meta(b: Building) -> dict:
    """Assemble the JSON the notebook needs to populate the dimension + KPIs."""
    return {
        "name": b.name,
        "country_code": (b.country_code or "EU"),
        "area_m2": float(b.floor_area_m2) if b.floor_area_m2 is not None else 0.0,
        "building_type": b.building_type or "office",
        "pv_capacity_kwp": float(b.pv_capacity_kwp) if b.pv_capacity_kwp is not None else 0.0,
        "has_heat_pump": (b.heating_system or "").lower() in {"heat_pump", "heatpump"},
        "epc_class": b.epc_class,
        "wall_u_value": float(b.wall_u_value) if b.wall_u_value is not None else None,
        "roof_u_value": float(b.roof_u_value) if b.roof_u_value is not None else None,
        "window_u_value": float(b.window_u_value) if b.window_u_value is not None else None,
        "insulation_year": b.insulation_year,
        "has_gas_heating": b.has_gas_heating,
        "construction_year": b.construction_year,
        "city": b.city,
    }


def _consumption_rows(db: Session, building_id: UUID) -> list[dict]:
    """Building's monthly rows shaped for the OneLake CSV writer."""
    rows = consumption_repo.list_rows(db, building_id=building_id)
    return [
        {
            "period_month": r.period,
            "kwh": float(r.energy_kwh),
            "cost_eur": float(r.cost_eur) if r.cost_eur is not None else None,
        }
        for r in rows
    ]


def _audit(db, *, admin_id, org_id, building_id, action, details, ip, ua):
    audit_repo.record_event(
        db,
        user_id=admin_id,
        organization_id=org_id,
        action=action,
        entity_type="building",
        entity_id=str(building_id),
        details=details,
        ip_address=ip,
        user_agent=ua,
    )


def run_automated_bridge(
    db: Session,
    *,
    request_id: UUID,
    admin_id: UUID,
    fabric_building_id_override: str | None = None,
    dry_run: bool = False,
    ip: str | None = None,
    ua: str | None = None,
) -> dict:
    """Execute (or simulate) the automated bridge for a bridge request.

    Returns a structured result: {ok, dry_run, fabric_building_id, steps:[...],
    error?}. Commits Postgres changes on success (and audit rows along the way).
    Raises BridgeDisabled when automation is off; ValueError for bad inputs.
    """
    if not automation_enabled() and not dry_run:
        raise BridgeDisabled(
            "BRIDGE_AUTOMATION_ENABLED is off — use manual 'Fulfil & go live'."
        )

    req = bridge_repo.get_by_id(db, request_id=request_id)
    if req is None:
        raise ValueError("Bridge request not found")
    building = admin_repo.get_building_by_id(db, req.building_id)
    if building is None:
        raise ValueError("Building not found")

    steps: list[dict] = []

    def step(name: str, status: str, **info):
        entry = {"step": name, "status": status, **info}
        steps.append(entry)
        return entry

    def fail(name: str, message: str) -> dict:
        step(name, "failed", message=message)
        _audit(
            db, admin_id=admin_id, org_id=req.organization_id,
            building_id=req.building_id, action="admin.bridge.automation_failed",
            details={"request_id": str(req.id), "step": name, "error": message[:500]},
            ip=ip, ua=ua,
        )
        db.commit()
        logger.warning("Automated bridge failed at %s: %s", name, message)
        return {"ok": False, "dry_run": dry_run, "error": message,
                "failed_step": name, "steps": steps}

    # --- Step 1: provision id ------------------------------------------------
    if building.fabric_building_id:
        return fail("provision_id",
                    f"Building already bridged as {building.fabric_building_id}")
    fabric_id = (fabric_building_id_override or "").strip() or next_free_fabric_id(db)
    if admin_repo.fabric_id_in_use(
        db, fabric_building_id=fabric_id, exclude_building_id=req.building_id
    ):
        return fail("provision_id", f"fabric_building_id '{fabric_id}' already in use")
    step("provision_id", "ok", fabric_building_id=fabric_id)

    # --- Step 2: assemble + land bronze -------------------------------------
    rows = _consumption_rows(db, req.building_id)
    meta = _building_meta(building)
    if not rows:
        return fail("land_bronze", "No uploaded consumption to bridge.")

    notebook_params = {
        "building_uuid": str(req.building_id),
        "fabric_building_id": fabric_id,
        "building_meta_json": json.dumps(meta),
    }

    if dry_run:
        step("land_bronze", "skipped (dry-run)", rows=len(rows))
        step("run_job", "skipped (dry-run)", params=notebook_params)
        for _env, _name, _label in _REPORT_CHAIN:
            step(_name,
                 "planned (dry-run)" if os.getenv(_env) else "skipped (id not configured)",
                 label=_label, params={"BRIDGE_BUILDING_ID": fabric_id})
        step("refresh_model", "skipped (dry-run)")
        step("write_back", "skipped (dry-run)")
        _audit(
            db, admin_id=admin_id, org_id=req.organization_id,
            building_id=req.building_id, action="admin.bridge.automation_dryrun",
            details={"request_id": str(req.id), "fabric_building_id": fabric_id,
                     "months": len(rows)},
            ip=ip, ua=ua,
        )
        db.commit()
        return {"ok": True, "dry_run": True, "fabric_building_id": fabric_id,
                "steps": steps, "plan": {"rows": len(rows), "params": notebook_params}}

    # Live path — imports here so dry-run never requires httpx/SP config.
    from app.integrations import onelake, fabric_jobs

    try:
        bronze_path = onelake.write_bronze_csv(str(req.building_id), rows)
    except onelake.OneLakeError as e:
        return fail("land_bronze", str(e))
    step("land_bronze", "ok", rows=len(rows), bronze_path=bronze_path)

    # --- Step 3: run the parameterised notebook job -------------------------
    try:
        location = fabric_jobs.trigger_bridge_notebook(
            {**notebook_params, "bronze_path": bronze_path}
        )
        final = fabric_jobs.poll_until_done(location)
    except fabric_jobs.FabricJobError as e:
        return fail("run_job", str(e))
    step("run_job", "ok", status=final.get("status"))

    # --- Step 3b: report chain (best-effort, scoped to this building) --------
    # The baseline above is REQUIRED (a failure already returned). These add the
    # GHG / compliance / recommendation gold rows for the new building. A failure
    # is a warning, not a hard stop: the building still goes live and the missing
    # report simply shows as "needs data / unavailable" in the readiness map.
    for _env, _name, _label in _REPORT_CHAIN:
        nb_id = os.getenv(_env)
        if not nb_id:
            step(_name, "skipped", label=_label, message=f"{_env} not configured")
            continue
        try:
            loc = fabric_jobs.trigger_notebook(nb_id, {"BRIDGE_BUILDING_ID": fabric_id})
            rep = fabric_jobs.poll_until_done(loc)
            step(_name, "ok", label=_label, status=rep.get("status"))
        except fabric_jobs.FabricJobError as e:
            step(_name, "warning", label=_label, message=str(e)[:300])
            logger.warning("Report step %s failed (continuing): %s", _name, e)

    # --- Step 4: refresh semantic model (best-effort) -----------------------
    try:
        _refresh_semantic_model()
        step("refresh_model", "ok")
    except Exception as e:  # best-effort: DirectLake reflects gold without it
        step("refresh_model", "warning", message=str(e)[:300])

    # --- Step 5: write back to Postgres -------------------------------------
    building.fabric_building_id = fabric_id
    req.status = "fulfilled"
    req.resolved_by = admin_id
    req.resolved_at = datetime.now(timezone.utc)
    req.resolution_note = (req.resolution_note or "") + " [auto-bridged]"
    _audit(
        db, admin_id=admin_id, org_id=req.organization_id,
        building_id=req.building_id, action="admin.bridge.automated",
        details={"request_id": str(req.id), "fabric_building_id": fabric_id,
                 "months": len(rows), "job_status": final.get("status")},
        ip=ip, ua=ua,
    )
    step("write_back", "ok", fabric_building_id=fabric_id)
    db.commit()
    logger.info("Automated bridge complete: %s -> %s", req.building_id, fabric_id)
    return {"ok": True, "dry_run": False, "fabric_building_id": fabric_id,
            "steps": steps}


def _refresh_semantic_model() -> None:
    """Force a DirectLake reframe so new gold rows surface immediately.

    DirectLake reads the gold Delta tables directly, so a bridged building's rows
    appear on the next query even without a refresh — this just warms framing.
    RLS for a real customer org (mapping the org's users to their buildings) is a
    documented follow-up, not done here: the demo role filters via a DAX rule on
    silver_building_master, which the bridged dimension row already satisfies.
    """
    import httpx

    from app.integrations.pbi_embed import acquire_service_principal_token

    workspace = os.getenv("PBI_WORKSPACE_ID")
    report_id = os.getenv("PBI_REPORT_ID")
    if not workspace or not report_id:
        raise RuntimeError("PBI_WORKSPACE_ID / PBI_REPORT_ID not set")

    token = acquire_service_principal_token()
    headers = {"Authorization": f"Bearer {token}"}
    base = "https://api.powerbi.com/v1.0/myorg"
    with httpx.Client(timeout=30) as client:
        meta = client.get(
            f"{base}/groups/{workspace}/reports/{report_id}", headers=headers
        )
        meta.raise_for_status()
        dataset_id = meta.json()["datasetId"]
        r = client.post(
            f"{base}/groups/{workspace}/datasets/{dataset_id}/refreshes",
            headers=headers,
            json={"type": "automatic"},
        )
        if r.status_code not in (200, 202):
            raise RuntimeError(f"refresh {r.status_code}: {r.text[:200]}")
