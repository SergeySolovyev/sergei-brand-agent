#!/opt/brand-agent/venv/bin/python3
"""dashboard — generate HTML cockpit aggregating all agent state.

Triggered:
  - on-demand: /dashboard Telegram command (bot spawns this)
  - event-driven: after each emit_event (post-emit hook)

Reads (10 sections):
  1. Header           — system status, refresh time
  2. Deadlines        — sqlite deadline_emit_log + hardcoded list
  3. Unblockers       — STATIC config — what Sergei must provide
  4. Drafts           — glob posts/, dms/, applications/, proposals/
  5. Calendar         — confirmed-attending.md + deadline dates
  6. Activity 24h     — audit/jsonl event counts by kind
  7. Autonomous       — crontab + systemctl status
  8. Quick links      — static URLs
  9. Pipeline state   — counts per stage
  10. Week ahead      — quick LLM-generated focus list

Output: /opt/reports/dashboard/index.html
Auto-commits to git for sharing via GitHub raw URL.
"""
import json
import re
import subprocess
import sqlite3
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

STATE_DB = Path("/root/.openclaw/agent_state.sqlite")
REPORTS_ROOT = Path("/opt/reports")
TRACKING_DIR = REPORTS_ROOT / "tracking"
INBOX_DIR = REPORTS_ROOT / "reports" / "inbox"
AUDIT_DIR = REPORTS_ROOT / "audit"
DASH_DIR = REPORTS_ROOT / "dashboard"
DASH_HTML = DASH_DIR / "index.html"

# Public mirror via GitHub Pages (sergeisolovev.com)
# Slug is random; only Sergei knows the URL. Bookmark and don't share.
SLUG_PATH = Path("/opt/brand-agent/secrets/cockpit_slug.txt")
PUBLIC_REPO = Path("/opt/sergeisolovev_com")
PUBLIC_REPO_GIT_URL = "github-sergeisolovevcom:SergeySolovyev/sergeisolovev.com.git"


# ─────────────────────────────────────────────────────────────────────
# Section data extractors
# ─────────────────────────────────────────────────────────────────────
def section_deadlines() -> list[dict]:
    """Hardcoded deadlines + dynamic days_remaining."""
    items = [
        ("2026-06-02", "Интернаука №20 submit",     "publication", "2,450 ₽"),
        ("2026-06-03", "W&B webinar",                "event",       "registered?"),
        ("2026-06-06", "Молодой учёный №22 pay",    "publication", "3,600 ₽"),
        ("2026-06-14", "Universum 6(147) confirm",  "publication", "3,818 ₽"),
        ("2026-06-15", "AIRI Summer School submit", "education",   "PDF+video"),
        ("2026-06-23", "CFA-8 Москва",               "conference",  "билет ✓"),
        ("2026-07-31", "МФТИ Master documents",     "education",   "RINC + CV + LoR"),
        ("2026-09-04", "ETHOnline 2026 starts",     "hackathon",   "apply pending"),
    ]
    today = date.today()
    out = []
    for d, title, cat, note in items:
        try:
            due = date.fromisoformat(d)
            days = (due - today).days
            if days < 0:
                continue
        except Exception:
            continue
        if days <= 3:
            severity = "critical"
        elif days <= 14:
            severity = "warning"
        elif days <= 30:
            severity = "watch"
        else:
            severity = "future"
        out.append({
            "date": d, "title": title, "category": cat,
            "note": note, "days": days, "severity": severity,
        })
    return sorted(out, key=lambda x: x["days"])


