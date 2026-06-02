#!/opt/brand-agent/venv/bin/python3
"""retrospective — weekly self-improvement loop (evaluator-optimizer, meta-level).

YC principle: fast iteration + measure what matters. The GBrain pattern: the
agent learns from its own history. Each week this:

  1. Reviews the past week — what was emitted, what Sergei ENGAGED with
     (button clicks = ground-truth preference signal), what he SKIPPED/MUTED
  2. Computes simple signal: which kinds/topics get engaged vs ignored
  3. Asks an LLM to propose concrete tuning: discovery keywords to add/drop,
     senders to promote/mute, content angles that land
  4. Applies the safe automatic changes (discovery keyword additions, mutes)
  5. Writes a retrospective note to memory + a digest to Sergei

This closes the loop: discovery_v2 / triage get smarter from Sergei's behavior
without him having to configure anything.

Runs weekly (Sunday 20:00 UTC). Output:
  /opt/reports/memory/retrospective.md  (append)
  /opt/brand-agent/learned_keywords.json (discovery_v2 reads this)
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, "/opt/brand-agent")
from model_router import run_llm  # noqa: E402

REPORTS = Path("/opt/reports")
MEMORY = REPORTS / "memory" / "retrospective.md"
AUDIT_DIR = REPORTS / "audit"
LEARNED = Path("/opt/brand-agent/learned_keywords.json")
STATE_DB = Path("/root/.openclaw/agent_state.sqlite")


def _week_events() -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).timestamp()
    out = []
    for md in sorted(AUDIT_DIR.glob("*")):
        jf = md / "events.jsonl"
        if not jf.exists():
            continue
        for line in jf.read_text().splitlines():
            try:
                ev = json.loads(line)
                if ev.get("unix", 0) >= cutoff:
                    out.append(ev)
            except Exception:
                pass
    return out


def _actions() -> list[tuple]:
    if not STATE_DB.exists():
        return []
    try:
        conn = sqlite3.connect(STATE_DB)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        rows = conn.execute(
            "SELECT slug, action FROM event_actions WHERE ts>=?", (cutoff,)
        ).fetchall()
        conn.close()
        return rows or []
    except Exception:
        return []


def main() -> int:
    events = _week_events()
    actions = _actions()

    kind_counts = Counter(e.get("kind", "?") for e in events)
    # engaged = interested/compose/reply ; rejected = skip/mute
    engaged = [s for s, a in actions if a in ("i", "t", "r")]
    rejected = [s for s, a in actions if a in ("s", "m")]

    summary = (
        f"events this week: {dict(kind_counts)}\n"
        f"engaged ({len(engaged)}): {engaged[:15]}\n"
        f"rejected ({len(rejected)}): {rejected[:15]}\n"
    )

    existing_learned = {}
    if LEARNED.exists():
        try:
            existing_learned = json.loads(LEARNED.read_text())
        except Exception:
            pass

    prompt = (
        "You are the retrospective/optimizer for Sergei Solovev's brand agent. "
        "Based on a week of activity and Sergei's engagement (button clicks are "
        "ground-truth: 'interested/compose/reply' = he cares; 'skip/mute' = noise), "
        "propose concrete tuning to make next week sharper.\n\n"
        f"WEEK SUMMARY:\n{summary}\n\n"
        f"CURRENT learned discovery keywords: {json.dumps(existing_learned.get('keywords', []))}\n\n"
        "Output ONLY JSON:\n"
        "{\n"
        '  "insights": ["<2-4 short observations about what landed vs flopped>"],\n'
        '  "add_keywords": ["<0-5 NEW discovery search terms to add, specific to what he engaged with>"],\n'
        '  "drop_keywords": ["<0-3 existing learned keywords to remove if they produced noise>"],\n'
        '  "next_focus": "<one sentence: what the agent should prioritize next week>"\n'
        "}\n"
        "Keep keywords concrete and relevant to DeFi-security / RAG / quant / AI-agents."
    )
    out = run_llm("summarize", prompt, timeout=90)
    m = re.search(r"\{.*\}", out, re.DOTALL)
    rec = {}
    if m:
        try:
            rec = json.loads(m.group(0))
        except Exception:
            pass

    # Apply safe automatic changes: update learned_keywords
    kw = set(existing_learned.get("keywords", []))
    for k in rec.get("add_keywords", []):
        if isinstance(k, str) and 3 < len(k) < 60:
            kw.add(k)
    for k in rec.get("drop_keywords", []):
        kw.discard(k)
    LEARNED.write_text(json.dumps({
        "keywords": sorted(kw),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_focus": rec.get("next_focus", ""),
    }, ensure_ascii=False, indent=2))

    # Append to memory
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    note = (f"\n## {today} retrospective\n"
            f"- " + "\n- ".join(rec.get("insights", ["(no insights)"])) + "\n"
            f"- next focus: {rec.get('next_focus','')}\n"
            f"- keywords now: {sorted(kw)}\n")
    with MEMORY.open("a", encoding="utf-8") as fh:
        fh.write(note)

    # Commit + notify
    try:
        subprocess.run(["git", "-C", str(REPORTS), "add", "memory/"], check=False)
        subprocess.run(
            ["git", "-C", str(REPORTS), "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m", f"retrospective {today}", "--quiet"], check=False)
        subprocess.run(["git", "-C", str(REPORTS), "push", "--quiet"], check=False)
    except Exception:
        pass

    insights = "\n".join(f"  • {i}" for i in rec.get("insights", [])[:4])
    subprocess.run([
        "/usr/local/bin/tg_send",
        f"🔄 *Weekly retrospective*\n\n"
        f"Engaged: {len(engaged)} · Rejected: {len(rejected)}\n\n"
        f"What I learned:\n{insights}\n\n"
        f"Next focus: {rec.get('next_focus','')}\n"
        f"Discovery keywords now: {len(kw)} (auto-tuned from your clicks)"],
        check=False)
    print(f"retrospective: {len(engaged)} engaged, {len(kw)} keywords, "
          f"{len(rec.get('add_keywords', []))} added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
