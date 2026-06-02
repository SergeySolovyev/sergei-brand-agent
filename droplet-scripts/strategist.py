#!/opt/brand-agent/venv/bin/python3
"""strategist — the weekly orchestrator (the agent network's brain).

YC solo-founder AI-first principle: distribution > product, compounding assets,
ship on a cadence, founder-led narrative. The Strategist ties the specialist
agents into a coherent week instead of random daily output.

Runs weekly (Monday 06:30 UTC, before the week's content fires). It:
  1. Reads the file-of-record memory (what happened, what Sergei engaged with)
  2. Reads last 7 days of events (citations, discoveries, deadlines, opportunities)
  3. Reads the preprint corpus + identity (who Sergei is, what he's about)
  4. Produces a WEEKLY PLAN (theme, narrative thread, priorities) — Opus tier
  5. Fills topic_queue.json — an ordered list of content topics for the week
     that daily_commentary + article_drafter DRAIN instead of picking randomly

Output:
  /opt/reports/plans/YYYY-WW.md         — human-readable weekly plan
  /opt/brand-agent/topic_queue.json     — machine-readable queue for drafters

This is the Orchestrator in Anthropic's Orchestrator-Workers pattern: it sets
direction; the Composer/drafters are workers that execute it.
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, "/opt/brand-agent")
from model_router import run_llm  # noqa: E402

REPORTS = Path("/opt/reports")
PLANS_DIR = REPORTS / "plans"
MEMORY_DIR = REPORTS / "memory"
AUDIT_DIR = REPORTS / "audit"
TOPIC_QUEUE = Path("/opt/brand-agent/topic_queue.json")
PREPRINTS = Path("/opt/brand-agent/knowledge_base/preprints.json")
SOUL = Path("/opt/brand-agent/SOUL.md")
STATE_DB = Path("/root/.openclaw/agent_state.sqlite")


def _recent_events(days: int = 7) -> list[str]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
    out = []
    for month_dir in sorted(AUDIT_DIR.glob("*")):
        jf = month_dir / "events.jsonl"
        if not jf.exists():
            continue
        for line in jf.read_text().splitlines():
            try:
                ev = json.loads(line)
                if ev.get("unix", 0) >= cutoff:
                    out.append(f"{ev.get('kind')}: {ev.get('title','')[:80]}")
            except Exception:
                pass
    return out[-60:]


def _engaged_signals() -> list[str]:
    """What Sergei actually clicked — strongest signal of what he cares about."""
    if not STATE_DB.exists():
        return []
    try:
        conn = sqlite3.connect(STATE_DB)
        rows = conn.execute(
            "SELECT action, slug FROM event_actions "
            "WHERE action IN ('i','t','r') ORDER BY ts DESC LIMIT 20"
        ).fetchall()
        conn.close()
        amap = {"i": "interested", "t": "compose-post", "r": "reply"}
        return [f"{amap.get(a,a)}: {s}" for a, s in rows]
    except Exception:
        return []


def _read(path: Path, limit: int = 2000) -> str:
    try:
        return path.read_text(encoding="utf-8")[:limit]
    except Exception:
        return ""


def main() -> int:
    events = _recent_events(7)
    engaged = _engaged_signals()
    soul = _read(SOUL, 1500)
    daily_log = _read(MEMORY_DIR / "daily-log.md", 1500)
    preprints = _read(PREPRINTS, 1500)

    iso_year, iso_week, _ = datetime.now(timezone.utc).isocalendar()
    week_id = f"{iso_year}-W{iso_week:02d}"

    prompt = (
        "You are the STRATEGIST for Sergei Solovev's personal-brand agent — an "
        "AI-first solo-founder growth engine. Your job: set this week's direction "
        "so the content/outreach agents ship a coherent narrative, not random "
        "posts. Think like a YC founder: distribution > product, compounding "
        "assets, founder-led story, ship on cadence.\n\n"
        f"WHO SERGEI IS (SOUL):\n{soul}\n\n"
        f"HIS PREPRINTS (the asset base to amplify):\n{preprints}\n\n"
        f"LAST 7 DAYS — events the agent surfaced:\n" + "\n".join(events[:40]) + "\n\n"
        f"WHAT SERGEI ENGAGED WITH (his button clicks — strongest signal):\n"
        + ("\n".join(engaged) or "(no clicks yet)") + "\n\n"
        f"RECENT MEMORY:\n{daily_log}\n\n"
        "Produce a WEEKLY PLAN as JSON with this exact shape:\n"
        "{\n"
        '  "week": "' + week_id + '",\n'
        '  "theme": "<one-line narrative theme for the week>",\n'
        '  "rationale": "<2-3 sentences why this theme now, tied to events/engagement>",\n'
        '  "topics": [\n'
        '    {"title": "<content topic>", "channel": "linkedin|x|blog|telegram", "angle": "<hook>", "ties_to": "<which preprint or event>"},\n'
        "    ... 5-7 topics, ordered by priority ...\n"
        "  ],\n"
        '  "outreach": ["<1-3 concrete people/orgs to reach this week and why>"],\n'
        '  "focus_metric": "<the ONE metric to move this week, e.g. citations, profile views, github stars>"\n'
        "}\n\n"
        "Be concrete and specific to Sergei's DeFi-security / RAG / quant work. "
        "Output ONLY the JSON."
    )
    out = run_llm("strategy", prompt, timeout=240)
    m = re.search(r"\{.*\}", out, re.DOTALL)
    if not m:
        print("strategist: LLM produced no JSON")
        return 1
    try:
        plan = json.loads(m.group(0))
    except Exception as e:
        print(f"strategist: bad JSON ({e})")
        return 1

    # Write topic_queue (drafters drain this)
    queue = {
        "week": plan.get("week", week_id),
        "theme": plan.get("theme", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topics": plan.get("topics", []),
    }
    TOPIC_QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2))

    # Write human-readable plan
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    plan_md = (
        f"# Weekly Plan — {plan.get('week', week_id)}\n\n"
        f"**Theme:** {plan.get('theme','')}\n\n"
        f"**Why now:** {plan.get('rationale','')}\n\n"
        f"**Focus metric:** {plan.get('focus_metric','')}\n\n"
        f"## Content topics (drain order)\n"
    )
    for i, t in enumerate(plan.get("topics", []), 1):
        plan_md += (f"{i}. **[{t.get('channel','?')}]** {t.get('title','')}\n"
                    f"   - angle: {t.get('angle','')}\n"
                    f"   - ties to: {t.get('ties_to','')}\n")
    plan_md += "\n## Outreach this week\n"
    for o in plan.get("outreach", []):
        plan_md += f"- {o}\n"
    plan_file = PLANS_DIR / f"{plan.get('week', week_id)}.md"
    plan_file.write_text(plan_md, encoding="utf-8")

    # Commit
    try:
        subprocess.run(["git", "-C", str(REPORTS), "add",
                        f"plans/{plan.get('week', week_id)}.md"], check=False)
        subprocess.run(
            ["git", "-C", str(REPORTS), "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m", f"strategist: weekly plan {plan.get('week', week_id)}",
             "--quiet"], check=False)
        subprocess.run(["git", "-C", str(REPORTS), "push", "--quiet"], check=False)
    except Exception:
        pass

    # Notify — single digestible summary, not a flood
    topics_preview = "\n".join(
        f"  {i}. [{t.get('channel','?')}] {t.get('title','')[:55]}"
        for i, t in enumerate(plan.get("topics", [])[:7], 1))
    summary = (
        f"🧭 *Weekly plan — {plan.get('week', week_id)}*\n\n"
        f"Theme: {plan.get('theme','')}\n"
        f"Focus metric: {plan.get('focus_metric','')}\n\n"
        f"Topics queued for the week:\n{topics_preview}\n\n"
        f"Full plan: https://github.com/SergeySolovyev/sergei-brand-agent-reports/"
        f"blob/main/plans/{plan.get('week', week_id)}.md"
    )
    subprocess.run(["/usr/local/bin/tg_send", summary], check=False)
    print(f"strategist: plan {plan.get('week', week_id)} written, "
          f"{len(plan.get('topics', []))} topics queued")
    return 0


if __name__ == "__main__":
    sys.exit(main())
