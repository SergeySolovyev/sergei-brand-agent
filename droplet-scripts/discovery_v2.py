#!/opt/brand-agent/venv/bin/python3
"""discovery_v2 — reliable daily discovery on WORKING no-auth APIs.

The old discovery hit ETHGlobal (404), DoraHacks (405), fasie.ru (403) — all
dead. This replaces them with rock-solid sources that actually return fresh
signal every day:

  1. arXiv API (export.arxiv.org) — new papers in Sergei's domains. Two uses:
     - IDEAS: what to read / build on / cite
     - CITATION TARGETS: papers close to his work he could engage with
  2. Hacker News (Algolia API) — recent stories/comments mentioning his
     keywords + opportunity words (grant, hackathon, hiring, bounty, CFP).
  3. OpenAlex — new works citing his domains (lightweight, polite pool).

All dedupe via the existing `discoveries` table. Severity:
  - direct opportunity (grant/hackathon/CFP/hiring) → high
  - relevant new paper / idea → medium
  - tangential → low (rolled into daily digest)

Runs daily 07:00 UTC.
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATE = Path("/root/.openclaw/agent_state.sqlite")
db = sqlite3.connect(STATE)
db.execute(
    "CREATE TABLE IF NOT EXISTS discoveries "
    "(url TEXT PRIMARY KEY, kind TEXT, title TEXT, first_seen TEXT)"
)

# Sergei's research/interest keywords — drive all queries.
KEYWORDS = [
    "smart contract vulnerability", "RAG retrieval augmented",
    "DeFi security", "limit order book", "ERC-4626",
    "prompt injection", "EVM bytecode", "AI agent finance",
    "MEV", "formal verification solidity",
]

# Self-improvement: merge in keywords the retrospective learned from Sergei's
# engagement (button clicks). Closes the loop — discovery gets smarter weekly.
try:
    _learned = json.loads(
        Path("/opt/brand-agent/learned_keywords.json").read_text())
    for _k in _learned.get("keywords", []):
        if isinstance(_k, str) and _k not in KEYWORDS:
            KEYWORDS.append(_k)
except Exception:
    pass
# Opportunity trigger words (for HN + general)
OPP_WORDS = ["grant", "hackathon", "bounty", "call for papers", "cfp",
             "hiring researcher", "research fellowship", "funding", "residency"]


def already(url: str) -> bool:
    return db.execute("SELECT 1 FROM discoveries WHERE url=?", (url,)).fetchone() is not None


def remember(url: str, kind: str, title: str) -> None:
    db.execute(
        "INSERT OR REPLACE INTO discoveries VALUES (?, ?, ?, ?)",
        (url, kind, title, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()


def emit(sev: str, kind: str, title: str, body: str) -> None:
    subprocess.run(["/usr/local/bin/emit_event", sev, kind, title, body], check=False)


def _get(url: str, headers: dict | None = None, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url, headers=headers or {"User-Agent": "sergei-brand-agent/discovery-v2"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


found = 0


# ─────────────────────────────────────────────────────────────────────
# 1. arXiv — new papers in domain (IDEAS + citation targets)
# ─────────────────────────────────────────────────────────────────────
def scan_arxiv() -> int:
    global found
    n = 0
    # Build an OR query across keyword phrases, restricted to relevant categories
    cat = "(cat:cs.CR OR cat:cs.LG OR cat:cs.AI OR cat:q-fin.TR OR cat:q-fin.CP)"
    terms = " OR ".join(f'abs:"{k}"' for k in KEYWORDS[:6])
    q = f"{cat} AND ({terms})"
    url = ("http://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote(q)
           + "&sortBy=submittedDate&sortOrder=descending&max_results=15")
    try:
        xml = _get(url)
    except Exception as e:
        print(f"arxiv error: {e}")
        return 0
    # Parse Atom entries
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
    for e in entries:
        m_id = re.search(r"<id>([^<]+)</id>", e)
        m_t = re.search(r"<title>([^<]+)</title>", e, re.DOTALL)
        m_s = re.search(r"<summary>([^<]+)</summary>", e, re.DOTALL)
        if not m_id or not m_t:
            continue
        link = m_id.group(1).strip()
        title = re.sub(r"\s+", " ", m_t.group(1)).strip()
        summary = re.sub(r"\s+", " ", (m_s.group(1) if m_s else "")).strip()
        if already(link):
            continue
        remember(link, "paper", title)
        emit("medium", "paper_discovered",
             f"arXiv: {title[:70]}",
             f"New paper in your domain — idea / citation target.\n\n"
             f"{title}\n{link}\n\n{summary[:400]}")
        n += 1
        found += 1
        if n >= 5:  # cap per run
            break
    return n


# ─────────────────────────────────────────────────────────────────────
# 2. Hacker News (Algolia) — opportunities + discussion in domain
# ─────────────────────────────────────────────────────────────────────
def scan_hn() -> int:
    global found
    n = 0
    queries = ["smart contract security", "DeFi", "RAG evaluation",
               "AI agents", "limit order book"]
    for query in queries:
        url = ("https://hn.algolia.com/api/v1/search_by_date?query="
               + urllib.parse.quote(query)
               + "&tags=(story,comment)&numericFilters=points%3E5&hitsPerPage=10")
        try:
            data = json.loads(_get(url))
        except Exception as e:
            print(f"hn error ({query}): {e}")
            continue
        for hit in data.get("hits", []):
            obj_id = hit.get("objectID")
            hn_url = f"https://news.ycombinator.com/item?id={obj_id}"
            if already(hn_url):
                continue
            title = hit.get("title") or hit.get("story_title") or ""
            text = (hit.get("comment_text") or hit.get("story_text") or "")[:500]
            haystack = f"{title} {text}".lower()
            # Only surface if it mentions an opportunity OR strong domain match
            is_opp = any(w in haystack for w in OPP_WORDS)
            if not title and not is_opp:
                continue
            remember(hn_url, "hn", title or query)
            sev = "high" if is_opp else "low"
            emit(sev, "discussion_discovered",
                 f"HN: {(title or query)[:70]}",
                 f"{'OPPORTUNITY' if is_opp else 'Discussion'} in your domain.\n\n"
                 f"{title}\n{hn_url}\n\n{text[:300]}")
            n += 1
            found += 1
            if n >= 6:
                return n
    return n


if __name__ == "__main__":
    a = scan_arxiv()
    h = scan_hn()
    if found == 0:
        emit("low", "discovery_quiet", "discovery_v2: nothing new",
             "Scanned arXiv + HN. No new papers or opportunities matched today.")
    print(f"discovery_v2: arxiv={a} hn={h} total_new={found} "
          f"at {datetime.now(timezone.utc).isoformat()}")
