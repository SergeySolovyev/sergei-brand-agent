"""
orchestrator.py — sergei-brand-agent main loop

The Harness layer of the three-layer architecture (Sandbox + Trace + Loop).
Wires together personas + skills + tools per Anthropic's Managed Agents
pattern.

Run modes:
  python orchestrator.py once          # single pass through all due skills
  python orchestrator.py daemon        # long-running, polls every 60s
  python orchestrator.py skill <name>  # run one named skill (testing)
  python orchestrator.py status        # print current state + pending approvals
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent
STATE_DB = REPO_ROOT / "data" / "state.sqlite"
SKILLS_DIR = REPO_ROOT / "skills"
DRAFTS_DIR = REPO_ROOT / "data" / "drafts"
TRACES_DIR = REPO_ROOT / "data" / "traces"

# ---------------------------------------------------------------------------
# Logging — JSONL to traces/ + stdout
# ---------------------------------------------------------------------------
class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for key in ("session", "skill", "tier", "decision"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    trace_file = TRACES_DIR / f"{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"

    logger = logging.getLogger("orchestrator")
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(trace_file, encoding="utf-8")
    file_handler.setFormatter(JsonLineFormatter())
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-5s %(name)s | %(message)s")
    )
    logger.addHandler(console_handler)

    return logger


log = setup_logging()


# ---------------------------------------------------------------------------
# State store — SQLite as event bus + memory
# ---------------------------------------------------------------------------
SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY,
      source TEXT NOT NULL,
      kind TEXT NOT NULL,
      subject TEXT,
      severity TEXT CHECK(severity IN ('low','medium','high','critical')),
      tier INTEGER,
      ts TEXT NOT NULL,
      raw TEXT,
      handled_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS drafts (
      draft_path TEXT PRIMARY KEY,
      channel TEXT,
      topic TEXT,
      created_at TEXT,
      composer_concerns TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS critic_verdicts (
      id INTEGER PRIMARY KEY,
      draft_path TEXT NOT NULL,
      verdict TEXT CHECK(verdict IN ('PASS','REVISE','REJECT','PENDING')),
      reasons TEXT,
      ts TEXT NOT NULL,
      round INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS approvals (
      id INTEGER PRIMARY KEY,
      draft_path TEXT NOT NULL,
      verdict TEXT CHECK(verdict IN ('approved','rejected')),
      approver TEXT,
      ts TEXT NOT NULL,
      note TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS published (
      id INTEGER PRIMARY KEY,
      draft_path TEXT,
      channel TEXT,
      message_id TEXT,
      post_url TEXT,
      screenshot_path TEXT,
      approver TEXT,
      published_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS grant_candidates (
      url TEXT PRIMARY KEY,
      sponsor TEXT,
      title TEXT,
      deadline TEXT,
      match_score REAL,
      required_docs_json TEXT,
      raw_json TEXT,
      first_seen TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS hackathon_events (
      url TEXT PRIMARY KEY,
      name TEXT,
      organizer TEXT,
      start_date TEXT,
      alignment_score REAL,
      prize_pool_usd INTEGER,
      raw_json TEXT,
      first_seen TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cfp_calls (
      url TEXT PRIMARY KEY,
      title TEXT,
      venue TEXT,
      deadline TEXT,
      rank TEXT,
      match_score REAL,
      raw_json TEXT,
      first_seen TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS weekly_metrics_snapshot (
      captured_at TEXT PRIMARY KEY,
      openalex_cited_by INTEGER,
      github_total_stars INTEGER,
      figshare_downloads INTEGER,
      linkedin_followers INTEGER,
      tg_subscribers INTEGER,
      site_visitors INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_state (
      key TEXT PRIMARY KEY,
      value TEXT,
      updated_at TEXT
    )
    """,
    # ── GBrain-inspired pattern memory (cross-session learning) ─────────────
    """
    CREATE TABLE IF NOT EXISTS patterns (
      id INTEGER PRIMARY KEY,
      pattern_type TEXT CHECK(pattern_type IN ('voice','structure','taboo','timing')),
      title TEXT,
      description TEXT,
      applies_when TEXT,
      anti_example TEXT,
      exemplar TEXT,
      tags_json TEXT,
      source_draft_path TEXT,
      outcome TEXT CHECK(outcome IN ('strong_signal','weak_signal','rejected','neutral')),
      confidence REAL DEFAULT 0.5,
      created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pattern_usage (
      pattern_id INTEGER REFERENCES patterns(id) ON DELETE CASCADE,
      used_by_skill TEXT,
      used_at TEXT,
      use_count INTEGER DEFAULT 0,
      PRIMARY KEY (pattern_id, used_by_skill)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mentions (
      mention_url TEXT PRIMARY KEY,
      platform TEXT,
      author TEXT,
      text_snippet TEXT,
      signal_strength TEXT CHECK(signal_strength IN ('low','medium','high')),
      ts TEXT,
      first_seen TEXT,
      replied_at TEXT
    )
    """,
]


