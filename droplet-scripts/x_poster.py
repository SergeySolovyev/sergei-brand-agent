#!/opt/brand-agent/venv/bin/python3
"""x_poster — post to X (Twitter) using session cookies (auth_token + ct0).

Why cookies, not the official API: X's v2 API write access costs $100+/mo.
The web session (auth_token + ct0 CSRF) lets the agent post on the free tier
the same way the browser does. Cookies live in /opt/brand-agent/secrets/x.env
(chmod 600). They expire eventually (~months) — refresh by re-copying from
DevTools when posting starts failing with 401.

Usage:
  x_poster.py "<tweet text>"           # single tweet
  x_poster.py --file <path>            # tweet text from file
  x_poster.py --thread <file>          # one tweet per non-empty line (reply chain)

Reads: /opt/brand-agent/secrets/x.env  (X_AUTH_TOKEN=..., X_CT0=...)
Returns tweet URL on success.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

SECRETS = Path("/opt/brand-agent/secrets/x.env")
# Public web bearer token X's own site uses — not a secret, ships in their JS.
BEARER = ("Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
          "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA")
CREATE_TWEET_URL = "https://x.com/i/api/graphql/a1p9RWpkYKBjWv_I3WzS-A/CreateTweet"


def _creds() -> tuple[str, str]:
    auth = ct0 = ""
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            if line.startswith("X_AUTH_TOKEN="):
                auth = line.split("=", 1)[1].strip()
            elif line.startswith("X_CT0="):
                ct0 = line.split("=", 1)[1].strip()
    return auth, ct0


def post_tweet(text: str, reply_to: str | None = None,
               skip_guard: bool = False) -> str | None:
    auth, ct0 = _creds()
    if not auth or not ct0:
        print("FAIL: X_AUTH_TOKEN / X_CT0 missing in /opt/brand-agent/secrets/x.env")
        return None

    # ANTI-BAN GATE — never post without passing the guard (prevents the
    # burst-posting pattern that got the prior account banned). Thread replies
    # skip the gap/dedup check (they're one logical unit) but still record.
    if not skip_guard:
        try:
            import sys as _s
            _s.path.insert(0, "/opt/brand-agent")
            import post_guard
            ok, why = post_guard.guard_check("x", text)
            if not ok:
                print(f"BLOCKED by post_guard: {why}")
                return None
        except Exception as e:
            print(f"post_guard unavailable ({e}) — refusing to post for safety")
            return None

    variables = {
        "tweet_text": text,
        "dark_request": False,
        "media": {"media_entities": [], "possibly_sensitive": False},
        "semantic_annotation_ids": [],
    }
    if reply_to:
        variables["reply"] = {"in_reply_to_tweet_id": reply_to,
                              "exclude_reply_user_ids": []}
    payload = {
        "variables": variables,
        "features": {
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_enhance_cards_enabled": False,
        },
        "queryId": "a1p9RWpkYKBjWv_I3WzS-A",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(CREATE_TWEET_URL, data=data, method="POST")
    req.add_header("authorization", BEARER)
    req.add_header("x-csrf-token", ct0)
    req.add_header("content-type", "application/json")
    req.add_header("cookie", f"auth_token={auth}; ct0={ct0}")
    req.add_header("x-twitter-auth-type", "OAuth2Session")
    req.add_header("x-twitter-active-user", "yes")
    req.add_header("user-agent",
                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        tid = (resp.get("data", {}).get("create_tweet", {})
               .get("tweet_results", {}).get("result", {}).get("rest_id"))
        if tid:
            try:
                import sys as _s
                _s.path.insert(0, "/opt/brand-agent")
                import post_guard
                post_guard.record_post("x", text)
            except Exception:
                pass
            return f"https://x.com/i/status/{tid}"
        print(f"FAIL: unexpected response: {json.dumps(resp)[:300]}")
        return None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        print(f"FAIL HTTP {e.code}: {body}")
        # 226 = "looks automated" challenge, 429 = rate limit, 401 = bad cookie.
        # Freeze the platform for hours — NEVER retry into a lockout (research:
        # the longest bans come from retrying during the challenge).
        if e.code in (226, 429, 403):
            try:
                import sys as _s
                _s.path.insert(0, "/opt/brand-agent")
                import post_guard
                post_guard.set_backoff("x", hours=6, reason=f"HTTP {e.code}")
                print(f"post_guard: X frozen 6h after HTTP {e.code}")
            except Exception:
                pass
        return None
    except Exception as e:
        print(f"FAIL: {e}")
        return None


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    if sys.argv[1] == "--thread" and len(sys.argv) > 2:
        import time as _t
        import hashlib as _h
        lines = [l.strip() for l in Path(sys.argv[2]).read_text(
            encoding="utf-8").splitlines() if l.strip()]
        prev = None
        for i, ln in enumerate(lines):
            # First tweet passes the full guard; replies are one logical unit
            # so they skip gap/dedup but still record + use a human 20-90s delay.
            if i > 0:
                delay = 20 + (int(_h.md5(ln.encode()).hexdigest(), 16) % 70)
                _t.sleep(delay)
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
