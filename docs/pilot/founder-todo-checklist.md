# EnergyLens — Founder To-Do Checklist (2026-06-11)

_Everything that needs **you** (the parts the copilot's sandbox can't reach: your Fabric, Power BI,
Stripe, DB, and your domain approval). I've done all the sandbox-side work. Ordered by priority;
each item has a **how-to**. When you've done P1–P2 and decided P3–P4, tell me and **we verify
together** at the end._

---

## 🔴 P1 — Pilot go-live (the real critical path)
_These two runbooks turn "code-complete" into "a pilot can actually run." Do them in order._

- ☐ **1. Run CP-1 — Report go-live.** Open `docs/pilot/cp1-report-go-live-runbook.md`, follow
  Phases 0→6 (re-run notebook `03` → Tabular Editor install → time-grain → verify Pages 1–6).
  _~1–2h. Outcome: Pages 1–6 render with correct, sanity-checked numbers._
- ☐ **2. Run CP-2 — Pilot bridge + RLS isolation** (after CP-1). Open
  `docs/pilot/cp2-pilot-bridge-rls-runbook.md`. Bridge one real building, then the **2-customer
  isolation test**. _~1–2h. This is the go/no-go gate: a building goes live + **zero** cross-customer
  leakage._

## 🟠 P2 — Make the deployed app current
- ☐ **3. Apply DB migrations.** In `web-app/backend` with your prod DB env: run **`alembic upgrade
  head`**. _Why:_ the repo has migrations that must hit your Postgres (bridge_requests,
  pilot_requests, devices_sensor_points, alert_status, partner/residential, org_invitations,
  billing). _Verify:_ `alembic current` == `alembic heads`.
- ☐ **4. Merge/deploy latest.** The new `.github/workflows/backend-ci.yml` + doc updates are
  additive — just pull/merge to `main`. CI then runs the Tier-1 energy-logic tests on every push.

## 🟡 P3 — Go-to-market (materials ready — finalise + send)
- ☐ **5. Confirm pricing + set in Stripe.** Tiers already exist on `/pricing`: **Free €0 · Basic
  €99/mo · Monitor €299/mo · Enterprise custom · Residential €49/building + €3/unit**. Decide if
  final, then set the authoritative amounts in Stripe — follow `web-app/BILLING_SETUP.md`. _(Until
  you do, the page amounts are display placeholders.)_
- ☐ **6. Send the C4 outreach.** `docs/c4-outreach/01_intro_email.md` is ready — fill **[Professor
  name]** + **[phone]**, attach `docs/c4-outreach/EnergyLens_C4_onepager.pdf` + a demo link, send
  (ideally right after the professor's intro). _C4 = real prospect (embodied-carbon firm via BSBI)._

## 🟢 P4 — Residential (planned + scaffolded — your approval gates it)
- ☐ **7. Approve residential saving ranges.** Per CLAUDE.md, the indicative ranges in
  `docs/strategy/2026-06_growth_strategy.md` §4.3 (e.g. operational measures ~10–20% heating) need
  your **energy-domain sign-off** before we show a customer. Approve as-is, edit, or let's review
  together.
- ☐ **8. Confirm residential buyer + geography.** Recommended: professional portfolio
  (*Hausverwaltung*) + **Germany first**. Confirm or redirect (changes UX + sales motion).

## ⚪ P5 — Optional polish (low priority — say the word and I'll do the code ones)
- ☐ 9. Refresh `ref_` grid/tariff factors when 2026 values publish (carry-forward works meanwhile).
- ☐ 10. Remove `03` §8 legacy anomaly compute (saves Fabric compute — **I can prep the edit**).
- ☐ 11. Page 9 payback/IRR sanity (battery-only — investigate `battery_simulator.py` when a battery
  pilot is in scope).
- ☐ 12. Frontend TS CSV-parser unit test (the backend engines are already tested + in CI).

## ⏸ No action now
- **Capacity:** stay **④ static-snapshot (€0)**; activate **① Decouple** only at the first paying
  IoT customer (`docs/architecture/iot-capacity-decision.md`).
- **Execution Marketplace** (recommendation → installer): future phase, captured in the growth
  strategy addendum.

---

### How we close
Do **P1 + P2**, decide **P3 + P4**, then ping me — I'll verify together with you: spot-check the
report numbers, confirm RLS isolation, and review the deploy. The P5 items are genuinely optional.