@contextmanager
def db():
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(STATE_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        for stmt in SCHEMA:
            conn.execute(stmt)


# ---------------------------------------------------------------------------
# Skill loading & dispatch
# ---------------------------------------------------------------------------
def load_skill_index() -> dict[str, Path]:
    """Discover all *.yaml under skills/ and index by `name`."""
    index: dict[str, Path] = {}
    for path in SKILLS_DIR.rglob("*.yaml"):
        with path.open(encoding="utf-8") as f:
            try:
                spec = yaml.safe_load(f)
            except yaml.YAMLError as e:
                log.error(f"Invalid YAML in {path}: {e}")
                continue
        if not isinstance(spec, dict) or "name" not in spec:
            continue
        name = spec["name"]
        if name in index:
            log.warning(f"Duplicate skill name '{name}' at {path}")
        index[name] = path
    log.info(f"Loaded {len(index)} skills")
    return index


def check_guards(spec: dict) -> tuple[bool, str]:
    """Return (allowed, reason). For now: only emergency_pause is read from DB."""
    with db() as conn:
        row = conn.execute(
            "SELECT value FROM agent_state WHERE key = 'emergency_pause'"
        ).fetchone()
    if row and row["value"] == "true":
        return False, "emergency_pause=true in agent_state"
    return True, ""


def dispatch_skill(name: str, index: dict[str, Path], inputs: dict | None = None) -> dict:
    """
    Execute a single named skill.

    NOTE: This is the *harness shim*. Real procedure execution lives in the
    agent runtime (Hermes Agent uses its own executor). This implementation
    is a Python fallback that handles the most common action types when
    Hermes Agent isn't running (e.g. local testing).

    For production: register skills with Hermes Agent
    via `hermes skill add skills/<category>/<name>.yaml`.
    """
    if name not in index:
        raise KeyError(f"Unknown skill: {name}")

    spec_path = index[name]
    with spec_path.open(encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    allowed, reason = check_guards(spec)
    if not allowed:
        log.warning(f"Skill {name} blocked by guard: {reason}")
        return {"skipped": True, "reason": reason}

    session_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{name}"
    log.info(
        f"Dispatching skill {name}",
        extra={"session": session_id, "skill": name, "tier": spec.get("tier", 1)},
    )

    # Defer to Hermes runtime when present
    hermes = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
    if Path(hermes).is_dir() and (Path(hermes) / "bin" / "hermes").exists():
        import subprocess

        result = subprocess.run(
            [
                str(Path(hermes) / "bin" / "hermes"),
                "skill",
                "run",
                name,
                "--inputs",
                json.dumps(inputs or {}),
            ],
            capture_output=True,
            text=True,
            timeout=spec.get("estimated_duration_seconds", 300) * 3,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "session": session_id,
        }

    # Fallback: log-only mode
    log.warning(
        f"Hermes runtime not found; skill {name} would have executed in dispatched mode"
    )
    return {"dry_run": True, "spec_path": str(spec_path), "session": session_id}


# ---------------------------------------------------------------------------
# Scheduler — read cron expressions from skill specs, fire due ones
# ---------------------------------------------------------------------------
def parse_cron_due(cron_expr: str, last_run: datetime | None) -> bool:
    """
    Minimal cron evaluation: fire when last_run is before the most recent
    match of the cron expression. Uses croniter if available; otherwise
    falls back to a 1-hour heuristic.
    """
    try:
        from croniter import croniter
    except ImportError:
        return last_run is None or (datetime.now(timezone.utc) - last_run) > timedelta(hours=1)

    now = datetime.now(timezone.utc)
    base = last_run or (now - timedelta(days=2))
    itr = croniter(cron_expr, base)
    next_fire = itr.get_next(datetime)
    return next_fire <= now


def get_last_run(skill_name: str) -> datetime | None:
    with db() as conn:
        row = conn.execute(
            "SELECT value FROM agent_state WHERE key = ?",
            (f"last_run:{skill_name}",),
        ).fetchone()
    if not row:
        return None
    try:
        return datetime.fromisoformat(row["value"])
    except (TypeError, ValueError):
        return None


def set_last_run(skill_name: str, ts: datetime) -> None:
    with db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO agent_state (key, value, updated_at)
            VALUES (?, ?, ?)
            """,
            (f"last_run:{skill_name}", ts.isoformat(), datetime.now(timezone.utc).isoformat()),
        )


def run_once(index: dict[str, Path]) -> dict[str, Any]:
    """Run all skills whose cron expression is due."""
    results: dict[str, Any] = {}
    for name, path in index.items():
        with path.open(encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        cron_expr = spec.get("cron")
        if not cron_expr:
            continue
        last = get_last_run(name)
        if not parse_cron_due(cron_expr, last):
            continue
        try:
            results[name] = dispatch_skill(name, index)
            set_last_run(name, datetime.now(timezone.utc))
        except Exception as exc:
            log.exception(f"Skill {name} crashed: {exc}")
            results[name] = {"error": str(exc)}
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def cmd_once(args: argparse.Namespace) -> int:
    init_db()
    index = load_skill_index()
    results = run_once(index)
    for skill_name, outcome in results.items():
        print(f"{skill_name}: {outcome}")
    return 0


def cmd_daemon(args: argparse.Namespace) -> int:
    init_db()
    index = load_skill_index()
    log.info("Daemon mode: polling every 60s")
    try:
        while True:
            run_once(index)
            time.sleep(60)
    except KeyboardInterrupt:
        log.info("Daemon stopped")
        return 0


def cmd_skill(args: argparse.Namespace) -> int:
    init_db()
    index = load_skill_index()
    inputs = json.loads(args.inputs) if args.inputs else {}
    result = dispatch_skill(args.skill_name, index, inputs)
    print(json.dumps(result, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    init_db()
    with db() as conn:
        events = conn.execute(
            "SELECT source, kind, subject, severity, ts FROM events "
            "WHERE ts >= datetime('now', '-24 hours') ORDER BY ts DESC LIMIT 20"
        ).fetchall()
        pending = conn.execute(
            """
            SELECT d.draft_path, d.channel, d.topic, cv.verdict
            FROM drafts d
            LEFT JOIN critic_verdicts cv ON d.draft_path = cv.draft_path
            LEFT JOIN approvals a ON d.draft_path = a.draft_path
            WHERE a.id IS NULL AND cv.verdict = 'PASS'
            ORDER BY d.created_at DESC
            LIMIT 10
            """
        ).fetchall()
        paused = conn.execute(
            "SELECT value FROM agent_state WHERE key = 'emergency_pause'"
        ).fetchone()

    print("=" * 60)
    print(f"Agent state    : {'PAUSED' if paused and paused['value'] == 'true' else 'RUNNING'}")
    print(f"Events (24h)   : {len(events)}")
    print(f"Pending approve: {len(pending)}")
    print("=" * 60)
    print("\nRecent events:")
    for e in events:
        print(f"  [{e['severity'][0].upper()}] {e['ts'][:19]} {e['source']:>10} | {e['kind']} | {e['subject']}")
    print("\nDrafts awaiting /approve:")
    for d in pending:
        print(f"  {d['channel']:>10} | {d['topic']} | {d['draft_path']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("once", help="Single pass through due skills").set_defaults(func=cmd_once)
    sub.add_parser("daemon", help="Long-running poller").set_defaults(func=cmd_daemon)
    sub.add_parser("status", help="Print state + pending approvals").set_defaults(func=cmd_status)

    p = sub.add_parser("skill", help="Run one skill by name")
    p.add_argument("skill_name")
    p.add_argument("--inputs", help="JSON-encoded input dict", default=None)
    p.set_defaults(func=cmd_skill)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