def section_unblockers() -> list[dict]:
    """What Sergei must provide. Detect 'done' state from secrets/env presence."""
    secrets = Path("/opt/brand-agent/secrets")
    env_path = Path("/opt/brand-agent/.env")
    env_text = env_path.read_text() if env_path.exists() else ""
    identity_path = Path("/opt/brand-agent/knowledge_base/identity.json")
    identity = {}
    if identity_path.exists():
        try:
            identity = json.loads(identity_path.read_text())
        except Exception:
            pass
    globals_ = identity.get("globals", {})
    profiles = identity.get("profiles", {})

    items = [
        {
            "priority": "🔴",
            "title": "LinkedIn li_at cookie",
            "unlocks": "3 drafters (citer DM, daily X-post, hackathon team-finding)",
            "done": "LINKEDIN_LI_AT" in env_text,
        },
        {
            "priority": "🟡",
            "title": "ORCID iD",
            "unlocks": "arXiv submissions, Wikidata, formal grants",
            "done": bool(globals_.get("orcid")),
        },
        {
            "priority": "🟡",
            "title": "TG channel @sergeisolovev_research",
            "unlocks": "daily_commentary auto-publish",
            "done": "TELEGRAM_PUBLIC_CHANNEL=@" in env_text,
        },
        {
            "priority": "🟢",
            "title": "HSE supervisor name + email",
            "unlocks": "all RU grants (РНФ/ФСИ/Бортник)",
            "done": bool(profiles.get("academic_hse", {}).get("supervisor")),
        },
        {
            "priority": "🟢",
            "title": "X (Twitter) auth_token cookie",
            "unlocks": "X posting + thread auto-publish",
            "done": "TWITTER_AUTH_TOKEN" in env_text,
        },
        {
            "priority": "⚪",
            "title": "Sessionize speaker account",
            "unlocks": "conference proposal auto-submit",
            "done": "SESSIONIZE_TOKEN" in env_text,
        },
        {
            "priority": "⚪",
            "title": "ETHOnline application Steps 2-5",
            "unlocks": "ETHOnline 2026 participation",
            "done": False,
        },
    ]
    return items


def section_drafts() -> dict:
    """Count drafts across /opt/reports/{posts,dms,applications,proposals}/."""
    out = {"posts": [], "dms": [], "applications": [], "proposals": []}
    for kind in out:
        d = REPORTS_ROOT / kind
        if not d.exists():
            continue
        for path in sorted(d.rglob("*.md"), reverse=True)[:10]:
            try:
                stat = path.stat()
                out[kind].append({
                    "path": str(path.relative_to(REPORTS_ROOT)),
                    "name": path.stem,
                    "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": stat.st_size // 1024,
                })
            except Exception:
                pass
    return out


def section_calendar() -> list[dict]:
    """Combine confirmed-attending.md + deadline dates into chronological list."""
    items = []
    # Add deadlines as calendar entries
    for d in section_deadlines():
        items.append({
            "date": d["date"], "title": d["title"],
            "kind": d["category"], "icon": "📅",
        })
    # Parse confirmed-attending.md for dated events
    confirmed = TRACKING_DIR / "confirmed-attending.md"
    if confirmed.exists():
        text = confirmed.read_text(encoding="utf-8")
        for m in re.finditer(r"^## (\d{4}-\d{2}-\d{2}) — (.+)$", text, re.MULTILINE):
            d, title = m.group(1), m.group(2)
            # Avoid duplicates from deadlines
            if not any(x["date"] == d and x["title"][:20] in title for x in items):
                items.append({
                    "date": d, "title": title,
                    "kind": "confirmed", "icon": "🎫",
                })
    return sorted(items, key=lambda x: x["date"])[:15]


