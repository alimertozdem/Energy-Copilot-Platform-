# Billing setup (Stripe)

EnergyLens uses **Stripe Checkout + Customer Portal + webhooks** for self-serve
subscriptions. The app code is complete; this is the one-time operator setup
(test mode). Plans: `free` (default) · `basic` + `monitor` (self-serve) ·
`enterprise` (contact sales). Prices live in Stripe — never hardcoded.

## 1. Stripe account + products (test mode)

1. Create a Stripe account and stay in **Test mode** (toggle, top-right).
2. **Products → Add product** twice:
   - **Basic** — add a **recurring / monthly** price → copy its `price_…` id.
   - **Monitor** — add a **recurring / monthly** price → copy its `price_…` id.
   (Amounts are up to you; e.g. Basic €99/mo, Monitor €299/mo.)
3. **Developers → API keys** → copy the **Secret key** (`sk_test_…`).
4. **Customer Portal**: Settings → Billing → **Customer portal** → activate it in
   test mode (one-time), otherwise `/billing/portal` will error.

## 2. Backend `.env` (web-app/backend/.env)

```
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx          # see step 4 (local = from `stripe listen`)
STRIPE_PRICE_BASIC=price_xxx
STRIPE_PRICE_MONITOR=price_xxx
BILLING_SUCCESS_URL=http://localhost:3000/settings?billing=success
BILLING_CANCEL_URL=http://localhost:3000/settings?billing=cancel
BILLING_PORTAL_RETURN_URL=http://localhost:3000/settings
```

`uvicorn --reload` does NOT reload `.env` — restart uvicorn after editing it.

## 3. Install dep + run migration

```powershell
cd web-app/backend
.\venv\Scripts\Activate.ps1
pip install stripe            # already added to requirements.txt
alembic upgrade head          # adds stripe_customer_id / stripe_subscription_id / current_period_end
```

## 4. Local webhook (Stripe CLI)

Stripe must reach the backend webhook. For local dev, use the Stripe CLI:

```powershell
stripe login
stripe listen --forward-to 127.0.0.1:8000/billing/webhook
```

`stripe listen` prints a **webhook signing secret** (`whsec_…`) — put THAT in
`STRIPE_WEBHOOK_SECRET` for local testing (it differs from a dashboard webhook
secret). Keep `stripe listen` running while you test.

For a deployed environment instead: Developers → Webhooks → add an endpoint
`https://<host>/billing/webhook` listening to `checkout.session.completed`,
`customer.subscription.created|updated|deleted`; use that endpoint's `whsec_…`.

## 5. Test the flow

1. Both servers running (`uvicorn` + `npm run dev`) and `stripe listen` open.
2. Log in as an **org admin**, go to **/settings → Subscription**.
3. Click **Upgrade to Basic/Monitor** → redirected to Stripe Checkout.
4. Pay with the test card **4242 4242 4242 4242**, any future expiry, any CVC, any ZIP.
5. Stripe fires `checkout.session.completed` → `stripe listen` forwards it →
   backend syncs `organizations.subscription_tier/status/current_period_end`.
6. Back on /settings the card shows the new plan; **Manage billing** opens the
   Customer Portal (change/cancel) — cancellations sync back to `free` via the
   `customer.subscription.deleted` event.

## Notes

- The webhook endpoint is unauthenticated but **signature-verified** against
  `STRIPE_WEBHOOK_SECRET` — only Stripe can drive tier changes.
- Checkout/Portal endpoints are **org-admin only** (`POST /billing/checkout`,
  `/billing/portal`). Non-admins see a read-only plan card.
- If `STRIPE_SECRET_KEY` is unset, billing endpoints return `503` and the
  Subscription card surfaces a calm error — the rest of the app is unaffected.
- `enterprise` is not self-serve: the card shows a "Contact sales" mailto.
