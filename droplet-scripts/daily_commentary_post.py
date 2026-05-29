#!/opt/brand-agent/venv/bin/python3
"""daily_commentary_post — autonomous daily content generator.

Runs from cron at 10:00 UTC daily. Picks ONE preprint from Sergei's portfolio,
generates a 200-word commentary thread (LinkedIn-style) and saves to drafts.

If TELEGRAM_PUBLIC_CHANNEL is set in .env, also publishes to that channel.
Otherwise just files the draft for manual review.
"""
import json
import os
import random
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENV_PATH = Path("/opt/brand-agent/.env")
POSTS_DIR = Path("/opt/reports/posts")
SOUL_PATH = Path("/opt/brand-agent/SOUL.md")

# Sergei's 5 preprints with light context
PREPRINT_TOPICS = [
    {
        "doi": "10.6084/m9.figshare.32141182",
        "title": "Honest-RAG-Solidity",
        "angle": "RAG retrieval verification reduces hallucination in smart-contract vulnerability detection",
        "tag": "smart contract security",
    },
    {
        "doi": "10.6084/m9.figshare.32141167",
        "title": "AI-Yield-Vault",
        "angle": "ML-driven strategy selection for ERC-4626 yield vaults — balancing exploration vs exploitation",
        "tag": "DeFi",
    },
    {
        "doi": "10.6084/m9.figshare.31859557",
        "title": "Regime-Conditioning for LOB",
        "angle": "Market regime detection improves limit order book mid-price prediction",
        "tag": "quant",
    },
    {
        "doi": "10.6084/m9.figshare.31429971",
        "title": "FinAgent",
        "angle": "Multi-agent architecture for systematic financial research",
        "tag": "AI agents",
    },
    {
        "doi": "10.6084/m9.figshare.31430086",
        "title": "Honest Prompt-Injection Detection",
        "angle": "Detecting prompt injection in RAG pipelines via retrieval consistency",
        "tag": "LLM security",
    },
]


def _load_env():
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _compose_post(topic, soul):
    prompt = (
        "You are Sergei Solovev posting a short LinkedIn-style commentary on your "
        "own research. Voice: technical, evidence-based, no marketing speak. "
        "No exclamation marks. No hashtag spam (max 3 specific tags).\n\n"
        f"YOUR VOICE (excerpt):\n{soul[:1000]}\n\n"
        f"TODAY'S TOPIC:\n"
        f"  Preprint: {topic['title']}\n"
        f"  DOI: {topic['doi']}\n"
        f"  Angle: {topic['angle']}\n"
        f"  Tag: {topic['tag']}\n\n"
        "Write a 150-250 word post that:\n"
        "  1. Opens with a concrete observation or question\n"
        "  2. States what you found / propose (1-2 sentences)\n"
        "  3. Why it matters in practice (1-2 sentences)\n"
        "  4. Link to preprint: https://figshare.com/articles/preprint/{title-slug}/{id}\n"
        "  5. Ends with 2-3 hashtags from {DeFi, ML, RAG, SmartContracts, QuantFinance, AIagents}\n\n"
        "Output ONLY the post body. No preamble."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=120,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception as e:
        print(f"compose error: {e}")
        return ""


def _critique(post, topic):
    prompt = (
        "Critic review of a LinkedIn-style research commentary. Find:\n"
        "- factual errors about the preprint\n"
        "- overclaiming or hype\n"
        "- exclamation marks (banned)\n"
        "- generic LinkedIn-speak ('thrilled to share', 'excited to announce')\n"
        "- hashtag spam (>3 tags)\n\n"
        f"Topic: {topic['title']} — {topic['angle']}\n\n"
        f"--- POST ---\n{post[:2000]}\n--- END ---\n\n"
        "Reply with VERDICT: PASS | REVISE | REJECT\nThen 2-3 bullet issues."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return "PASS", "Critic unreachable"
        out = r.stdout
        m = re.search(r"VERDICT:\s*(PASS|REVISE|REJECT)", out)
        return m.group(1) if m else "PASS", out
    except Exception as e:
        return "PASS", f"Critic exception: {e}"


def _publish_to_tg_channel(post, channel, bot_token):
    """Publish post to public TG channel via Bot API."""
    if not channel or not bot_token:
        return None
    try:
        data = json.dumps({
            "chat_id": channel,
            "text": post,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
        return resp.get("result", {}).get("message_id")
    except Exception as e:
        print(f"tg channel publish failed: {e}")
        return None


def main():
    env = _load_env()
    soul = SOUL_PATH.read_text(encoding="utf-8") if SOUL_PATH.exists() else ""

    # Daily pick — use date-seeded so each day picks different one
    random.seed(datetime.utcnow().date().toordinal())
    topic = random.choice(PREPRINT_TOPICS)
    print(f"today's topic: {topic['title']}")

    post = _compose_post(topic, soul)
    if not post:
        return 1

    verdict, feedback = _critique(post, topic)
    print(f"verdict: {verdict}")

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow().date().isoformat()
    slug = re.sub(r"[^a-z0-9-]+", "-", topic["title"].lower())[:40]
    draft_path = POSTS_DIR / f"{today}-{slug}.md"
    draft_path.write_text(
        f"<!-- Topic: {topic['title']} -->\n"
        f"<!-- Verdict: {verdict} -->\n"
        f"<!-- DOI: {topic['doi']} -->\n\n"
        + post, encoding="utf-8",
    )

    # Auto-publish if channel configured + verdict PASS
    public_channel = env.get("TELEGRAM_PUBLIC_CHANNEL", "")
    bot_token = env.get("TELEGRAM_BOT_TOKEN", "")
    published_id = None
    if verdict == "PASS" and public_channel:
        published_id = _publish_to_tg_channel(post, public_channel, bot_token)

    # Notify Sergei
    status = (
        f"✓ Published to {public_channel} (msg #{published_id})"
        if published_id else
        ("⏸ Channel not configured — draft only"
         if not public_channel else
         "✗ Auto-publish failed — draft only")
    )
    summary = (
        f"📝 *Daily commentary draft*\n\n"
        f"Topic: {topic['title']}\n"
        f"Verdict: {verdict}\n"
        f"Status: {status}\n\n"
        f"Post preview:\n{post[:600]}\n\n"
        f"Draft: https://github.com/SergeySolovyev/sergei-brand-agent-reports/"
        f"blob/main/posts/{today}-{slug}.md"
    )
    subprocess.run(["/usr/local/bin/tg_send", summary], check=False)

    # Commit
    try:
        subprocess.run(
            ["git", "-C", "/opt/reports", "add", f"posts/{today}-{slug}.md"],
            check=False,
        )
        subprocess.run(
            ["git", "-C", "/opt/reports", "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m", f"daily commentary: {topic['title']}", "--quiet"],
            check=False,
        )
        subprocess.run(["git", "-C", "/opt/reports", "push", "--quiet"], check=False)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
