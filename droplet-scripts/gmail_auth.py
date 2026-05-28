#!/usr/bin/env python3
"""Gmail OAuth helper — three-step manual flow for headless droplet.

Why manual: the droplet can't open a browser on Sergei's machine, so the
google_auth_oauthlib InstalledAppFlow local-server trick doesn't work.
Instead we do the same dance as the Anthropic OAuth flow:

  Step 1:  emit_url     → prints auth URL Sergei opens in Chrome
  Step 2:  exchange     → exchanges code from redirect URL for tokens
  Step 3:  test         → fetches the inbox to verify everything works

Scope: gmail.modify  → read + draft + send + labels (NOT permanent delete).

Storage:
  Credentials JSON  → /opt/brand-agent/secrets/gmail_credentials.json (0600)
  OAuth tokens      → /opt/brand-agent/secrets/gmail_token.json     (0600)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SECRETS = Path("/opt/brand-agent/secrets")
CREDS_PATH = SECRETS / "gmail_credentials.json"
TOKEN_PATH = SECRETS / "gmail_token.json"
VERIFIER_PATH = SECRETS / "gmail_code_verifier.txt"

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
REDIRECT_URI = "http://localhost:8080/"


def step_emit_url() -> int:
    """Print the Google consent URL for Sergei to open."""
    if not CREDS_PATH.exists():
        print(
            f"ERROR: {CREDS_PATH} not found.\n\n"
            "Get it from Google Cloud Console:\n"
            "  1. https://console.cloud.google.com/ → new project (e.g. 'sergei-brand-agent')\n"
            "  2. APIs & Services → Library → enable 'Gmail API'\n"
            "  3. APIs & Services → OAuth consent screen:\n"
            "     • User type: External\n"
            "     • App name: sergei-brand-agent\n"
            "     • Your email + same as developer contact\n"
            "     • Scopes → Add 'https://www.googleapis.com/auth/gmail.modify'\n"
            "     • Test users → add sssolovjov@gmail.com\n"
            "  4. APIs & Services → Credentials → Create → OAuth client ID\n"
            "     • Type: Desktop app\n"
            "     • Name: sergei-brand-agent-droplet\n"
            "     • Download JSON → upload to droplet at the path above.",
            file=sys.stderr,
        )
        return 1

    flow = Flow.from_client_secrets_file(
        str(CREDS_PATH), scopes=SCOPES, redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",          # force refresh_token issuance
        include_granted_scopes="true",
    )
    # Persist PKCE code_verifier so step_exchange can replay it.
    # Without this, Google returns "Missing code verifier" on token exchange.
    SECRETS.mkdir(parents=True, exist_ok=True)
    VERIFIER_PATH.write_text(flow.code_verifier or "")
    os.chmod(VERIFIER_PATH, 0o600)
    print("Open this URL in Chrome (already signed into sssolovjov@gmail.com):\n")
    print(auth_url)
    print(
        "\nAfter clicking 'Allow', your browser will try to load\n"
        "  http://localhost:8080/?code=...&scope=...\n"
        "and show 'Site can't be reached' — that's fine. Copy the FULL URL\n"
        "from the address bar and run:\n"
        "  gmail_auth.py exchange '<paste URL here>'\n"
    )
    return 0


def step_exchange(redirect_url: str) -> int:
    """Exchange the auth code (in redirect URL) for access + refresh tokens."""
    if not CREDS_PATH.exists():
        print(f"ERROR: {CREDS_PATH} not found", file=sys.stderr)
        return 1

    parsed = urlparse(redirect_url)
    qs = parse_qs(parsed.query)
    if "code" not in qs:
        print(f"ERROR: no 'code' parameter in URL.\nFull qs: {qs}", file=sys.stderr)
        return 1
    code = qs["code"][0]

    flow = Flow.from_client_secrets_file(
        str(CREDS_PATH), scopes=SCOPES, redirect_uri=REDIRECT_URI,
    )
    # Replay the PKCE verifier from step_emit_url
    if VERIFIER_PATH.exists():
        flow.code_verifier = VERIFIER_PATH.read_text().strip()
    flow.fetch_token(code=code)
    creds = flow.credentials

    SECRETS.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())
    os.chmod(TOKEN_PATH, 0o600)
    print(f"✓ token saved → {TOKEN_PATH}")
    print(f"  refresh_token present: {bool(creds.refresh_token)}")
    print("Run: gmail_auth.py test")
    return 0


def step_test() -> int:
    """Fetch inbox metadata to verify OAuth works."""
    if not TOKEN_PATH.exists():
        print(f"ERROR: {TOKEN_PATH} not found — run exchange first", file=sys.stderr)
        return 1
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    print(f"✓ authenticated as {profile['emailAddress']}")
    print(f"  messages total: {profile['messagesTotal']}")
    print(f"  threads total:  {profile['threadsTotal']}")

    # Show 5 most recent inbox subjects
    recent = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], maxResults=5)
        .execute()
    )
    print("\nRecent 5 inbox subjects:")
    for msg_ref in recent.get("messages", []):
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg_ref["id"],
                format="metadata",
                metadataHeaders=["Subject", "From"],
            )
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subj = headers.get("Subject", "(no subject)")[:60]
        sender = headers.get("From", "(unknown)")[:40]
        print(f"  • {subj}  ← {sender}")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "emit_url":
        return step_emit_url()
    elif cmd == "exchange":
        if len(sys.argv) < 3:
            print("Usage: gmail_auth.py exchange '<redirect URL>'", file=sys.stderr)
            return 1
        return step_exchange(sys.argv[2])
    elif cmd == "test":
        return step_test()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