def section_activity_24h() -> dict:
    """Count events by kind from audit/jsonl in last 24h."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).timestamp()
    counts = {}
    month = datetime.utcnow().strftime("%Y-%m")
    audit_file = AUDIT_DIR / month / "events.jsonl"
    if not audit_file.exists():
        return counts
    try:
        for line in audit_file.read_text().splitlines():
            try:
                ev = json.loads(line)
                if ev.get("unix", 0) >= cutoff:
                    k = ev.get("kind", "unknown")
                    counts[k] = counts.get(k, 0) + 1
            except Exception:
                pass
    except Exception:
        pass
    return counts


def section_autonomous() -> dict:
    """Inventory cron jobs + systemd daemons + emit_event hooks."""
    out = {"cron": [], "daemons": [], "hooks": []}
    try:
        r = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract command part
                    parts = line.split(None, 5)
                    if len(parts) >= 6:
                        cmd = Path(parts[5].split()[0]).name
                        schedule = " ".join(parts[:5])
                        out["cron"].append({"schedule": schedule, "cmd": cmd})
    except Exception:
        pass

    for svc in ["brand-agent-bot", "telegram-user-monitor"]:
        try:
            r = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True, text=True, timeout=5,
            )
            out["daemons"].append({
                "name": svc, "status": r.stdout.strip(),
            })
        except Exception:
            out["daemons"].append({"name": svc, "status": "unknown"})

    # Hooks — parse emit_event tail
    try:
        emit_text = Path("/usr/local/bin/emit_event").read_text()
        for m in re.finditer(r'KIND" == "(\w+)".+?nohup .+/(\w+)\.py', emit_text, re.DOTALL):
            out["hooks"].append({"trigger_kind": m.group(1), "drafter": m.group(2)})
    except Exception:
        pass

    return out


def section_pipeline() -> list[dict]:
    """Funnel state: discovered → drafted → review → submitted."""
    drafts = section_drafts()
    # Crude pipeline counts
    return [
        {"stage": "Discovered (inbox)",       "count": len(list(INBOX_DIR.glob("*.md"))) if INBOX_DIR.exists() else 0, "color": "#888"},
        {"stage": "Drafted (post/dm/app/prop)", "count": sum(len(v) for v in drafts.values()),                          "color": "#88c"},
        {"stage": "Awaiting your review",      "count": _count_pending_drafts(),                                          "color": "#fa0"},
        {"stage": "Submitted/Published",      "count": _count_submitted(),                                                  "color": "#0a0"},
    ]


def _count_pending_drafts() -> int:
    """Drafts not yet reviewed (no decided_at in SQLite drafts table)."""
    try:
        with sqlite3.connect(STATE_DB) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM drafts WHERE status='pending'"
            ).fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


def _count_submitted() -> int:
    """Drafts marked sent in SQLite."""
    try:
        with sqlite3.connect(STATE_DB) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM drafts WHERE status='sent'"
            ).fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


def section_week_ahead() -> str:
    """LLM-quick generated week focus list. ~5 bullets."""
    deadlines = section_deadlines()
    urgent = [d for d in deadlines if d["days"] <= 14]
    urgent_str = "\n".join(
        f"  - {d['date']} ({d['days']}d) — {d['title']}: {d['note']}"
        for d in urgent
    )
    prompt = (
        "You are the Strategist for Sergei Solovev's brand agent. Given current "
        "deadlines, produce a 5-bullet week-ahead focus list. Be concrete. "
        "Each bullet: 'Day → Specific action'. No fluff.\n\n"
        f"Urgent (next 14d):\n{urgent_str}\n\n"
        "Today: " + str(date.today()) + "\n\n"
        "Output ONLY 5 bullets. No header."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-haiku-4-5", prompt],
            capture_output=True, text=True, timeout=45,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return "(LLM unavailable)"


# ─────────────────────────────────────────────────────────────────────
# HTML renderer
# ─────────────────────────────────────────────────────────────────────
def html_escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\n", "<br>"))


SEVERITY_COLORS = {
    "critical": "#ff4444",
    "warning":  "#ffa500",
    "watch":    "#88c",
    "future":   "#888",
}


def render_html() -> str:
    deadlines = section_deadlines()
    unblockers = section_unblockers()
    drafts = section_drafts()
    calendar = section_calendar()
    activity = section_activity_24h()
    autonomous = section_autonomous()
    pipeline = section_pipeline()
    week_ahead = section_week_ahead()

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    daemon_ok = all(d["status"] == "active" for d in autonomous["daemons"])
    status_emoji = "🟢" if daemon_ok else "🟡"

    html = f"""<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive,nosnippet">
