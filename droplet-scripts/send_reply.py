#!/opt/brand-agent/venv/bin/python3
"""send_reply — actually send an approved draft via Gmail API.

Invoked by telegram_bot.py when user taps ✅ Send.
  send_reply.py <draft_id>

Flow:
  1. Load draft from drafts table (status must be 'pending')
  2. Build RFC 2822 MIME with In-Reply-To / References headers for threading
  3. Call Gmail users.messages.send via google-api-python-client
  4. Mark draft status='sent', record gmail_sent_id
  5. Telegram confirmation back to Sergei
"""
from __future__ import annotations

import base64
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

STATE_DB = Path("/root/.openclaw/agent_state.sqlite")
TOKEN_PATH = Path("/opt/brand-agent/secrets/gmail_token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def _notify(text: str) -> None:
    subprocess.run(["/usr/local/bin/tg_send", text], check=False)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: send_reply.py <draft_id>")
        return 1
    try:
        draft_id = int(sys.argv[1])
    except ValueError:
        print(f"invalid draft_id: {sys.argv[1]}")
        return 1

    conn = sqlite3.connect(STATE_DB)
    row = conn.execute(
        "SELECT slug, recipient, gmail_msg_id, subject, body, status "
        "FROM drafts WHERE draft_id = ?",
        (draft_id,),
    ).fetchone()
    if not row:
        _notify(f"❌ Draft #{draft_id} not found")
        return 1
    slug, recipient, gmail_msg_id, subject, body, status = row
    if status != "pending":
        _notify(f"❌ Draft #{draft_id} already {status}")
        return 1

    if not TOKEN_PATH.exists():
        _notify(f"❌ Gmail token missing — re-run gmail_auth.py")
        return 1

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    # If we have the original Gmail message_id, fetch its Message-ID header
    # for proper threading via In-Reply-To / References.
    in_reply_to = None
    thread_id = None
    if gmail_msg_id:
        try:
            orig = service.users().messages().get(
                userId="me", id=gmail_msg_id, format="metadata",
                metadataHeaders=["Message-ID", "References"],
            ).execute()
            thread_id = orig.get("threadId")
            for h in orig.get("payload", {}).get("headers", []):
                if h["name"].lower() == "message-id":
                    in_reply_to = h["value"]
                    break
        except Exception as e:
            print(f"could not fetch original message headers: {e}")

    msg = EmailMessage()
    msg["To"] = recipient
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id

    try:
        sent = service.users().messages().send(userId="me", body=payload).execute()
    except Exception as e:
        _notify(f"❌ Send failed for draft #{draft_id}: {e}")
        return 1

    conn.execute(
        "UPDATE drafts SET status = 'sent', decided_at = ? WHERE draft_id = ?",
        (datetime.now(timezone.utc).isoformat(), draft_id),
    )
    conn.commit()
    conn.close()

    _notify(
        f"✅ Sent draft #{draft_id}\n"
        f"To: {recipient}\n"
        f"Re: {subject[:60]}\n"
        f"Gmail message_id: {sent.get('id', '?')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
