"""Phase 2 bridge — LIVE run (no /admin). Actually bridges ONE pending building
into Fabric: writes its consumption to OneLake, runs the 40 notebook on your
capacity, writes gold_kpi + the dimension row, and flips the building live.

REQUIRES (web-app/backend/.env): FABRIC_WORKSPACE_ID, FABRIC_LAKEHOUSE_ID,
FABRIC_BRIDGE_NOTEBOOK_ID, FABRIC_ONELAKE_HOST, BRIDGE_AUTOMATION_ENABLED=true,
plus the PBI_* service-principal creds — and an ACTIVE Fabric capacity. The report
notebooks (09/05/06) are skipped unless their FABRIC_*_NOTEBOOK_ID is set.

Run from web-app/backend with the venv active (RESTART the backend first if you
just edited .env so it re-reads the new vars):
    python test_bridge_live.py
It finds the pending building, shows the plan, and asks you to type 'yes'.
This USES Fabric compute (free on a trial) and PERMANENTLY bridges the building
(writes fabric_building_id back to Postgres).
"""
import sys

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Building, User
from app.repositories import bridge as bridge_repo
from app.repositories import consumption as consumption_repo
from app.services import bridge_orchestrator


def _count(db, building_id) -> int:
    try:
        return len(consumption_repo.list_rows(db, building_id=building_id))
    except Exception:
        return 0


def main() -> None:
    if not bridge_orchestrator.automation_enabled():
        sys.exit(
            "BRIDGE_AUTOMATION_ENABLED is not 'true' in .env — set it (plus the FABRIC_* "
            "vars), RESTART the backend, then re-run. (Live needs the flag; dry-run didn't.)"
        )

    db = SessionLocal()
    try:
        pending = list(
            db.scalars(select(Building).where(Building.fabric_building_id.is_(None))).all()
        )
        target = next((b for b in pending if _count(db, b.id) > 0), None)
        if target is None:
            print("No pending building with consumption to bridge. Add one (onboarding + CSV).")
            return

        req = bridge_repo.get_active_request(db, building_id=target.id)
        if req is None:
            req = bridge_repo.create_request(
                db, building_id=target.id, organization_id=target.organization_id,
                requested_by=None, target_tier="basic", readiness=None,
                note="live test harness",
            )
            db.commit()
        admin = db.scalar(select(User).where(User.is_platform_admin.is_(True))) or db.scalar(
            select(User)
        )
        if admin is None:
            print("No users in DB — aborting.")
            return

        print(f"About to LIVE-bridge:  {target.name}  (id={target.id})")
        print(f"  consumption_months = {_count(db, target.id)}")
        print("  -> writes the consumption to OneLake, runs notebook 40 on your Fabric")
        print("     capacity, writes gold_kpi + the dim row, flips the building live.")
        if input("\nType 'yes' to run LIVE: ").strip().lower() != "yes":
            print("Aborted.")
            return

        print("\nRunning... (notebook spin-up + run can take ~1-3 min, please wait)")
        try:
            result = bridge_orchestrator.run_automated_bridge(
                db, request_id=req.id, admin_id=admin.id, dry_run=False
            )
        except bridge_orchestrator.BridgeDisabled as e:
            sys.exit(str(e))

        print(f"\nok={result['ok']}  fabric_building_id={result.get('fabric_building_id')}")
        if result.get("error"):
            print(f"error: {result['error']}  (failed_step={result.get('failed_step')})")
        print("\nSteps:")
        for s in result.get("steps", []):
            extra = {k: v for k, v in s.items() if k not in ("step", "status")}
            print(f"  [{s.get('status',''):<22}] {s.get('step',''):<20} {extra or ''}")

        if result["ok"]:
            fid = result.get("fabric_building_id")
            print(f"\n✅ Bridged. The building is now live as {fid}.")
            print("   Open it in the app — its KPIs/dashboard should populate from Fabric.")
            print("   (GHG/GEG/recommendations stay empty until you set FABRIC_*_NOTEBOOK_ID.)")
        else:
            print("\n⚠️  Bridge did not complete — see the failed step above. The building was")
            print("   NOT flipped live. Common causes: SP missing workspace Contributor, the")
            print("   tenant 'Service principals can use Fabric APIs' setting off, no active")
            print("   capacity, or a wrong GUID in .env. Fix and re-run — it's idempotent.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
