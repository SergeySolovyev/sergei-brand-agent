#!/opt/brand-agent/venv/bin/python3
"""x_poster_api — post to X via the OFFICIAL API (OAuth 1.0a user context).

Chosen over cookie-posting because: (1) datacenter-IP cookie automation is a
ban signal, (2) the sanctioned API is server-friendly, (3) free write tier
(~1,500 posts/month) easily covers 1-4 posts/day. Same post_guard anti-ban
layer applies — the guard caps cadence regardless of transport.

Credentials in /opt/brand-agent/secrets/x_api.env (chmod 600):
  X_API_KEY=...            (consumer key)
  X_API_SECRET=...         (consumer secret)
  X_ACCESS_TOKEN=...       (must be Read+Write)
  X_ACCESS_SECRET=...

Usage:
  x_poster_api.py "<tweet text>"
  x_poster_api.py --file <path>
  x_poster_api.py --thread <file>     # one tweet per non-empty line, reply chain
"""
from __future__ import annotations

import sys
from pathlib import Path

SECRETS = Path("/opt/brand-agent/secrets/x_api.env")


def _creds() -> dict:
    out = {}
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def _client():
    import tweepy
    c = _creds()
    needed = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"]
    if not all(c.get(k) for k in needed):
        print(f"FAIL: missing keys in {SECRETS} (need {needed})")
        return None
    return tweepy.Client(
        consumer_key=c["X_API_KEY"],
        consumer_secret=c["X_API_SECRET"],
        access_token=c["X_ACCESS_TOKEN"],
        access_token_secret=c["X_ACCESS_SECRET"],
    )


def post_tweet(text: str, reply_to: str | None = None,
               skip_guard: bool = False) -> str | None:
    if not skip_guard:
        try:
            sys.path.insert(0, "/opt/brand-agent")
            import post_guard
            ok, why = post_guard.guard_check("x", text)
            if not ok:
                print(f"BLOCKED by post_guard: {why}")
                return None
        except Exception as e:
            print(f"post_guard unavailable ({e}) — refusing to post")
            return None

    client = _client()
    if not client:
        return None
    try:
        kwargs = {"text": text}
        if reply_to:
            kwargs["in_reply_to_tweet_id"] = reply_to
        resp = client.create_tweet(**kwargs)
        tid = resp.data["id"]
        try:
            sys.path.insert(0, "/opt/brand-agent")
            import post_guard
            post_guard.record_post("x", text)
        except Exception:
            pass
        return f"https://x.com/i/status/{tid}"
    except Exception as e:
        msg = str(e)
        print(f"FAIL: {msg}")
        # 429 rate-limit / 403 duplicate → freeze platform, never hammer
        if "429" in msg or "403" in msg or "duplicate" in msg.lower():
            try:
                sys.path.insert(0, "/opt/brand-agent")
                import post_guard
                post_guard.set_backoff("x", hours=6, reason=msg[:50])
            except Exception:
                pass
        return None


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    if sys.argv[1] == "--thread" and len(sys.argv) > 2:
        import time, hashlib
        lines = [l.strip() for l in Path(sys.argv[2]).read_text(
            encoding="utf-8").splitlines() if l.strip()]
        prev = None
        for i, ln in enumerate(lines):
            if i > 0:
                time.sleep(20 + int(hashlib.md5(ln.encode()).hexdigest(), 16) % 70)
            url = post_tweet(ln, reply_to=prev, skip_guard=(i > 0))
            if not url:
                return 1
            if i > 0:
                try:
                    sys.path.insert(0, "/opt/brand-agent")
                    import post_guard
                    post_guard.record_post("x", ln)
                except Exception:
                    pass
            prev = url.rstrip("/").split("/")[-1]
            print(f"posted: {url}")
        return 0
    text = (Path(sys.argv[2]).read_text(encoding="utf-8")
            if sys.argv[1] == "--file" else sys.argv[1])
    url = post_tweet(text)
    if url:
        print(f"posted: {url}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
