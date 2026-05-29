"""model_router — central model-tier router for cost economy.

Based on Anthropic "Building Effective Agents" Routing pattern + 2026 routing
research: route by task type AND difficulty to the cheapest sufficient model.

Pricing (per 1M tokens in/out, May 2026):
  Opus 4.8   $5 / $25   — strategy, orchestration, flagship, final grant gate
  Sonnet 4.6 $3 / $15   — drafting, critique, verification, research subagents
  Haiku 4.5  $1 / $5    — triage, classification, memory writes, scheduling

Measured: 3-tier routing ≈ 51% cheaper than uniform-Opus; routing broadly
saves 40-70%. Token usage explains ~80% of agent cost variance, so who-uses-
what is the dominant lever.

The 20% break-even rule: if a Haiku task needs Sonnet-level correction >20%
of the time, promote that task class to Sonnet (the re-prompt cost eats the
3x price advantage). Tracked in /root/.openclaw/router_stats.sqlite.

Usage:
    from model_router import model_for, run_llm

    model = model_for("triage")          # → claude-haiku-4-5
    out   = run_llm("draft", prompt)     # picks sonnet, calls claude-cli, returns text
"""
from __future__ import annotations

import subprocess
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Model tier identifiers (claude-cli model names)
OPUS = "claude-opus-4-8"
SONNET = "claude-sonnet-4-6"
HAIKU = "claude-haiku-4-5"

# Task class → tier. The heart of the economy policy.
TASK_MODEL = {
    # ── Haiku tier: pattern-matching, classification, no deep reasoning ──
    "triage":          HAIKU,   # inbound email/TG classification
    "classify":        HAIKU,
    "route":           HAIKU,
    "topic_fit":       HAIKU,   # is awesome-list relevant?
    "memory_write":    HAIKU,   # memory-keeper consolidation
    "memory_consolidate": HAIKU,
    "schedule":        HAIKU,
    "tag":             HAIKU,
    "week_ahead":      HAIKU,   # short planning bullets
    "monitor":         HAIKU,   # health/anomaly checks

    # ── Sonnet tier: anything that ships to a human ──
    "draft":           SONNET,  # composer: posts, replies
    "draft_reply":     SONNET,
    "critique":        SONNET,  # critic
    "verify":          SONNET,  # verifier / citation check
    "research":        SONNET,  # researcher subagents
    "article":         SONNET,  # platform articles
    "commentary":      SONNET,
    "summarize":       SONNET,
    "pr_draft":        SONNET,  # awesome-list PR body

    # ── Opus tier: cross-cutting strategy, irreversible/high-stakes ──
    "strategy":        OPUS,    # weekly orchestration plan
    "grant_application": OPUS,  # high-stakes, irreversible deadline
    "flagship":        OPUS,    # cornerstone blog / keynote abstract
    "orchestrate":     OPUS,
}

DEFAULT_TIER = SONNET  # unknown task → safe middle
STATS_DB = Path("/root/.openclaw/router_stats.sqlite")


def model_for(task_class: str) -> str:
    """Return the model id for a task class."""
    return TASK_MODEL.get(task_class, DEFAULT_TIER)


def _record(task_class: str, model: str, ok: bool, corrected: bool = False) -> None:
    """Track usage for the 20% break-even rule. Cheap, fire-and-forget."""
    try:
        STATS_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(STATS_DB)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS router_calls "
            "(ts TEXT, task_class TEXT, model TEXT, ok INTEGER, corrected INTEGER)"
        )
        conn.execute(
            "INSERT INTO router_calls VALUES (?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), task_class, model,
             int(ok), int(corrected)),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def run_llm(task_class: str, prompt: str, timeout: int = 180,
            model_override: str | None = None) -> str:
    """Route a prompt to the right model tier and return text output.

    Returns "" on failure (callers should handle empty gracefully).
    """
    model = model_override or model_for(task_class)
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", model, prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        ok = r.returncode == 0
        _record(task_class, model, ok)
        return r.stdout.strip() if ok else ""
    except Exception as e:
        _record(task_class, model, False)
        print(f"run_llm({task_class}, {model}) error: {e}")
        return ""


def break_even_report() -> dict:
    """Compute per-task correction rates — flag Haiku tasks exceeding 20%.

    A high correction rate means the cheap tier is too cheap for that task;
    the router should promote it. Surfaced in the dashboard.
    """
    if not STATS_DB.exists():
        return {}
    try:
        conn = sqlite3.connect(STATS_DB)
        rows = conn.execute(
            "SELECT task_class, model, "
            "  COUNT(*) AS n, "
            "  SUM(corrected) AS corr "
            "FROM router_calls GROUP BY task_class, model"
        ).fetchall()
        conn.close()
        out = {}
        for task_class, model, n, corr in rows:
            rate = (corr or 0) / n if n else 0
            out[task_class] = {
                "model": model, "calls": n,
                "correction_rate": round(rate, 3),
                "promote": bool(model == HAIKU and rate > 0.20),
            }
        return out
    except Exception:
        return {}


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        print(json.dumps(break_even_report(), indent=2))
    else:
        # Print the routing table
        print("Task class → model tier:")
        for tc, m in sorted(TASK_MODEL.items(), key=lambda x: x[1]):
            tier = {OPUS: "OPUS", SONNET: "SONNET", HAIKU: "HAIKU"}[m]
            print(f"  {tc:22} → {tier}")
