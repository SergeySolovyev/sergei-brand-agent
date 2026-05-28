"""button_actions — shared SQLite helper for inline-keyboard button presses.

Both telegram_bot.py (writer) and agent_* scripts (reader) use this.
DB: /root/.openclaw/agent_state.sqlite

Schema:
    event_actions(slug TEXT, action TEXT, param TEXT, ts TEXT, user TEXT)

`action` values produced by buttons:
  - interested  : user wants follow-up (Composer picks up)
  - skip        : user dismisses, archive
  - ack         : critical event acknowledged
  - snooze      : delay re-emit; param = days (string)
  - thank       : user wants a thank-you post drafted
  - reply       : user wants a reply drafted
  - mute        : permanently mute this source/author
  - seen        : low-friction "I read it"
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("/root/.openclaw/agent_state.sqlite")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS event_actions (
            slug TEXT,
            action TEXT,
            param TEXT,
            ts TEXT,
            user TEXT,
            PRIMARY KEY (slug, action, param)
        )
        """
    )
    return conn


def record(slug: str, action: str, param: str | None, user: str) -> bool:
    """Record a button press. Returns True if newly inserted, False if duplicate."""
    with _conn() as conn:
        try:
            conn.execute(
                "INSERT INTO event_actions VALUES (?, ?, ?, ?, ?)",
                (slug, action, param or "", datetime.now(timezone.utc).isoformat(), user),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def last_action(slug: str) -> tuple[str, str, str] | None:
    """Return (action, param, ts) of the most recent button press on this slug."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT action, param, ts FROM event_actions "
            "WHERE slug = ? ORDER BY ts DESC LIMIT 1",
            (slug,),
        ).fetchone()
        return tuple(row) if row else None


def is_skipped(slug: str) -> bool:
    """Check if this slug has been skipped — used by discovery scripts to dedup."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM event_actions WHERE slug = ? AND action = 'skip' LIMIT 1",
            (slug,),
        ).fetchone()
        return row is not None
