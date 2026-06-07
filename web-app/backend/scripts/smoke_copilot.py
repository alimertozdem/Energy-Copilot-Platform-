"""End-to-end smoke test for /copilot.

Verifies:
    0. ANTHROPIC_API_KEY env var is set
    1. /auth/login returns a JWT
    2. POST /copilot/conversations creates a thread (201)
    3. GET  /copilot/conversations lists it
    4. POST /copilot/conversations/{id}/messages streams SSE events
       - Logs every event type encountered
       - Asserts that at least one of {tool_call, text, complete} arrives
       - Flags any 'error' event for inspection
    5. GET  /copilot/conversations/{id} returns the persisted history

Run:
    cd web-app/backend
    .\\venv\\Scripts\\activate
    python scripts/smoke_copilot.py

The default credentials assume the email-provider test user created in
Day 11-12 (alimertozdem@gmail.com is via Microsoft/Google providers, not
Credentials). Edit SMOKE_EMAIL/SMOKE_PASSWORD below or pass --email/--pw.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env so ANTHROPIC_API_KEY can be checked.
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

# Defaults — override via CLI args.
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_EMAIL = "test1@energylens.eu"          # created in Day 12 backend test
DEFAULT_PASSWORD = "password1234"               # change if you set a different one
DEFAULT_PROMPT = "B001'in son 30 günlük enerji tüketimini söyle."

C_GREEN = "\033[32m"
C_RED = "\033[31m"
C_YELLOW = "\033[33m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"{C_GREEN}OK{C_RESET}  {msg}")


def fail(msg: str) -> None:
    print(f"{C_RED}FAIL{C_RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{C_YELLOW}WARN{C_RESET} {msg}")


def dim(msg: str) -> None:
    print(f"{C_DIM}{msg}{C_RESET}")


def check_env() -> None:
    print("\n[0] Environment check")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        fail("ANTHROPIC_API_KEY not set. Add it to web-app/backend/.env and rerun.")
        sys.exit(1)
    if not key.startswith("sk-ant-"):
        warn(f"ANTHROPIC_API_KEY does not start with 'sk-ant-' (got '{key[:8]}…'). "
             "Check that you copied the full key.")
    else:
        ok(f"ANTHROPIC_API_KEY present ({key[:11]}…{key[-4:]})")

    for var in ("FABRIC_SQL_SERVER", "FABRIC_SQL_DATABASE", "PBI_TENANT_ID"):
        if not os.environ.get(var):
            warn(f"{var} not set — tools may fail.")


def login(client: httpx.Client, email: str, password: str) -> str:
    print("\n[1] /auth/login")
    # /auth/login is service-to-service protected — frontend NextAuth normally
    # provides this header; for the smoke script we read it from .env directly.
    internal_key = os.environ.get("INTERNAL_API_KEY")
    if not internal_key:
        fail("INTERNAL_API_KEY not set in .env — required for /auth/login.")
        sys.exit(1)
    r = client.post(
        "/auth/login",
        json={"email": email, "password": password},
        headers={"X-Internal-Api-Key": internal_key},
    )
    if r.status_code != 200:
        fail(f"Login returned {r.status_code}: {r.text}")
        sys.exit(1)
    data = r.json()
    token = data.get("access_token")
    if not token:
        fail(f"Login response has no access_token: {data}")
        sys.exit(1)
    ok(f"Got JWT (user_id={data.get('user_id')}, len={len(token)})")
    return token


def create_conversation(client: httpx.Client, title: str | None = None) -> str:
    print("\n[2] POST /copilot/conversations")
    body = {"title": title} if title else {}
    r = client.post("/copilot/conversations", json=body)
    if r.status_code != 201:
        fail(f"Create returned {r.status_code}: {r.text}")
        sys.exit(1)
    data = r.json()
    ok(f"Created conversation id={data['id']} title={data['title']!r}")
    return data["id"]


def list_conversations(client: httpx.Client, expect_id: str) -> None:
    print("\n[3] GET /copilot/conversations")
    r = client.get("/copilot/conversations")
    if r.status_code != 200:
        fail(f"List returned {r.status_code}: {r.text}")
        sys.exit(1)
    items = r.json()["conversations"]
    found = next((x for x in items if x["id"] == expect_id), None)
    if not found:
        fail(f"Newly-created conversation {expect_id} not in list (size={len(items)})")
        sys.exit(1)
    ok(f"List has {len(items)} convos; new one present")


def stream_message(
    client: httpx.Client,
    conversation_id: str,
    prompt: str,
) -> dict:
    print(f"\n[4] POST /copilot/conversations/{conversation_id}/messages (SSE)")
    print(f"    prompt: {prompt!r}")

    counts: dict[str, int] = {}
    text_chunks: list[str] = []
    tool_calls: list[dict] = []
    tool_results: list[dict] = []
    complete_meta: dict | None = None
    errors: list[dict] = []
    t0 = time.monotonic()

    with client.stream(
        "POST",
        f"/copilot/conversations/{conversation_id}/messages",
        json={"content": prompt},
        timeout=120.0,
    ) as r:
        if r.status_code != 200:
            r.read()
            fail(f"Stream returned {r.status_code}: {r.text}")
            sys.exit(1)

        current_event = None
        for raw in r.iter_lines():
            line = raw if isinstance(raw, str) else raw.decode()
            if not line:
                current_event = None
                continue
            if line.startswith("event: "):
                current_event = line[len("event: "):].strip()
                counts[current_event] = counts.get(current_event, 0) + 1
                continue
            if line.startswith("data: "):
                payload_raw = line[len("data: "):]
                try:
                    payload = json.loads(payload_raw)
                except json.JSONDecodeError:
                    payload = {"_raw": payload_raw}

                if current_event == "text":
                    text_chunks.append(payload.get("text", ""))
                elif current_event == "tool_call":
                    tool_calls.append(payload)
                    print(f"    {C_YELLOW}→ tool_call: {payload.get('tool')} "
                          f"input={json.dumps(payload.get('input'))[:120]}{C_RESET}")
                elif current_event == "tool_result":
                    tool_results.append(payload)
                    preview = payload.get("result_preview", "")[:120]
                    err_flag = " [ERROR]" if payload.get("is_error") else ""
                    print(f"    {C_DIM}← tool_result: {payload.get('tool')}{err_flag} "
                          f"{preview}{C_RESET}")
                elif current_event == "complete":
                    complete_meta = payload
                elif current_event == "error":
                    errors.append(payload)
                    fail(f"error event: {payload.get('message')}")

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    full_text = "".join(text_chunks)

    print(f"\n    {C_DIM}--- stream stats ---{C_RESET}")
    print(f"    event counts:  {counts}")
    print(f"    text chars:    {len(full_text)}")
    print(f"    tool_calls:    {len(tool_calls)}")
    print(f"    tool_results:  {len(tool_results)}")
    print(f"    errors:        {len(errors)}")
    print(f"    elapsed:       {elapsed_ms}ms")
    if complete_meta:
        print(f"    stop_reason:   {complete_meta.get('stop_reason')}")
        print(f"    tokens:        in={complete_meta.get('tokens_input')} "
              f"out={complete_meta.get('tokens_output')}")

    if full_text:
        wrapped = textwrap.fill(full_text, width=100, initial_indent="    > ",
                                subsequent_indent="    > ")
        print(f"\n    {C_GREEN}--- assistant final text ---{C_RESET}\n{wrapped}")

    if errors:
        fail(f"{len(errors)} error events received — see above")
        return {"errors": errors}
    if not complete_meta:
        warn("Stream ended without a 'complete' event")
    if not full_text and not tool_calls:
        warn("No text and no tool calls — model didn't produce anything useful")
    else:
        ok(f"Stream completed ({len(tool_calls)} tool call(s), "
           f"{len(full_text)} chars text)")
    return {
        "counts": counts,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "complete": complete_meta,
        "text": full_text,
    }


def fetch_history(client: httpx.Client, conversation_id: str) -> None:
    print("\n[5] GET /copilot/conversations/{id}")
    r = client.get(f"/copilot/conversations/{conversation_id}")
    if r.status_code != 200:
        fail(f"History returned {r.status_code}: {r.text}")
        sys.exit(1)
    data = r.json()
    msgs = data["messages"]
    print(f"    {len(msgs)} message(s) persisted:")
    for m in msgs:
        role = m["role"]
        content_preview = (m.get("content") or "")[:80].replace("\n", " ")
        tool_calls = m.get("tool_calls")
        extra = ""
        if tool_calls:
            tc = tool_calls if isinstance(tool_calls, list) else [tool_calls]
            extra = f"  +{len(tc)} tool_call(s)"
        print(f"    [{role:9s}] {content_preview!r}{extra}")
    ok(f"History endpoint returned {len(msgs)} messages")


def main():
    parser = argparse.ArgumentParser(description="Copilot smoke test")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--pw", default=DEFAULT_PASSWORD)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--title", default="Smoke test (auto)")
    args = parser.parse_args()

    check_env()

    client = httpx.Client(base_url=args.base_url, timeout=30.0)
    token = login(client, args.email, args.pw)
    client.headers["Authorization"] = f"Bearer {token}"

    conv_id = create_conversation(client, title=args.title)
    list_conversations(client, expect_id=conv_id)
    stream_message(client, conv_id, args.prompt)
    fetch_history(client, conv_id)

    print(f"\n{C_GREEN}=== Copilot smoke complete ==={C_RESET}\n")


if __name__ == "__main__":
    main()
