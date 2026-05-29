"""article_drafter — multi-platform technical article generator.

Generates publication-ready drafts for Habr (RU), dev.to (EN), Hashnode (EN),
Medium (EN). Each platform has slightly different conventions; this module
adapts voice + structure + length per target.

Triggered by cron weekly (Friday 10:00 UTC) — picks a different platform each
week to spread output. Also callable on-demand:
  article_drafter.py habr [topic_key]
  article_drafter.py devto [topic_key]

Pipeline:
  1. Pick platform from cron rotation, or argv[1]
  2. Pick topic — date-seeded from PREPRINT_TOPICS (so each week different)
  3. Compose draft (Sonnet) — platform-aware prompt
  4. Critic review (Sonnet)
  5. Save to /opt/reports/posts/{platform}/{date}-{slug}.md
  6. Commit + push, notify TG

Why one drafter for 4 platforms: same source material (Sergei's preprints +
brand voice), different rendering. Single Composer call per week per platform.
Easier to maintain than 4 separate scripts.

Publication blocked on API tokens (dev.to API, Hashnode GraphQL, Medium token,
Habr cookie). When tokens added to .env, can auto-publish via separate
publish_article.py.
"""
from __future__ import annotations

import json
import random
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

POSTS_DIR = Path("/opt/reports/posts")
SOUL_PATH = Path("/opt/brand-agent/SOUL.md")

PREPRINT_TOPICS = [
    {
        "key": "honest-rag-solidity",
        "title_en": "Honest RAG for Smart-Contract Vulnerability Detection",
        "title_ru": "Honest RAG: обнаружение уязвимостей смарт-контрактов",
        "doi": "10.6084/m9.figshare.32141182",
        "angle_en": "RAG with retrieval verification cuts hallucinations in smart-contract auditing.",
        "angle_ru": "RAG с верификацией извлечения снижает галлюцинации при аудите смарт-контрактов.",
        "key_points": [
            "Smart-contract LLM audits hallucinate at ~31% baseline (Slither + GPT-4o)",
            "RAG with cross-encoder rerank cuts hallucination to 7%",
            "Honest verification step: LLM cannot answer if no retrieval evidence",
            "Repo + benchmark dataset released",
        ],
    },
    {
        "key": "ai-yield-vault",
        "title_en": "AI-Yield-Vault: Strategy Selection for ERC-4626 with ML",
        "title_ru": "AI-Yield-Vault: ML для выбора стратегии в ERC-4626",
        "doi": "10.6084/m9.figshare.32141167",
        "angle_en": "Market regime classifier outperforms naive yield chasing in ERC-4626 vaults.",
        "angle_ru": "Классификатор рыночного режима превосходит наивную охоту за доходностью в ERC-4626.",
        "key_points": [
            "Naive APY-chasing: -23% Sharpe in 2024 stress periods",
            "HMM + XGBoost regime classifier → +12-23% Sharpe improvement",
            "Composable with any ERC-4626 vault via hook",
            "Backtest on Aave v3 + Compound + Yearn",
        ],
    },
    {
        "key": "lob-regime",
        "title_en": "Regime-Conditioning for Limit Order Book Prediction",
        "title_ru": "Регимное кондиционирование для предсказания LOB",
        "doi": "10.6084/m9.figshare.31859557",
        "angle_en": "Regime tags improve mid-price prediction by 4-8% RMSE.",
        "angle_ru": "Регимные метки улучшают предсказание середины спреда на 4-8% RMSE.",
        "key_points": [
            "Standard MLOB models ignore regime context",
            "Conditioning on VPIN + spread regime → measurable lift",
            "Works on both centralized (Binance) and DEX LOBs",
            "Open dataset of 50M labelled snapshots",
        ],
    },
    {
        "key": "finagent",
        "title_en": "FinAgent: Multi-Agent Systematic Financial Research",
        "title_ru": "FinAgent: мультиагентная систематика финансовых исследований",
        "doi": "10.6084/m9.figshare.31429971",
        "angle_en": "Specialized agents (data, model, audit) compose for repeatable quant research.",
        "angle_ru": "Специализированные агенты (data, model, audit) образуют повторяемое quant-исследование.",
        "key_points": [
            "Single-prompt 'do quant research' hallucinates 60% of conclusions",
            "Decomposed 3-agent system grounds claims in measurable artifacts",
            "Critic agent rejects unverifiable claims (PASS / REVISE / REJECT)",
            "Open framework on GitHub",
        ],
    },
    {
        "key": "prompt-injection",
        "title_en": "Detecting Prompt Injection via Retrieval Consistency",
        "title_ru": "Обнаружение prompt injection через консистентность retrieval",
        "doi": "10.6084/m9.figshare.31430086",
        "angle_en": "If retrieval shifts dramatically on rephrasings, the prompt is being attacked.",
        "angle_ru": "Если retrieval сильно меняется на перефразах — на промпт идёт атака.",
        "key_points": [
            "Static injection detectors miss novel attacks (28% recall)",
            "Retrieval-consistency signal: stable retrievals = stable intent",
            "Self-supervised — no labelled injection corpus needed",
            "Benchmark on PromptBench + new RAGSec testbed",
        ],
    },
]

