"""awesome_list_pr_drafter — find awesome-* repos where Sergei's work should appear, draft PRs.

Pure autonomous: no Sergei input needed. Runs weekly cron Thursday 10:00 UTC.

Pipeline:
  1. Iterate over a curated TARGETS list of awesome-* GitHub repos
  2. For each, fetch README.md via GitHub raw URL
  3. Check if any of Sergei's signals (preprints, repos, name) already linked
  4. If NOT linked AND topic-match is strong (LLM check), draft a PR description:
       - Where to insert (which section)
       - What to add (markdown bullet)
       - PR title + body
  5. Save draft to /opt/reports/contributions/awesome-{slug}/{date}-pr-draft.md
  6. TG notify with "ready-to-submit" link

The actual PR submission requires GitHub auth (fork → branch → commit → PR).
Currently STOPS at draft; can extend with gh CLI + PAT for autonomous submit.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CONTRIBUTIONS_DIR = Path("/opt/reports/contributions")
STATE_PATH = Path("/root/.openclaw/awesome_seen.json")

# Curated awesome-* targets — high-relevance for Sergei's portfolio
TARGETS = [
    {
        "repo": "crytic/awesome-ethereum-security",
        "raw": "https://raw.githubusercontent.com/crytic/awesome-ethereum-security/master/README.md",
        "match_keywords": ["RAG", "vulnerability detection", "ML"],
        "section_hint": "Tools / Resources / Research",
        "suggest": "Honest-RAG-Solidity (RAG-based vulnerability detection)",
    },
    {
        "repo": "ConsenSys/awesome-defi",
        "raw": "https://raw.githubusercontent.com/ConsenSys/awesome-defi/master/README.md",
        "match_keywords": ["ERC-4626", "yield", "vault strategy"],
        "section_hint": "Research / Vaults",
        "suggest": "AI-Yield-Vault (ML strategy selection for ERC-4626)",
    },
    {
        "repo": "jslee02/awesome-deep-learning-finance",
        "raw": "https://raw.githubusercontent.com/jslee02/awesome-deep-learning-finance/master/README.md",
        "match_keywords": ["LOB", "limit order book", "mid-price"],
        "section_hint": "Papers / Limit order book",
        "suggest": "Regime-Conditioning for LOB Mid-Price Prediction",
    },
    {
        "repo": "georgezouq/awesome-ai-in-finance",
        "raw": "https://raw.githubusercontent.com/georgezouq/awesome-ai-in-finance/master/README.md",
        "match_keywords": ["multi-agent", "research agent", "quant agent"],
        "section_hint": "Agents / Research",
        "suggest": "FinAgent: Multi-agent systematic financial research",
    },
    {
        "repo": "promptslab/Awesome-Prompt-Engineering",
        "raw": "https://raw.githubusercontent.com/promptslab/Awesome-Prompt-Engineering/main/README.md",
        "match_keywords": ["prompt injection", "RAG security", "honest RAG"],
        "section_hint": "Security / Prompt Injection",
        "suggest": "Honest Prompt-Injection Detection via Retrieval Consistency",
    },
    {
        "repo": "kjam/awesome-rag",
        "raw": "https://raw.githubusercontent.com/kjam/awesome-rag/main/README.md",
        "match_keywords": ["RAG", "retrieval", "smart contract", "Solidity"],
        "section_hint": "Applications / Security",
        "suggest": "Honest-RAG-Solidity — vulnerability detection",
    },
    {
        "repo": "francescogorini/awesome-blockchain-research",
        "raw": "https://raw.githubusercontent.com/francescogorini/awesome-blockchain-research/main/README.md",
        "match_keywords": ["security", "DeFi", "MEV"],
        "section_hint": "Security / Auditing",
        "suggest": "Honest-RAG-Solidity",
    },
    {
        "repo": "ZenGo-X/awesome-smart-contract-vulnerability-detection",
        "raw": "https://raw.githubusercontent.com/ZenGo-X/awesome-smart-contract-vulnerability-detection/main/README.md",
        "match_keywords": ["LLM", "RAG", "static analysis"],
        "section_hint": "LLM-based detection",
        "suggest": "Honest-RAG-Solidity (cross-encoder rerank + retrieval verification)",
    },
]

SERGEI_SIGNALS = [
    "sergeisolovev.com",
    "SergeySolovyev",
    "Sergei Solovev",
    "honest-rag-solidity",
    "ai-yield-vault",
    "32141182", "32141167", "31859557", "31429971", "31430086",  # DOI tails
]


def _load_seen() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_seen(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def _fetch_readme(url: str) -> str:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "sergei-brand-agent/awesome-scanner"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"fetch {url} error: {e}")
        return ""


def _already_present(readme: str) -> bool:
    txt = readme.lower()
    return any(sig.lower() in txt for sig in SERGEI_SIGNALS)


def _topic_match_check(readme_excerpt: str, keywords: list[str]) -> bool:
    """Lightweight LLM check: is this awesome-list a good fit for Sergei?"""
    prompt = (
        "You're checking topic-fit between Sergei Solovev's portfolio (DeFi "
        "security, RAG, ML for finance, smart-contract auditing) and an "
        f"awesome-* GitHub list with keywords {keywords}.\n\n"
        f"List README excerpt (first 3000 chars):\n{readme_excerpt[:3000]}\n\n"
        "Reply with one word: FIT (high-relevance) or SKIP (low-relevance)."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-haiku-4-5", prompt],
            capture_output=True, text=True, timeout=30,
        )
        return "FIT" in r.stdout.upper()
    except Exception:
        return True  # default to attempt on LLM failure


def _draft_pr(target: dict, readme: str) -> str:
    prompt = (
        f"Draft a GitHub PR description for adding Sergei Solovev's work to "
        f"the awesome list `{target['repo']}`.\n\n"
        f"Suggestion to add: {target['suggest']}\n"
        f"Section hint: {target['section_hint']}\n"
        f"Target signals/keywords in list: {target['match_keywords']}\n\n"
        f"README excerpt (first 2000 chars):\n{readme[:2000]}\n\n"
        "Output as markdown with these sections:\n\n"
        "## PR title\n"
        "<title, max 70 chars, format: 'Add: <work> (<short description>)'>\n\n"
        "## Where to insert\n"
        "<exact section name from README + reasoning>\n\n"
        "## Markdown bullet to add\n"
        "```markdown\n"
        "<one bullet line, format: - [Name](URL) — short description (year).>\n"
        "```\n\n"
        "## PR body\n"
        "<2-3 sentences explaining why this work fits the list, mentioning a "
        "specific technical contribution. NO marketing speak, NO exclamations.>\n"
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=120,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception as e:
        print(f"draft error: {e}")
        return ""


def main() -> int:
    seen = _load_seen()
    drafts_created = 0
    today = datetime.now(timezone.utc).date().isoformat()

    for target in TARGETS:
        repo = target["repo"]
        if seen.get(repo, {}).get("drafted_at"):
            print(f"skip {repo}: already drafted")
            continue

        readme = _fetch_readme(target["raw"])
        if not readme:
            continue
        if _already_present(readme):
            print(f"skip {repo}: Sergei already linked")
            seen[repo] = {"already_present": True,
                          "checked_at": datetime.now(timezone.utc).isoformat()}
            continue
        if not _topic_match_check(readme, target["match_keywords"]):
            print(f"skip {repo}: topic-fit check failed")
            continue

        pr_draft = _draft_pr(target, readme)
        if not pr_draft:
            continue

        slug = repo.replace("/", "-")
        out_dir = CONTRIBUTIONS_DIR / f"awesome-{slug}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{today}-pr-draft.md"
        out_file.write_text(
            f"<!-- Target repo: {repo} -->\n"
            f"<!-- Generated: {datetime.now(timezone.utc).isoformat()} -->\n\n"
            f"# PR draft for {repo}\n\n"
            f"{pr_draft}\n\n"
            f"---\n"
            f"\n## To submit\n"
            f"1. Fork https://github.com/{repo}\n"
            f"2. Edit README per 'Where to insert' section above\n"
            f"3. Open PR with title + body from this draft\n"
            f"4. Link this draft in PR description for audit trail\n",
            encoding="utf-8",
        )

        seen[repo] = {"drafted_at": datetime.now(timezone.utc).isoformat(),
                      "draft_file": str(out_file)}
        drafts_created += 1

        subprocess.run(
            ["/usr/local/bin/tg_send",
             f"📋 *Awesome-list PR drafted*\n\n"
             f"Target: {repo}\n"
             f"Suggest: {target['suggest']}\n\n"
             f"Draft: https://github.com/SergeySolovyev/sergei-brand-agent-reports/"
             f"blob/main/contributions/awesome-{slug}/{today}-pr-draft.md"],
            check=False,
        )

        try:
            subprocess.run(
                ["git", "-C", "/opt/reports", "add",
                 f"contributions/awesome-{slug}/{today}-pr-draft.md"],
                check=False,
            )
            subprocess.run(
                ["git", "-C", "/opt/reports", "-c", "user.name=openclaw-agent",
                 "-c", "user.email=agent@sergeisolovev.com",
                 "commit", "-m", f"awesome PR draft: {slug}", "--quiet"],
                check=False,
            )
            subprocess.run(["git", "-C", "/opt/reports", "push", "--quiet"], check=False)
        except Exception:
            pass

    _save_seen(seen)
    print(f"done. drafts created: {drafts_created}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
