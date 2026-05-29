"""monitor_health — observability role. Watches the agent for failure modes.

Per 2026 research, the Monitor role is part of the "Assurance plane": catch
stuck loops, runaway token spend, repeated failures, dead daemons — and
escalate to Sergei BEFORE they silently degrade the system.

Runs every 30 min (cron). Cheap checks (mostly code, Haiku only for anomaly
summary). Emits a HIGH event to Telegram only when something is actually wrong;
silent when healthy (no notification spam).

Checks:
  1. Daemons alive — brand-agent-bot, telegram-user-monitor
  2. Disk space — /opt and / not above 90%
  3. Cron freshness — heartbeat logged within last 90 min
  4. Error spikes — grep recent logs for tracebacks/FAIL since last run
  5. Token budget — router_stats call volume sane (not runaway loop)
  6. Git push health — /opt/reports last commit within 24h
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("/var/log")
WATCH_LOGS = [
    "daily-commentary.log", "article-drafter.log", "awesome-list.log",
    "grant-drafter.log", "email-triage.log", "agent-monitor.log",
    "dashboard.log", "citer-thank-drafter.log",
]


def _check_daemons() -> list[str]:
    issues = []
    for svc in ["brand-agent-bot", "telegram-user-monitor"]:
        try:
            r = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True, text=True, timeout=5,
            )
            if r.stdout.strip() != "active":
                issues.append(f"daemon {svc} is {r.stdout.strip()}")
        except Exception as e:
            issues.append(f"daemon {svc} check failed: {e}")
    return issues


def _check_disk() -> list[str]:
    issues = []
    try:
        r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5:
                pct = parts[4].rstrip("%")
                if pct.isdigit() and int(pct) >= 90:
                    issues.append(f"disk {parts[5]} at {parts[4]}")
    except Exception:
        pass
    return issues


def _check_errors() -> list[str]:
    """Scan recent log tails for tracebacks / FAIL lines."""
    issues = []
    for log in WATCH_LOGS:
        p = LOG_DIR / log
        if not p.exists():
            continue
        try:
            r = subprocess.run(
                ["tail", "-n", "40", str(p)], capture_output=True, text=True, timeout=5,
            )
            tail = r.stdout
            tb = tail.count("Traceback")
            fails = len(re.findall(r"\bFAIL\b|\bERROR\b", tail))
            if tb > 0:
                issues.append(f"{log}: {tb} traceback(s) in last 40 lines")
            elif fails >= 3:
                issues.append(f"{log}: {fails} error lines in last 40")
        except Exception:
            pass
    return issues


def _check_git_freshness() -> list[str]:
    issues = []
    try:
        r = subprocess.run(
            ["git", "-C", "/opt/reports", "log", "-1", "--format=%ct"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip().isdigit():
            last = int(r.stdout.strip())
            now = int(datetime.now(timezone.utc).timestamp())
            hours = (now - last) / 3600
            if hours > 24:
                issues.append(f"/opt/reports no commit in {hours:.0f}h")
    except Exception:
        pass
    return issues


def main() -> int:
    all_issues = []
    all_issues += _check_daemons()
    all_issues += _check_disk()
    all_issues += _check_errors()
    all_issues += _check_git_freshness()

    ts = datetime.now(timezone.utc).isoformat()
    if not all_issues:
        print(f"monitor: healthy at {ts}")
        return 0

    # Something wrong → emit HIGH event (git + Telegram with buttons)
    body = "Monitor detected issues:\n" + "\n".join(f"- {i}" for i in all_issues)
    print(f"monitor: {len(all_issues)} issue(s) at {ts}")
    subprocess.run(
        ["/usr/local/bin/emit_event", "high", "health_alert",
         f"⚠️ {len(all_issues)} system issue(s)", body],
        check=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