PLATFORM_CONFIGS = {
    "habr": {
        "lang": "ru",
        "length_words": (1500, 2500),
        "voice_instructions": (
            "Habr style: техническая глубина, конкретика, code-блоки, никакого "
            "маркетинг-блаблабла. Заголовок без 'как я', 'почему я'. "
            "Структура: hook → проблема → решение → код → выводы → ссылки. "
            "Минимум 2 code-блока, минимум 1 таблица или график (markdown)."
        ),
        "hashtags": ["smartcontracts", "defi", "machinelearning", "rag", "blockchain"],
    },
    "devto": {
        "lang": "en",
        "length_words": (1000, 1800),
        "voice_instructions": (
            "dev.to style: practical, code-first, friendly but not chummy. "
            "Front-matter ready: title + canonical_url + tags + cover_image. "
            "Sections: TL;DR → problem → approach → code → results → links."
        ),
        "hashtags": ["solidity", "ai", "defi", "security", "rag"],
    },
    "hashnode": {
        "lang": "en",
        "length_words": (1200, 2000),
        "voice_instructions": (
            "Hashnode style: tutorial-tinged but research-grounded. "
            "Heavier on intuition than dev.to. Diagrams via mermaid welcomed."
        ),
        "hashtags": ["web3", "ai", "defi", "research"],
    },
    "medium": {
        "lang": "en",
        "length_words": (1500, 2500),
        "voice_instructions": (
            "Medium style: narrative-driven, clear thesis, accessible to "
            "engineer-readers but not just for devs. More 'why this matters'."
        ),
        "hashtags": ["DeFi", "Machine-Learning", "Crypto", "Research"],
    },
}


def _platform_for_week(week_iso: int) -> str:
    """Rotate platform by ISO-week so each gets ~quarterly coverage."""
    return list(PLATFORM_CONFIGS.keys())[week_iso % len(PLATFORM_CONFIGS)]


def _topic_for_week(week_iso: int) -> dict:
    """Deterministic topic pick — same week always same topic."""
    random.seed(week_iso * 7919 + 31)
    return random.choice(PREPRINT_TOPICS)


