#!/opt/brand-agent/venv/bin/python3
"""draft_reply — generate a reply draft for an inbound mention.

Invoked by telegram_bot.py when user clicks 💬 Reply.
  draft_reply.py <slug>

Flow:
  1. Find the original inbox file at /opt/reports/inbox/*_<slug>.md
  2. Extract sender / subject / body from the markdown
  3. Call claude-cli (Sonnet, Max subscription) with Composer + Critic prompts
  4. Insert draft into agent_state.sqlite `drafts` table
  5. Send draft to Telegram with [✅ Send] [✏️ Edit] [❌ Discard] buttons

The actual SMTP send happens in send_reply.py — only after Sergei taps ✅.
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_DB = Path("/root/.openclaw/agent_state.sqlite")
REPORTS_INBOX = Path("/opt/reports/reports/inbox")
SOUL_PATH = Path("/opt/brand-agent/SOUL.md")


def _db():
    conn = sqlite3.connect(STATE_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS drafts (
          draft_id      INTEGER PRIMARY KEY AUTOINCREMENT,
          slug          TEXT,
          channel       TEXT,
          recipient     TEXT,
          gmail_msg_id  TEXT,
          subject       TEXT,
          body          TEXT,
          status        TEXT,
          created_at    TEXT,
          decided_at    TEXT
        )
        """
    )
    return conn


def _find_inbox_file(slug: str) -> Path | None:
    """Find latest inbox MD file matching this slug."""
    if not REPORTS_INBOX.exists():
        return None
    matches = sorted(REPORTS_INBOX.glob(f"*_{slug}.md"))
    return matches[-1] if matches else None


def _parse_inbox_md(path: Path) -> dict:
    """Extract From / Subject / body / Gmail message_id from inbox markdown."""
    text = path.read_text(encoding="utf-8")
    out = {"raw": text}
    m = re.search(r"^From:\s*(.+)$", text, re.MULTILINE)
    if m:
        out["sender"] = m.group(1).strip()
        # Pull bare email
        m2 = re.search(r"<([^>]+@[^>]+)>", out["sender"])
        out["recipient"] = m2.group(1) if m2 else out["sender"]
    m = re.search(r"^Subject:\s*(.+)$", text, re.MULTILINE)
    if m:
        out["subject"] = m.group(1).strip()
    m = re.search(r"#inbox/([a-zA-Z0-9]+)", text)
    if m:
        out["gmail_msg_id"] = m.group(1)
    # Everything after the From: / Subject: block is body
    body_match = re.split(r"\n\n", text, maxsplit=2)
    out["body"] = body_match[-1] if body_match else ""
    return out


def _compose_draft(email: dict) -> str:
    """Ask claude-cli to draft a reply matching brand voice."""
    soul = SOUL_PATH.read_text() if SOUL_PATH.exists() else ""
    prompt = (
        "You are Sergei Solovev replying to an email. Stay in HIS voice: "
        "concise, technical, no fluff, no exclamation marks, no LinkedIn-speak. "
        "Russian if the inbound was Russian, English otherwise. "
        "If the inbound is asking a question, answer it. If it's a meeting "
        "request, propose a 30-min slot next week. If it's a marketing email, "
        "do NOT generate a reply — return literally the string SKIP.\n\n"
        f"Brand voice reference:\n{soul[:1500]}\n\n"
        f"--- INBOUND EMAIL ---\n"
        f"From: {email.get('sender', '?')}\n"
        f"Subject: {email.get('subject', '?')}\n\n"
        f"{email.get('body', '')[:2000]}\n"
        f"--- END INBOUND ---\n\n"
        "Respond with ONLY the reply body (no Subject line, no greeting "
        "header — the email client wraps that). Keep under 200 words. "
        "Sign as: 'Sergei' (or 'Сергей' for Russian)."
    )
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception as e:
        print(f"compose error: {e}")
        return ""


def _emit_draft_to_telegram(draft_id: int, slug: str, recipient: str,
                            subject: str, draft_body: str) -> None:
    """Send draft preview to Telegram with action buttons."""
    preview = (
        f"📝 *Draft reply* (#{draft_id})\n"
        f"To: {recipient}\n"
        f"Re: {subject[:60]}\n\n"
        f"{draft_body[:1500]}"
    )
    subprocess.run(
        ["/usr/local/bin/tg_send",
         "--kind", "draft_reply",
         "--slug", str(draft_id),
         preview],
        check=False,
    )


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: draft_reply.py <slug>")
        return 1
    slug = sys.argv[1]

    inbox_file = _find_inbox_file(slug)
    if not inbox_file:
        print(f"no inbox file for slug={slug}")
        return 1

    email = _parse_inbox_md(inbox_file)
    print(f"composing reply to: {email.get('sender', '?')}")

    draft_body = _compose_draft(email)
    if not draft_body or draft_body.strip() == "SKIP":
        # Composer decided this isn't worth replying to (likely marketing)
        subprocess.run(
            ["/usr/local/bin/tg_send",
             f"📭 No reply drafted — Composer judged this not worth a response "
             f"(likely marketing).\nSlug: {slug}"],
            check=False,
        )
        return 0

    conn = _db()
    try:
        cursor = conn.execute(
            "INSERT INTO drafts (slug, channel, recipient, gmail_msg_id, "
            "subject, body, status, created_at) "
            "VALUES (?, 'gmail', ?, ?, ?, ?, 'pending', ?)",
            (slug, email.get("recipient", ""), email.get("gmail_msg_id", ""),
             f"Re: {email.get('subject', '')}", draft_body,
             datetime.now(timezone.utc).isoformat()),
        )
        draft_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()

    _emit_draft_to_telegram(
        draft_id, slug, email.get("recipient", "?"),
        email.get("subject", "?"), draft_body,
    )
    print(f"draft #{draft_id} sent to Telegram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
