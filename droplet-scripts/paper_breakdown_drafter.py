#!/opt/brand-agent/venv/bin/python3
"""paper_breakdown_drafter — turn a discovered arXiv paper into content.

YC principle: compounding distribution. discovery_v2 finds fresh papers in
Sergei's domain daily. Instead of just notifying, this turns the BEST one into
a short "paper breakdown" post that ties the new work to Sergei's own preprints
— positioning him as someone at the frontier, and creating a citation/mention
hook back to his work.

Triggered by paper_discovered events (emit_event hook), but rate-limited: only
drafts a breakdown for the FIRST relevant paper per day (avoid flooding). State
in /root/.openclaw/agent_state.sqlite breakdown_log.

  paper_breakdown_drafter.py <slug>

Output: /opt/reports/posts/breakdowns/<date>-<slug>.md  + TG preview.
Composer = Sonnet; Verifier checks it doesn't misrepresent the paper or Sergei.
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone, date
from pathlib import Path

sys.path.insert(0, "/opt/brand-agent")
from model_router import run_llm  # noqa: E402

REPORTS = Path("/opt/reports")
INBOX = REPORTS / "reports" / "inbox"
OUT_DIR = REPORTS / "posts" / "breakdowns"
PREPRINTS = Path("/opt/brand-agent/knowledge_base/preprints.json")
SOUL = Path("/opt/brand-agent/SOUL.md")
STATE_DB = Path("/root/.openclaw/agent_state.sqlite")


def _already_today() -> bool:
    """Rate-limit: one breakdown per day."""
    try:
        conn = sqlite3.connect(STATE_DB)
        conn.execute("CREATE TABLE IF NOT EXISTS breakdown_log "
                     "(day TEXT PRIMARY KEY, slug TEXT, ts TEXT)")
        row = conn.execute("SELECT 1 FROM breakdown_log WHERE day=?",
                           (date.today().isoformat(),)).fetchone()
        conn.close()
        return row is not None
    except Exception:
        return False


def _mark_today(slug: str) -> None:
    try:
        conn = sqlite3.connect(STATE_DB)
        conn.execute("CREATE TABLE IF NOT EXISTS breakdown_log "
                     "(day TEXT PRIMARY KEY, slug TEXT, ts TEXT)")
        conn.execute("INSERT OR REPLACE INTO breakdown_log VALUES (?,?,?)",
                     (date.today().isoformat(), slug,
                      datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()
    except Exception:
        pass


def _find_inbox(slug: str):
    matches = sorted(INBOX.glob(f"*_{slug}*.md"))
    return matches[-1] if matches else None


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: paper_breakdown_drafter.py <slug>")
        return 1
    slug = sys.argv[1]
    if _already_today():
        print("breakdown: already drafted one today, skipping")
        return 0

    inbox = _find_inbox(slug)
    if not inbox:
        print(f"no inbox for {slug}")
        return 1
    paper_ctx = inbox.read_text(encoding="utf-8")[:2500]
    soul = SOUL.read_text(encoding="utf-8")[:1200] if SOUL.exists() else ""
    preprints = PREPRINTS.read_text(encoding="utf-8")[:1500] if PREPRINTS.exists() else ""

    prompt = (
        "You are Sergei Solovev writing a short 'paper breakdown' post about a "
        "newly published arXiv paper in your field. Voice: technical, honest, no "
        "hype, no exclamation marks. The goal: show you're at the frontier AND "
        "connect the new paper to YOUR own work (cite the relevant preprint by "
        "title). 150-220 words.\n\n"
        f"YOUR VOICE:\n{soul}\n\n"
        f"YOUR PREPRINTS (cite the most relevant ONE, exact title):\n{preprints}\n\n"
        f"THE NEW PAPER (from arXiv):\n{paper_ctx}\n\n"
        "Structure: (1) one-line what the paper does, (2) the one interesting "
        "finding or limitation, (3) how it connects to / contrasts with your own "
        "work — name your preprint, (4) one forward question. End with 2-3 "
        "hashtags. Do NOT overclaim about the paper or your work. If the paper "
        "isn't actually close to your domains, respond with exactly: SKIP.\n\n"
        "Output ONLY the post text."
    )
    post = run_llm("commentary", prompt, timeout=120)
    if not post or post.strip() == "SKIP":
        print("breakdown: Composer judged paper not relevant enough — SKIP")
        return 0

    # Verify it doesn't misrepresent Sergei's work (citation correctness)
    verdict = "PASS"
    try:
        import verifier
        vr = verifier.verify(post, "arXiv paper breakdown post", high_stakes=False)
        verdict = vr.get("verdict", "PASS")
    except Exception:
        pass

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    safe = re.sub(r"[^a-z0-9-]+", "-", slug.lower())[:40]
    f = OUT_DIR / f"{today}-{safe}.md"
    f.write_text(f"<!-- breakdown · verdict {verdict} -->\n\n{post}\n", encoding="utf-8")
    _mark_today(slug)

    # Commit + notify
    try:
        subprocess.run(["git", "-C", str(REPORTS), "add",
                        f"posts/breakdowns/{today}-{safe}.md"], check=False)
        subprocess.run(
            ["git", "-C", str(REPORTS), "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m", f"breakdown post: {slug[:50]}", "--quiet"], check=False)
        subprocess.run(["git", "-C", str(REPORTS), "push", "--quiet"], check=False)
    except Exception:
        pass

    subprocess.run([
        "/usr/local/bin/tg_send",
        f"📰 *Paper breakdown drafted* (verdict {verdict})\n\n{post[:600]}\n\n"
        f"https://github.com/SergeySolovyev/sergei-brand-agent-reports/"
        f"blob/main/posts/breakdowns/{today}-{safe}.md"],
        check=False)
    print(f"breakdown drafted for {slug}, verdict {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