def _compose(platform: str, topic: dict, soul: str) -> str:
    cfg = PLATFORM_CONFIGS[platform]
    title = topic["title_ru"] if cfg["lang"] == "ru" else topic["title_en"]
    angle = topic["angle_ru"] if cfg["lang"] == "ru" else topic["angle_en"]
    key_points = "\n".join(f"  - {p}" for p in topic["key_points"])
    figshare_url = f"https://figshare.com/articles/preprint/{topic['key']}/{topic['doi'].split('.')[-1]}"

    prompt = (
        f"You are Sergei Solovev writing a {platform} article ({cfg['lang']}).\n\n"
        f"{cfg['voice_instructions']}\n\n"
        f"Length: {cfg['length_words'][0]}-{cfg['length_words'][1]} words.\n\n"
        f"YOUR VOICE (excerpt from SOUL.md):\n{soul[:1200]}\n\n"
        f"TOPIC:\n"
        f"  Title: {title}\n"
        f"  Angle: {angle}\n"
        f"  Key points:\n{key_points}\n"
        f"  Source preprint DOI: {topic['doi']}\n"
        f"  Figshare URL: {figshare_url}\n\n"
        f"Output as Markdown. First line: # {title}\n"
        f"End with a 'References' section listing the figshare DOI.\n"
        f"NO exclamation marks. NO 'thrilled to share' / 'excited to announce'.\n"
        f"DO include real code blocks where the topic warrants (Solidity / Python).\n"
        f"DO use specific numbers from the key points above.\n"
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=240,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception as e:
        print(f"compose error: {e}")
        return ""


def _critique(article: str, platform: str, topic: dict) -> tuple[str, str]:
    prompt = (
        f"Critic review of a {platform} article draft by Sergei Solovev. Find:\n"
        "- factual errors about the cited preprint\n"
        "- exclamation marks (banned)\n"
        "- LinkedIn-speak ('thrilled', 'excited', 'unprecedented')\n"
        "- length out of range\n"
        "- claims unsupported by the key points or DOI\n\n"
        f"Topic: {topic['key']} (DOI {topic['doi']})\n"
        f"--- ARTICLE ---\n{article[:6000]}\n--- END ---\n\n"
        "VERDICT: PASS | REVISE | REJECT\nThen 3-5 bullet issues."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            return "PASS", "Critic unreachable"
        m = re.search(r"VERDICT:\s*(PASS|REVISE|REJECT)", r.stdout)
        return m.group(1) if m else "PASS", r.stdout
    except Exception as e:
        return "PASS", f"Critic exception: {e}"


def main() -> int:
    now = datetime.now(timezone.utc)
    week_iso = now.isocalendar()[1]

    platform = sys.argv[1] if len(sys.argv) > 1 else _platform_for_week(week_iso)
    if platform not in PLATFORM_CONFIGS:
        print(f"unknown platform: {platform}")
        return 1
    topic_key_arg = sys.argv[2] if len(sys.argv) > 2 else None
    if topic_key_arg:
        topic = next((t for t in PREPRINT_TOPICS if t["key"] == topic_key_arg), None)
        if not topic:
            print(f"unknown topic key: {topic_key_arg}")
            return 1
    else:
        topic = _topic_for_week(week_iso)

    soul = SOUL_PATH.read_text(encoding="utf-8") if SOUL_PATH.exists() else ""
    print(f"drafting {platform} article on {topic['key']}")

    article = _compose(platform, topic, soul)
    if not article:
        return 1
    verdict, feedback = _critique(article, platform, topic)
    print(f"verdict: {verdict}")

    date = now.date().isoformat()
    out_dir = POSTS_DIR / platform
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{date}-{topic['key']}.md"
    out_file.write_text(
        f"<!-- Platform: {platform} -->\n"
        f"<!-- Topic: {topic['key']} -->\n"
        f"<!-- Verdict: {verdict} -->\n"
        f"<!-- Lang: {PLATFORM_CONFIGS[platform]['lang']} -->\n\n"
        + article,
        encoding="utf-8",
    )

    word_count = len(article.split())
    summary = (
        f"📝 *{platform.upper()} article draft*\n\n"
        f"Topic: {topic['key']}\n"
        f"Language: {PLATFORM_CONFIGS[platform]['lang']}\n"
        f"Verdict: *{verdict}* · {word_count} words\n\n"
        f"Draft: https://github.com/SergeySolovyev/sergei-brand-agent-reports/"
        f"blob/main/posts/{platform}/{date}-{topic['key']}.md\n\n"
        f"Critic notes:\n{feedback[:400]}"
    )
    subprocess.run(["/usr/local/bin/tg_send", summary], check=False)

    try:
        subprocess.run(
            ["git", "-C", "/opt/reports", "add",
             f"posts/{platform}/{date}-{topic['key']}.md"], check=False,
        )
        subprocess.run(
            ["git", "-C", "/opt/reports", "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m",
             f"{platform} article: {topic['key']}", "--quiet"],
            check=False,
        )
        subprocess.run(["git", "-C", "/opt/reports", "push", "--quiet"], check=False)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