<meta name="googlebot" content="noindex,nofollow,noarchive,nosnippet">
<meta name="referrer" content="no-referrer">
<title>🚀 Sergei Brand Agent — Mission Control</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
          background: #0e1117; color: #c9d1d9; margin: 0; padding: 16px;
          line-height: 1.5; max-width: 1100px; margin: 0 auto; }}
  h1 {{ font-size: 1.6em; margin: 0 0 8px; }}
  h2 {{ font-size: 1.1em; margin: 24px 0 8px; padding-bottom: 4px;
       border-bottom: 1px solid #30363d; color: #f0f6fc; }}
  .card {{ background: #161b22; border: 1px solid #30363d;
           border-radius: 6px; padding: 12px 16px; margin: 8px 0; }}
  .deadline {{ display: flex; justify-content: space-between;
               padding: 6px 0; border-bottom: 1px dashed #30363d; }}
  .days {{ font-weight: bold; padding: 2px 8px; border-radius: 12px;
           color: #fff; font-size: 0.85em; min-width: 60px; text-align: center; }}
  .meta {{ color: #8b949e; font-size: 0.85em; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0; }}
  td, th {{ padding: 4px 8px; text-align: left;
            border-bottom: 1px solid #21262d; font-size: 0.92em; }}
  th {{ color: #8b949e; font-weight: normal; }}
  .pipeline-bar {{ display: flex; height: 32px; border-radius: 4px;
                   overflow: hidden; margin: 8px 0; }}
  .pipeline-bar > div {{ padding: 4px 12px; color: #fff;
                          display: flex; align-items: center; font-size: 0.85em; }}
  .check {{ color: #56d364; }}
  .blocked {{ color: #ff4444; }}
  pre {{ background: #0a0d12; padding: 12px; border-radius: 4px;
         overflow-x: auto; color: #c9d1d9; font-size: 0.85em; }}
  a {{ color: #58a6ff; }}
  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  @media (max-width: 700px) {{ .grid2 {{ grid-template-columns: 1fr; }} }}
</style></head><body>

<h1>🚀 Sergei Brand Agent — Mission Control</h1>
<div class="meta">
  Дата: <b>{date.today().strftime('%d %B %Y')}</b> ·
  Refresh: <b>{now_iso}</b> ·
  Status: {status_emoji} <b>{'OPERATIONAL' if daemon_ok else 'DEGRADED'}</b>
</div>

<h2>⏰ Критические deadlines</h2>
<div class="card">
"""
    for d in deadlines:
        c = SEVERITY_COLORS[d["severity"]]
        days_label = "🔥 СЕГОДНЯ" if d["days"] == 0 else f"{d['days']}d"
        html += (
            f'<div class="deadline">'
            f'  <div><b>{html_escape(d["title"])}</b> '
            f'<span class="meta">· {html_escape(d["category"])} · {html_escape(d["note"])}</span></div>'
            f'  <span class="days" style="background:{c}">{days_label}</span>'
            f'</div>'
        )
    html += "</div>"

    # Unblockers + Pipeline grid
    html += '<div class="grid2"><div>'
    html += "<h2>🎯 Что ждёт от тебя</h2><div class='card'>"
    for u in unblockers:
        mark = '<span class="check">✓ done</span>' if u["done"] else '<span class="blocked">pending</span>'
        html += (
            f'<div style="padding:4px 0">'
            f'{u["priority"]} <b>{html_escape(u["title"])}</b> — {mark}<br>'
            f'<span class="meta">→ {html_escape(u["unlocks"])}</span>'
            f'</div>'
        )
    html += "</div></div><div>"

    html += "<h2>📊 Pipeline state</h2><div class='card'>"
    total = max(sum(p["count"] for p in pipeline), 1)
    html += '<div class="pipeline-bar">'
    for p in pipeline:
        width_pct = max(p["count"] / total * 100, 8 if p["count"] else 0)
        if p["count"]:
            html += (
                f'<div style="background:{p["color"]};width:{width_pct}%">'
                f'{html_escape(p["stage"])}: <b>{p["count"]}</b>'
                f'</div>'
            )
    html += "</div>"
    html += "<table><tr><th>Stage</th><th>Count</th></tr>"
    for p in pipeline:
        html += f'<tr><td>{html_escape(p["stage"])}</td><td>{p["count"]}</td></tr>'
    html += "</table></div></div></div>"

    # Drafts table
    html += "<h2>📋 Drafts awaiting review</h2><div class='card'>"
    total_drafts = sum(len(v) for v in drafts.values())
    if total_drafts == 0:
        html += "<i>No drafts yet. Daily commentary runs at 10:00 UTC. Hooks fire on grant/citer/CFP events.</i>"
    else:
        for kind, items in drafts.items():
            if not items:
                continue
            icon = {"posts": "📝", "dms": "💬", "applications": "📋", "proposals": "🎤"}.get(kind, "📄")
            html += f"<h3 style='margin:8px 0 4px;color:#8b949e;font-size:0.95em'>{icon} {kind.title()}</h3>"
            html += "<table>"
            for it in items[:5]:
                html += (
                    f'<tr>'
                    f'<td><a href="https://github.com/SergeySolovyev/sergei-brand-agent-reports/blob/main/{it["path"]}">{html_escape(it["name"])}</a></td>'
                    f'<td class="meta">{it["mtime"]}</td>'
                    f'<td class="meta">{it["size_kb"]} KB</td>'
                    f'</tr>'
                )
            html += "</table>"
    html += "</div>"

    # Calendar
    html += "<h2>🗓 Calendar</h2><div class='card'><table>"
    for c in calendar:
        html += (
            f'<tr><td>{html_escape(c["icon"])}</td>'
            f'<td><b>{html_escape(c["date"])}</b></td>'
            f'<td>{html_escape(c["title"])}</td>'
            f'<td class="meta">{html_escape(c["kind"])}</td></tr>'
        )
    html += "</table></div>"

    # Activity 24h
    html += "<h2>📈 Activity (last 24h)</h2><div class='card'>"
    if activity:
        for k, v in sorted(activity.items(), key=lambda x: -x[1]):
            html += f'<div>+{v} <b>{html_escape(k)}</b></div>'
    else:
        html += '<i>No events in last 24h.</i>'
    html += "</div>"

    # Week ahead
    html += "<h2>🎯 Неделя вперёд (Strategist plan)</h2><div class='card'>"
    html += f"<pre>{html_escape(week_ahead)}</pre>"
    html += "</div>"

    # Autonomous systems
    html += "<h2>🟢 Автономно работает</h2><div class='card'>"
    html += f"<b>Cron jobs ({len(autonomous['cron'])})</b><table>"
    for c in autonomous["cron"]:
        html += f"<tr><td><code>{html_escape(c['schedule'])}</code></td><td>{html_escape(c['cmd'])}</td></tr>"
    html += "</table>"
    html += f"<br><b>Daemons ({len(autonomous['daemons'])})</b><table>"
    for d in autonomous["daemons"]:
        color = "#56d364" if d["status"] == "active" else "#ff4444"
        html += f'<tr><td>{html_escape(d["name"])}</td><td style="color:{color}">●{html_escape(d["status"])}</td></tr>'
    html += "</table>"
    html += f"<br><b>Emit hooks ({len(autonomous['hooks'])})</b><table>"
    for h in autonomous["hooks"]:
        html += f"<tr><td>{html_escape(h['trigger_kind'])} →</td><td>{html_escape(h['drafter'])}</td></tr>"
    html += "</table></div>"

    # Quick links
    html += """<h2>🔗 Quick links</h2><div class='card'>
<a href="https://github.com/SergeySolovyev/sergei-brand-agent-reports/tree/main/posts">📝 Posts</a> ·
<a href="https://github.com/SergeySolovyev/sergei-brand-agent-reports/tree/main/applications">📋 Applications</a> ·
<a href="https://github.com/SergeySolovyev/sergei-brand-agent-reports/tree/main/dms">💬 DMs</a> ·
<a href="https://github.com/SergeySolovyev/sergei-brand-agent-reports/tree/main/proposals">🎤 Proposals</a> ·
<a href="https://github.com/SergeySolovyev/sergei-brand-agent-reports/tree/main/tracking">🎫 Tracking</a> ·
<a href="https://github.com/SergeySolovyev/sergei-brand-agent-reports/blob/main/reports/daily/">📰 Daily reports</a>
</div>"""

    html += f"<div class='meta' style='margin-top:24px;text-align:center'>Generated by dashboard.py @ {now_iso}</div>"
    html += "</body></html>"
    return html


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────
def _publish_to_public_repo(html: str) -> None:
    """Dual-push to sergeisolovev_build (public GitHub Pages) at random slug.

    Silently no-ops if deploy key not yet added or repo not cloned. This
    keeps the on-emit hook resilient: dashboard always writes to the
    nginx-served local path; public mirror is best-effort.
    """
    if not SLUG_PATH.exists():
        return
    slug = SLUG_PATH.read_text().strip()
    if not slug:
        return

    # Lazy clone on first use
    if not (PUBLIC_REPO / ".git").exists():
        try:
            r = subprocess.run(
                ["git", "clone", PUBLIC_REPO_GIT_URL, str(PUBLIC_REPO)],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                # Deploy key not added yet — skip silently
                return
        except Exception:
            return

    # Write HTML at random slug path
    out_dir = PUBLIC_REPO / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    # Defensive robots.txt — block crawlers even if meta missed
    robots = PUBLIC_REPO / "robots.txt"
    robots_text = robots.read_text() if robots.exists() else ""
    disallow_line = f"Disallow: /{slug}/"
    if disallow_line not in robots_text:
        # Append a User-agent: * Disallow block if not present
        if "User-agent: *" not in robots_text:
            robots_text += "\nUser-agent: *\n"
        robots_text += disallow_line + "\n"
        robots.write_text(robots_text)

    try:
        subprocess.run(
            ["git", "-C", str(PUBLIC_REPO), "pull", "--quiet", "--rebase"],
            check=False, timeout=15,
        )
        subprocess.run(
            ["git", "-C", str(PUBLIC_REPO), "add",
             f"{slug}/index.html", "robots.txt"],
            check=False, timeout=10,
        )
        subprocess.run(
            ["git", "-C", str(PUBLIC_REPO),
             "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m",
             f"cockpit: refresh {datetime.utcnow().strftime('%H:%M')}",
             "--quiet"], check=False, timeout=10,
        )
        subprocess.run(
            ["git", "-C", str(PUBLIC_REPO), "push", "--quiet"],
            check=False, timeout=20,
        )
    except Exception as e:
        print(f"public mirror push warning: {e}")


def main() -> int:
    DASH_DIR.mkdir(parents=True, exist_ok=True)
    html = render_html()
    DASH_HTML.write_text(html, encoding="utf-8")
    print(f"✓ dashboard rendered: {DASH_HTML}")

    # Mirror to public sergeisolovev_build (GitHub Pages)
    _publish_to_public_repo(html)

    # git commit + push private reports repo (audit trail)
    try:
        subprocess.run(
            ["git", "-C", str(REPORTS_ROOT), "add", "dashboard/index.html"],
            check=False, timeout=10,
        )
        subprocess.run(
            ["git", "-C", str(REPORTS_ROOT), "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m",
             f"dashboard: refresh {datetime.utcnow().strftime('%H:%M')}",
             "--quiet"], check=False, timeout=10,
        )
        subprocess.run(
            ["git", "-C", str(REPORTS_ROOT), "push", "--quiet"],
            check=False, timeout=15,
        )
    except Exception as e:
        print(f"git op warning: {e}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
