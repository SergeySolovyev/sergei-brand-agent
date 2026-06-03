"""post_guard — anti-ban safety layer for ALL social posting (X, LinkedIn).

Built from 2025-2026 research on what actually gets X accounts banned. The key
finding: bans come from VELOCITY (burst-posting), duplicate content, and bot-
signature timing — NOT from low daily volume. Sergei's prior account was banned
for non-stop burst posting. This module makes that impossible.

Every poster MUST call guard_check() before posting and record_post() after.

Rules encoded (the "DO / NEVER" list):
  - Daily cap: 6 posts/platform/day (target is 1-4)
  - Min gap 90 min between posts + random jitter ±30 min
  - Rolling 30-min ceiling: max 3 posts (hard wall is ~50; we stay 1/15th)
  - Dedup: reject text >80% similar to anything posted in last 14 days
  - Daytime window only (07:00-23:00 MSK) — natural overnight gaps
  - Warm-up: first 14 days after activation → 2 posts/day, no links
  - Backoff: on a 226/challenge/ratelimit, freeze the platform for 6h
  - Hashtag cap (2) + link cap (3/day) checked on content

State: /root/.openclaw/post_guard.sqlite
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from pathlib import Path

DB = Path("/root/.openclaw/post_guard.sqlite")
# Activation date — warm-up window counts from here. Set to first deploy.
WARMUP_START = datetime(2026, 6, 3, tzinfo=timezone.utc)
WARMUP_DAYS = 14

DAILY_CAP = 6
MIN_GAP_MIN = 90
JITTER_MIN = 30
ROLLING_WINDOW_MIN = 30
ROLLING_MAX = 3
DEDUP_DAYS = 14
DEDUP_SIM = 0.80
LINKS_PER_DAY = 3
HASHTAG_MAX = 2
DAY_START_H = 7   # MSK
DAY_END_H = 23
BACKOFF_HOURS = 6


def _conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS posts "
              "(platform TEXT, text TEXT, ts TEXT, had_link INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS backoff "
              "(platform TEXT PRIMARY KEY, until TEXT, reason TEXT)")
    return c


def _now_msk() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=3)


def in_warmup() -> bool:
    return (datetime.now(timezone.utc) - WARMUP_START).days < WARMUP_DAYS


def set_backoff(platform: str, hours: int = BACKOFF_HOURS, reason: str = "") -> None:
    c = _conn()
    until = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
    c.execute("INSERT OR REPLACE INTO backoff VALUES (?,?,?)",
              (platform, until, reason))
    c.commit()
    c.close()


def _recent(c, platform: str, minutes: int):
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    return c.execute(
        "SELECT text, ts, had_link FROM posts WHERE platform=? AND ts>=?",
        (platform, cutoff)).fetchall()


def guard_check(platform: str, text: str) -> tuple[bool, str]:
    """Return (allowed, reason). Call BEFORE posting. Reason explains a block."""
    c = _conn()
    try:
        now = datetime.now(timezone.utc)

        # 0. Backoff freeze (after a 226/challenge)
        bo = c.execute("SELECT until, reason FROM backoff WHERE platform=?",
                       (platform,)).fetchone()
        if bo and bo[0] > now.isoformat():
            return False, f"backoff until {bo[0][:16]} ({bo[1]})"

        # 1. Daytime window (MSK) — natural overnight gap
        h = _now_msk().hour
        if not (DAY_START_H <= h < DAY_END_H):
            return False, f"outside posting window ({h}:00 MSK; allowed {DAY_START_H}-{DAY_END_H})"

        # 2. Daily cap
        day_posts = _recent(c, platform, 24 * 60)
        cap = 2 if in_warmup() else DAILY_CAP
        if len(day_posts) >= cap:
            return False, f"daily cap reached ({len(day_posts)}/{cap}{' warmup' if in_warmup() else ''})"

        # 3. Rolling 30-min ceiling (anti-burst — THE rule that prevents the ban)
        roll = _recent(c, platform, ROLLING_WINDOW_MIN)
        if len(roll) >= ROLLING_MAX:
            return False, f"rolling-window ceiling ({len(roll)}/{ROLLING_MAX} in {ROLLING_WINDOW_MIN}min)"

        # 4. Min gap + jitter since last post
        if day_posts:
            last_ts = max(datetime.fromisoformat(p[1]) for p in day_posts)
            gap_min = (now - last_ts).total_seconds() / 60
            import hashlib
            # deterministic per-text jitter so it's stable across retries
            jit = (int(hashlib.md5(text.encode()).hexdigest(), 16) % (2 * JITTER_MIN)) - JITTER_MIN
            need = MIN_GAP_MIN + jit
            if gap_min < need:
                return False, f"too soon (last post {gap_min:.0f}min ago; need {need:.0f}min)"

        # 5. Dedup — reject near-duplicate text (the explicit X rule)
        for ptext, _, _ in _recent(c, platform, DEDUP_DAYS * 24 * 60):
            if SequenceMatcher(None, text.lower(), (ptext or "").lower()).ratio() > DEDUP_SIM:
                return False, "near-duplicate of a recent post (X bans duplicate content)"

        # 6. Content hygiene
        if len(re.findall(r"#\w+", text)) > HASHTAG_MAX:
            return False, f"too many hashtags (>{HASHTAG_MAX} trips spam filter)"
        has_link = bool(re.search(r"https?://", text))
        if has_link and in_warmup():
            return False, "warm-up: no external links in first 14 days"
        if has_link:
            links_today = sum(1 for p in day_posts if p[2])
            if links_today >= LINKS_PER_DAY:
                return False, f"daily link cap ({links_today}/{LINKS_PER_DAY})"

        return True, "ok"
    finally:
        c.close()


def record_post(platform: str, text: str) -> None:
    c = _conn()
    has_link = 1 if re.search(r"https?://", text) else 0
    c.execute("INSERT INTO posts VALUES (?,?,?,?)",
              (platform, text, datetime.now(timezone.utc).isoformat(), has_link))
    c.commit()
    c.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        ok, why = guard_check(sys.argv[1], sys.argv[2])
        print(f"allowed={ok} · {why} · warmup={in_warmup()}")
    else:
        print("usage: post_guard.py <platform> <text>")
