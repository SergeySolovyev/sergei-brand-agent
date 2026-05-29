#!/opt/brand-agent/venv/bin/python3
"""conference_proposal_drafter — auto-draft talk proposal on CFP discovery.

Triggered by cfp_discovered events.

  conference_proposal_drafter.py <slug>

Composes a full talk proposal:
  - Title (catchy, technical, no hype)
  - Abstract (200-300 words)
  - Outcomes (3 bullet points — what attendees will learn)
  - Speaker bio (from identity.json speaker_bio, fallback to academic_hse profile)
  - Format suggestion (workshop / lightning / keynote based on CFP signals)

Saves to /opt/reports/proposals/{cfp_slug}/draft.md.
Without Sessionize/Pretalx session, draft is file-only. With cookies, future
work submits via Playwright.
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPORTS_INBOX = Path("/opt/reports/reports/inbox")
PROPOSALS_DIR = Path("/opt/reports/proposals")
SOUL_PATH = Path("/opt/brand-agent/SOUL.md")
IDENTITY_PATH = Path("/opt/brand-agent/knowledge_base/identity.json")

PORTFOLIO_TOPICS = [
    "Smart-contract vulnerability detection with RAG verification",
    "Honest prompt-injection defense for production RAG systems",
    "Multi-agent architectures for systematic financial research (FinAgent)",
    "Regime-aware mid-price prediction in limit order books",
    "ML-driven strategy selection for ERC-4626 yield vaults",
    "Bridging TradFi banking operations to DeFi protocols",
]


def _find_inbox(slug):
    matches = sorted(REPORTS_INBOX.glob(f"*_{slug}*.md"))
    return matches[-1] if matches else None


def _parse_cfp(path):
    text = path.read_text(encoding="utf-8")
    out = {"raw": text}
    for field in ("Title", "Conference", "URL", "Submission deadline",
                  "Event date", "Location", "Tracks", "Topics"):
        m = re.search(rf"^{field}:\s*(.+)$", text, re.MULTILINE)
        if m:
            out[field.lower().replace(" ", "_")] = m.group(1).strip()
    return out


def _compose_proposal(cfp, profile, soul, speaker_bio):
    prompt = (
        "You are Sergei Solovev drafting a conference talk proposal. Stay in his "
        "voice: technical, evidence-based, no marketing speak, no exclamation marks.\n\n"
        f"YOUR BIO REFERENCE:\n{soul[:800]}\n\n"
        f"PORTFOLIO TOPICS YOU CAN COVER:\n" +
        "\n".join(f"  - {t}" for t in PORTFOLIO_TOPICS) + "\n\n"
        f"--- CFP ---\n"
        f"Conference: {cfp.get('conference', '?')}\n"
        f"Title/CFP: {cfp.get('title', '?')}\n"
        f"Tracks: {cfp.get('tracks', '?')}\n"
        f"Topics requested: {cfp.get('topics', '?')}\n"
        f"Deadline: {cfp.get('submission_deadline', '?')}\n"
        f"Event date: {cfp.get('event_date', '?')}\n"
        f"Location: {cfp.get('location', '?')}\n"
        f"URL: {cfp.get('url', '?')}\n"
        f"--- END CFP ---\n\n"
        "Choose the BEST-MATCHING portfolio topic for this CFP and draft a proposal:\n\n"
        "# Talk Proposal: <catchy technical title>\n\n"
        "**Format**: <workshop | lightning (15min) | regular (30min) | keynote>\n\n"
        "## Abstract (200-300 words)\n"
        "Concrete problem · what you'll show · key insight · who benefits.\n\n"
        "## What attendees will take away\n"
        "- 3 specific bullet points\n\n"
        "## Why I'm the right speaker\n"
        "Tie to 1-2 of Sergei's preprints + 1 unique perspective (TradFi → DeFi bridge).\n\n"
        "## Speaker bio (third person, ~80 words)\n"
        f"{speaker_bio or '<draft a bio from SOUL.md>'}\n\n"
        "## Talk outline (5 sections, 1 line each)\n\n"
        "Output ONLY the markdown. No commentary."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=180,
        )
        return r.stdout if r.returncode == 0 else ""
    except Exception as e:
        print(f"compose error: {e}")
        return ""


def main():
    if len(sys.argv) < 2:
        print("usage: conference_proposal_drafter.py <slug>")
        return 1
    slug = sys.argv[1]
    inbox = _find_inbox(slug)
    if not inbox:
        print(f"no inbox for slug={slug}")
        return 1
    cfp = _parse_cfp(inbox)
    soul = SOUL_PATH.read_text(encoding="utf-8") if SOUL_PATH.exists() else ""

    identity = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
    profile = dict(identity["profiles"].get("academic_hse", {}))
    profile["globals"] = identity.get("globals", {})
    speaker_bio = identity.get("globals", {}).get("speaker_bio", "")

    draft = _compose_proposal(cfp, profile, soul, speaker_bio)
    if not draft:
        return 1

    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-z0-9-]+", "-", slug.lower())[:50]
    today = datetime.utcnow().date().isoformat()
    out_dir = PROPOSALS_DIR / safe
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{today}-proposal.md"
    out_file.write_text(
        f"<!-- CFP: {cfp.get('conference','')} -->\n"
        f"<!-- Event: {cfp.get('event_date','')} at {cfp.get('location','')} -->\n"
        f"<!-- Deadline: {cfp.get('submission_deadline','')} -->\n"
        f"<!-- URL: {cfp.get('url','')} -->\n\n"
        + draft,
        encoding="utf-8",
    )

    # Notify
    word_count = len(draft.split())
    summary = (
        f"🎤 *Talk proposal draft ready*\n\n"
        f"CFP: {cfp.get('conference', '?')} — {cfp.get('title', '?')[:60]}\n"
        f"Deadline: {cfp.get('submission_deadline', '?')}\n"
        f"Event: {cfp.get('event_date', '?')} ({cfp.get('location', '?')})\n"
        f"Draft: ~{word_count} words\n\n"
        f"https://github.com/SergeySolovyev/sergei-brand-agent-reports/"
        f"blob/main/proposals/{safe}/{today}-proposal.md"
    )
    subprocess.run(["/usr/local/bin/tg_send", summary], check=False)

    # Commit
    try:
        subprocess.run(
            ["git", "-C", "/opt/reports", "add",
             f"proposals/{safe}/{today}-proposal.md"], check=False,
        )
        subprocess.run(
            ["git", "-C", "/opt/reports", "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m", f"talk proposal: {cfp.get('conference','')[:50]}",
             "--quiet"], check=False,
        )
        subprocess.run(["git", "-C", "/opt/reports", "push", "--quiet"], check=False)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
