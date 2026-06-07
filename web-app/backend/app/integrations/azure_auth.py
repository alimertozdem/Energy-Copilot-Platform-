"""Azure AD service-principal token acquisition for Fabric bridging (Layer 3).

Centralises the client-credentials flow so the OneLake writer and the Fabric job
client share one implementation. Reuses the existing Power BI service principal
(`PBI_TENANT_ID` / `PBI_CLIENT_ID` / `PBI_CLIENT_SECRET`) by default, but prefers
dedicated `FABRIC_BRIDGE_*` creds if they are set — so a future isolated SP needs
only an .env change, no code change. See docs/architecture/fabric-bridge-setup.md.

Tokens are cached per-scope until ~2 min before expiry (MSAL also caches, but a
thin guard avoids re-instantiating the app on every call).
"""
from __future__ import annotations

import os
import threading
import time

import msal

# Scopes used by the bridge:
#   Fabric REST (trigger notebook jobs)
FABRIC_API_SCOPE = "https://api.fabric.microsoft.com/.default"
#   OneLake / ADLS Gen2 DFS (write bronze files)
STORAGE_SCOPE = "https://storage.azure.com/.default"

_lock = threading.Lock()
_cache: dict[str, tuple[str, float]] = {}  # scope -> (token, expires_at_epoch)


class AzureAuthError(RuntimeError):
    """Raised when the service principal cannot acquire a token."""


def _creds() -> tuple[str, str, str]:
    """Return (tenant_id, client_id, client_secret), preferring FABRIC_BRIDGE_*."""
    tenant = os.getenv("FABRIC_BRIDGE_TENANT_ID") or os.getenv("PBI_TENANT_ID")
    client = os.getenv("FABRIC_BRIDGE_CLIENT_ID") or os.getenv("PBI_CLIENT_ID")
    secret = os.getenv("FABRIC_BRIDGE_CLIENT_SECRET") or os.getenv("PBI_CLIENT_SECRET")
    missing = [
        name
        for name, val in (
            ("tenant_id", tenant),
            ("client_id", client),
            ("client_secret", secret),
        )
        if not val
    ]
    if missing:
        raise AzureAuthError(
            f"Missing service-principal credentials: {missing} "
            "(set PBI_* or FABRIC_BRIDGE_* in .env)"
        )
    return tenant, client, secret  # type: ignore[return-value]


def acquire_token(scope: str) -> str:
    """Client-credentials bearer token for the given resource scope.

    Cached per scope until shortly before expiry. Raises AzureAuthError on
    failure so callers can map it to a clean 5xx / 'capacity unavailable' message.
    """
    now = time.time()
    with _lock:
        cached = _cache.get(scope)
        if cached and cached[1] - 120 > now:
            return cached[0]

    tenant, client, secret = _creds()
    app = msal.ConfidentialClientApplication(
        client_id=client,
        client_credential=secret,
        authority=f"https://login.microsoftonline.com/{tenant}",
    )
    result = app.acquire_token_for_client(scopes=[scope])
    if "access_token" not in result:
        err = (
            result.get("error_description")
            or result.get("error")
            or "unknown error"
        )
        raise AzureAuthError(f"Azure AD token request failed for {scope}: {err}")

    token = result["access_token"]
    expires_in = int(result.get("expires_in", 3600))
    with _lock:
        _cache[scope] = (token, now + expires_in)
    return token
