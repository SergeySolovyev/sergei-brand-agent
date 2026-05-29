"""coverage_report — measure what % of 120+ promotion tactics is automated.

Output: /opt/reports/dashboard/coverage.md — consumed by dashboard.py
to render a Pipeline Coverage section.

Categorization scheme:
  🟢 active        — autonomous drafter/skill exists + fires on triggers
  🟡 drafted_only  — drafter exists, manual publish (waiting on unblocker)
  🔵 schedulable   — could be autonomously built; on backlog
  🔴 blocked       — requires Sergei action (cookie, account, login)
  ⚪ deferred      — strategic/long-term, not next-step

Run from cron weekly. Result feeds dashboard's "Tactics coverage" panel.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# ───────────────────────────────────────────────────────────────────────
# Coverage map — each tactic → (status, drafter/skill name, notes)
# ───────────────────────────────────────────────────────────────────────
TACTICS = {
    # Category 1 — Owned media
    "1.1 sergeisolovev.com blog":           ("yellow", "blog_generator (cron Mon 10:00 UTC)"),
    "1.2 Case studies":                     ("blue",   "case_study_drafter (TODO when grant funded)"),
    "1.3 Newsletter Substack/beehiiv":      ("red",    "needs Substack account + API token"),
    "1.4 RSS / Atom feed":                  ("green",  "already deployed at /feed.xml"),
    "1.5 Personal podcast":                 ("deferred","heavy production, deferred to phase 4"),
    "1.6 Notion/Obsidian Publish garden":   ("blue",   "obsidian_drafter (TODO)"),
    "1.7 Calendly booking page":            ("red",    "needs Calendly account"),
    "1.8 Lead magnet ERC-4626 checklist":   ("blue",   "lead_magnet_generator (TODO)"),
    "1.9 Lead magnet RAG eval notebook":    ("blue",   "lead_magnet_generator (TODO)"),

    # Category 2 — Academic identity
    "2.1 Google Scholar":                   ("red",    "task #24, manual setup"),
    "2.2 ORCID":                            ("red",    "task #53"),
    "2.3 ResearchGate":                     ("red",    "account setup"),
    "2.4 Academia.edu":                     ("red",    "account setup"),
    "2.5 Semantic Scholar":                 ("yellow", "citation_digest pulls citations, indexed via API"),
    "2.6 OpenAlex":                         ("green",  "monitored by agent_monitor 30min"),
    "2.7 dblp":                             ("blue",   "dblp_claim helper (TODO)"),
    "2.8 HSE FCS faculty page":             ("red",    "needs HSE webmaster contact"),
    "2.9 RINC author profile":              ("red",    "manual claim"),
    "2.10 arXiv author ID":                 ("yellow", "task #15 batch submit"),

    # Category 3 — Code portfolios
    "3.1 GitHub profile (magic repo)":      ("green",  "task #32 done"),
    "3.2 GitHub pinned repos":              ("blue",   "pin_optimizer (TODO)"),
    "3.3 GitHub Sponsors":                  ("red",    "needs account opt-in"),
    "3.4 HuggingFace profile":              ("blue",   "hf_publisher (TODO, has API)"),
    "3.5 Kaggle profile":                   ("yellow", "task #12 done, no auto-publish"),
    "3.6 GitLab mirror":                    ("blue",   "gitlab_mirror (TODO autonomous)"),
    "3.7 Codeberg mirror":                  ("blue",   "codeberg_mirror (TODO autonomous)"),
    "3.8 Replit profile":                   ("deferred","low ROI"),
    "3.9 npm/PyPI published packages":      ("blue",   "pypi_publisher (TODO, no auth needed for own packages)"),
    "3.10 Awesome-list contribution":       ("blue",   "🆕 awesome_list_pr_drafter — building now"),
    "3.11 GitHub star-list curation":       ("blue",   "star_curator (TODO)"),

    # Category 4 — Long-form social (EN)
    "4.1 LinkedIn newsletter":              ("red",    "blocked: LinkedIn cookie #52"),
    "4.2 LinkedIn personal feed":           ("yellow", "daily_commentary drafts, publish blocked on cookie"),
    "4.3 LinkedIn carousels":               ("red",    "blocked: LinkedIn cookie"),
    "4.4 LinkedIn videos":                  ("deferred","heavy production"),
    "4.5 Substack publication":             ("red",    "needs Substack account"),
    "4.6 Medium publication":               ("blue",   "medium_publisher (TODO, has API)"),
    "4.7 Mirror.xyz":                       ("red",    "needs wallet sign-in"),
    "4.8 Paragraph.xyz":                    ("red",    "needs wallet sign-in"),

    # Category 5 — Developer long-form
    "5.1 dev.to":                           ("blue",   "🆕 devto_article_drafter — building now"),
    "5.2 Hashnode":                         ("blue",   "hashnode_drafter (TODO, has API)"),
    "5.3 In Plain English Medium pubs":     ("deferred","editorial submission"),
    "5.4 freeCodeCamp News":                ("deferred","editorial submission"),
    "5.5 Hacker Noon":                      ("deferred","editorial submission"),
    "5.8 Towards Data Science":             ("deferred","editorial submission"),
    "5.9 Cointelegraph guest column":       ("deferred","editorial pitch"),
    "5.10 The Block / Decrypt research":    ("deferred","editorial pitch"),

    # Category 6 — Short-form social (EN)
    "6.1 X / Twitter feed":                 ("yellow", "drafts via daily_commentary, publish blocked #57"),
    "6.2 X threads":                        ("yellow", "thread_drafter (TODO), publish blocked"),
    "6.3 X Spaces":                         ("deferred","manual live event"),
    "6.4 BlueSky":                          ("blue",   "🆕 bluesky_poster — building now (app password, easier than X)"),
    "6.5 Mastodon":                         ("blue",   "mastodon_poster (TODO, app token)"),
    "6.6 Threads (Meta)":                   ("red",    "no public API"),

    # Category 7 — Web3-native social
    "7.1 Farcaster account":                ("blue",   "farcaster_poster (TODO, has API via Neynar)"),
    "7.2 Farcaster Frames":                 ("deferred","complex production"),
    "7.3 Lens Protocol":                    ("red",    "needs wallet signing"),
    "7.4 ENS domain sergeisolovev.eth":     ("red",    "needs ETH wallet + registration"),

    # Category 8 — Russian/CIS platforms
    "8.1 Telegram own channel":             ("yellow", "drafts ready, blocked on #54 channel creation"),
    "8.2 TG active community participation":("blue",   "tg_community_helper via Telethon (TODO)"),
    "8.3 Habr article publication":         ("blue",   "🆕 habr_article_drafter — building now"),
    "8.4 VK (ВКонтакте) page":              ("red",    "needs VK account + API token"),
    "8.5 Tinkoff Journal expert column":    ("deferred","editorial pitch"),
    "8.6 Yandex.Zen channel":               ("deferred","Дзен largely sunset"),
    "8.7 РБК / Forbes Russia expert quote": ("blue",   "pressfeed_responder (TODO)"),
    "8.8 Pressfeed.ru expert profile":      ("blue",   "pressfeed_responder (TODO)"),
    "8.10 Russian DAO governance":          ("deferred","strategic, low automation potential"),

    # Category 9 — Q&A discussions
    "9.1 Stack Overflow answers":           ("blue",   "stackex_monitor (TODO autonomous draft)"),
    "9.2 Ethereum Stack Exchange":          ("blue",   "🆕 ethereum_stackex_monitor — building now"),
    "9.3 Crypto Stack Exchange":            ("blue",   "stackex_monitor (TODO)"),
    "9.4 Cross Validated":                  ("blue",   "stackex_monitor (TODO)"),
    "9.5 Hacker News submissions":          ("blue",   "hn_submission_drafter (TODO)"),
    "9.6 Lobste.rs":                        ("deferred","invite-only"),
    "9.7 Reddit r/ethereum etc.":           ("red",    "Reddit cookie needed"),

    # Categories 10-15 abbreviated for space
    "13.1 Invited university talks":        ("blue",   "conference_proposal_drafter handles"),
    "13.2 Conference paper presentation":   ("green",  "conference_proposal_drafter active"),
    "14.1 ETHGlobal hackathon":             ("yellow", "task #58 ETHOnline in progress"),
    "15.6 OpenReview peer review":          ("blue",   "openreview_monitor (TODO, has API)"),

    # Category 17 — Open source assets
    "17.1 Public dataset release":          ("blue",   "figshare_publisher (TODO, has token)"),
    "17.4 Python library PyPI":             ("blue",   "pypi_publisher (TODO)"),

    # Category 19 — Grants
    "19.1 ETH Foundation Academic Grants":  ("green",  "grant_application_drafter active"),
    "19.2 ETH Foundation ESP":              ("green",  "grant_application_drafter active"),
    "19.4 Protocol grants":                 ("green",  "grant_application_drafter active"),
    "19.5 Russian grants (РНФ/ФСИ)":        ("green",  "ru_grants_scanner + drafter active"),

    # Category 20 — Hackathons
    "20.1 ETHGlobal events":                ("green",  "agent_discover + ETHGlobal calendar"),
    "20.3 DoraHacks bounties":              ("yellow", "scanner broken — needs fix"),

    # Category 22 — Press / Media
    "22.1 HARO replies":                    ("blue",   "haro_responder (TODO, via Gmail inbox)"),
    "22.3 Pressfeed.ru":                    ("blue",   "pressfeed_responder (TODO)"),
    "22.8 Wikipedia author page":           ("blue",   "wikipedia_draft_drafter (TODO when notable)"),
    "22.10 Industry analyst engagement":    ("deferred","strategic, manual"),

    # Category 23 — Partnership
    "23.1 Co-authored papers":              ("deferred","strategic, requires real research collab"),
    "23.5 Cross-promotion swaps":           ("deferred","manual relationships"),

    # Category 24 — Direct outreach
    "24.1 Cold email to clients":           ("yellow", "cold_outreach_drafter (TODO, drafts only)"),
    "24.3 Cold reach to journalists":       ("blue",   "journalist_outreach_drafter (TODO)"),
    "24.4 DM podcast hosts":                ("red",    "blocked: Twitter/LinkedIn cookie"),

    # Category 26 — SEO
    "26.1 Sitemap submission":              ("green",  "task #26 done"),
    "26.2 IndexNow":                        ("green",  "task #29 done"),
    "26.3 Schema.org JSON-LD":              ("green",  "task #30 done"),
    "26.4 Citation meta tags":              ("green",  "task #25 done"),
    "26.5 Backlink building":               ("blue",   "backlink_tracker via Search Console (TODO)"),
    "26.6 Wikipedia citation":              ("blue",   "🆕 wikipedia_citation_finder — building now"),

    # Category 27 — Trust signals
    "27.5 GitHub verified domain":          ("green",  "done"),
    "27.6 figshare ORCID":                  ("yellow", "task #31 partial, needs #53"),
}


def _status_emoji(s: str) -> str:
    return {
        "green":    "🟢",
        "yellow":   "🟡",
        "blue":     "🔵",
        "red":      "🔴",
        "deferred": "⚪",
    }.get(s, "❓")


def _summary() -> dict:
    counts = {"green": 0, "yellow": 0, "blue": 0, "red": 0, "deferred": 0}
    for _, (status, _) in TACTICS.items():
        counts[status] = counts.get(status, 0) + 1
    total = sum(counts.values())
    return {
        "total": total,
        "counts": counts,
        "active_pct":      round(counts["green"]   / total * 100, 1),
        "drafted_pct":     round(counts["yellow"]  / total * 100, 1),
        "buildable_pct":   round(counts["blue"]    / total * 100, 1),
        "blocked_pct":     round(counts["red"]     / total * 100, 1),
        "deferred_pct":    round(counts["deferred"]/ total * 100, 1),
    }


def render_markdown() -> str:
    summary = _summary()
    md = [
        "# Brand Promotion Coverage Report",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "## Summary",
        f"- **Total mapped tactics**: {summary['total']} (of 120+ in playbook)",
        f"- 🟢 **Active** (autonomous + firing):     {summary['counts']['green']} ({summary['active_pct']}%)",
        f"- 🟡 **Drafted only** (Sergei publishes):  {summary['counts']['yellow']} ({summary['drafted_pct']}%)",
        f"- 🔵 **Buildable** (autonomous, on roadmap): {summary['counts']['blue']} ({summary['buildable_pct']}%)",
        f"- 🔴 **Blocked** (needs Sergei action):    {summary['counts']['red']} ({summary['blocked_pct']}%)",
        f"- ⚪ **Deferred** (strategic/manual):       {summary['counts']['deferred']} ({summary['deferred_pct']}%)",
        "",
        "## Detail",
        "",
        "| Tactic | Status | Skill / Notes |",
        "|---|---|---|",
    ]
    for name, (status, notes) in TACTICS.items():
        md.append(f"| {name} | {_status_emoji(status)} | {notes} |")
    return "\n".join(md)


def render_json() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": _summary(),
        "tactics": {
            name: {"status": status, "notes": notes}
            for name, (status, notes) in TACTICS.items()
        },
    }


def main() -> int:
    out_dir = Path("/opt/reports/dashboard")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "coverage.md").write_text(render_markdown(), encoding="utf-8")
    (out_dir / "coverage.json").write_text(
        json.dumps(render_json(), ensure_ascii=False, indent=2), encoding="utf-8",
    )
    summary = _summary()
    print(
        f"coverage: green={summary['counts']['green']} "
        f"yellow={summary['counts']['yellow']} "
        f"blue={summary['counts']['blue']} "
        f"red={summary['counts']['red']} "
        f"deferred={summary['counts']['deferred']} "
        f"/ {summary['total']}"
    )
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
