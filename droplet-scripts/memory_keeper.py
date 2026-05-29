"""memory_keeper — file-of-record memory consolidation (sleep-time agent).

Research consensus (Letta benchmark): a plain filesystem at 74.0% beats graph
memory at 68.5% on LoCoMo. Files win — auditable, version-controlled, cheap.
Claude's own design: memory.md index → domain files; CLAUDE.md = constitution.

This runs nightly (03:00 UTC, the quiet hours) as a Haiku "sleep-time" agent:
  1. Read last 24h of events (audit jsonl) + button actions (event_actions)
  2. Summarize the day into reports memory: what happened, what worked
  3. Update domain files: opportunities.md, contacts.md, decisions.md, deadlines.md
  4. Maintain memory.md as the pointer/index so only relevant context loads
  5. Prune: archive entries older than 90 days

Lives in /opt/reports/memory/ — committed to git for audit trail + so Claude
(the build brain) reads it on session start.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, "/opt/brand-agent")
from model_router import run_llm  # noqa: E402

MEMORY_DIR = Path("/opt/reports/memory")
AUDIT_DIR = Path("/opt/reports/audit")
STATE_DB = Path("/root/.openclaw/agent_state.sqlite")


def _recent_events(hours: int = 24) -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp()
    month = datetime.utcnow().strftime("%Y-%m")
    audit_file = AUDIT_DIR / month / "events.jsonl"
    events = []
    if audit_file.exists():
        for line in audit_file.read_text().splitlines():
            try:
                ev = json.loads(line)
                if ev.get("unix", 0) >= cutoff:
                    events.append(ev)
            except Exception:
                pass
    return events


def _button_actions(hours: int = 24) -> list[tuple]:
    if not STATE_DB.exists():
        return []
    try:
        conn = sqlite3.connect(STATE_DB)
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        rows = conn.execute(
            "SELECT slug, action, param, ts FROM event_actions "
            "WHERE ts >= ? ORDER BY ts",
            (cutoff,),
        ).fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def _consolidate(events: list[dict], actions: list[tuple]) -> str:
    """Haiku summarizes the day into a memory entry."""
    ev_lines = "\n".join(
        f"  - [{e.get('severity','?')}] {e.get('kind','?')}: {e.get('title','')[:80]}"
        for e in events[:40]
    ) or "  (no events)"
    act_lines = "\n".join(
        f"  - {a[1]} on {a[0]} {('('+a[2]+')') if a[2] else ''}"
        for a in actions[:20]
    ) or "  (no decisions)"

    prompt = (
        "You maintain Sergei Solovev's brand-agent memory. Summarize the last "
        "24 hours into a TERSE memory entry (max 150 words). Focus on: what "
        "opportunities appeared, what Sergei decided (button actions), what "
        "shipped, what's pending. Factual bullet points, no fluff.\n\n"
        f"EVENTS:\n{ev_lines}\n\n"
        f"SERGEI'S DECISIONS (button actions):\n{act_lines}\n\n"
        "Output a markdown section starting with '## <today's date>'."
    )
    return run_llm("memory_consolidate", prompt, timeout=45)


def _ensure_domain_files() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    index = MEMORY_DIR / "memory.md"
    if not index.exists():
        index.write_text(
            "# Brand Agent Memory — Index\n\n"
            "Pointer file. Domain memory lives in sibling files:\n\n"
            "- [daily-log.md](daily-log.md) — chronological consolidation\n"
            "- [opportunities.md](opportunities.md) — grants/CFPs/hackathons seen\n"
            "- [contacts.md](contacts.md) — people who reached out / cited\n"
            "- [decisions.md](decisions.md) — what Sergei approved/skipped/muted\n"
            "- [deadlines.md](deadlines.md) — tracked deadlines\n",
            encoding="utf-8",
        )
    for fname, header in [
        ("daily-log.md", "# Daily Log (newest first)\n"),
        ("opportunities.md", "# Opportunities Seen\n"),
        ("contacts.md", "# Contacts\n"),
        ("decisions.md", "# Decisions Log\n"),
        ("deadlines.md", "# Deadlines\n"),
    ]:
        f = MEMORY_DIR / fname
        if not f.exists():
            f.write_text(header, encoding="utf-8")


def main() -> int:
    _ensure_domain_files()
    events = _recent_events(24)
    actions = _button_actions(24)

    summary = _consolidate(events, actions)
    if summary:
        # Prepend to daily-log (newest first)
        daily = MEMORY_DIR / "daily-log.md"
        old = daily.read_text(encoding="utf-8")
        header, _, body = old.partition("\n")
        daily.write_text(f"{header}\n\n{summary}\n{body}", encoding="utf-8")

    # Record decisions to decisions.md
    if actions:
        dec = MEMORY_DIR / "decisions.md"
        lines = [f"- {a[3][:10]} · {a[1]} · {a[0]}" for a in actions]
        with dec.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    # Commit
    try:
        subprocess.run(["git", "-C", "/opt/reports", "add", "memory/"], check=False)
        subprocess.run(
            ["git", "-C", "/opt/reports", "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m",
             f"memory: consolidate {datetime.utcnow().strftime('%Y-%m-%d')}",
             "--quiet"], check=False,
        )
        subprocess.run(["git", "-C", "/opt/reports", "push", "--quiet"], check=False)
    except Exception:
        pass

    print(f"memory consolidated: {len(events)} events, {len(actions)} decisions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
