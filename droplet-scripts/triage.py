#!/usr/bin/env python3
"""triage — VIP-aware inbound classifier.

Used by email_triage_gmail.py, telegram_user_monitor.py, and any other
inbound source. Returns a structured decision:

    {
      "decision": "skip" | "engage" | "escalate",
      "severity": "low" | "medium" | "high" | "critical",
      "reason":   "short human-readable why",
      "tags":     ["grant", "deadline", "vip_tier_S", ...]
    }

Priority logic (deterministic before LLM):
  1. Sender on tier_S_critical or russian_ecosystem_critical → escalate/critical
  2. Subject contains any domain_terms_critical → escalate/critical
  3. Subject mentions a known deadline keyword + dates near our deadlines → escalate/high
  4. Sender on tier_A_high → engage/high
  5. Sender on tier_B_medium → engage/medium
  6. Otherwise → cheap LLM (claude-cli haiku) for skip vs engage

Fallback if LLM unreachable: default to engage/low so nothing is dropped silently.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

VIP_PATH = Path("/opt/brand-agent/knowledge_base/vip_authors.json")


def _load_vip() -> dict:
    if not VIP_PATH.exists():
        return {}
    try:
        return json.loads(VIP_PATH.read_text())
    except Exception:
        return {}


def _normalize_handle(s: str) -> str:
    """Lowercase + strip @ + strip whitespace for handle comparison."""
    return (s or "").lower().strip().lstrip("@")


def _sender_tier(sender: str, vip: dict) -> tuple[str | None, str]:
    """Return (tier_name, why) if sender matches a VIP entry, else (None, '')."""
    s = _normalize_handle(sender)
    if not s:
        return None, ""
    # Sender can be "Vitalik Buterin <vitalik@example.com>" or @handle
    candidates = {s}
    # Email part
    m = re.search(r"([\w.+-]+)@", s)
    if m:
        candidates.add(m.group(1))
    # @handle
    m = re.search(r"@(\w+)", s)
    if m:
        candidates.add(m.group(1))

    for tier_name, entries in vip.items():
        if not tier_name.startswith("tier_") and tier_name not in (
            "russian_ecosystem_critical",
        ):
            continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            handle = _normalize_handle(entry.get("handle", ""))
            if handle and handle in candidates:
                return tier_name, entry.get("why", "")
    return None, ""


def _contains_domain_term(text: str, vip: dict) -> str | None:
    """Return the first domain term matched, or None."""
    terms = vip.get("domain_terms_critical", {}).get(
        "auto_critical_if_text_contains_any", []
    )
    t = (text or "").lower()
    for term in terms:
        if term.lower() in t:
            return term
    return None


def _cheap_llm_decision(subject: str, snippet: str, sender: str) -> dict | None:
    """Ask claude-cli (haiku) for a skip/engage call. Returns None on failure."""
    prompt = (
        "You are triaging an inbound email for Sergei Solovev "
        "(HSE FCS researcher, DeFi/AI, TradFi→AI→DeFi; lives in Moscow).\n\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Snippet: {snippet[:600]}\n\n"
        "Decide skip vs engage. ENGAGE (surface to Sergei) if the email is ANY of:\n"
        "  • An opportunity: grant, CFP, hackathon, conference invite, job/collab, "
        "speaking/interview/podcast request, citation of his work\n"
        "  • Actionable & personal: a BILL or payment due, invoice, official/government "
        "notice, tax, university/HSE admin, visa/document, account-security alert, "
        "a real deadline, a reply from a real person who knows him\n"
        "  • Anything where missing it has real consequences (money, deadline, relationship)\n"
        "SKIP only if it is clearly promotional/newsletter/marketing/automated-digest "
        "with no action needed.\n\n"
        "Severity: high = money/deadline/official within days · medium = opportunity or "
        "personal reply · low = mildly useful FYI.\n"
        "HARD RULE: if severity is high or medium, decision MUST be engage (never skip "
        "something important).\n\n"
        'Respond with ONLY JSON: {"decision":"skip|engage","severity":"low|medium|high","reason":"<10 words>"}'
    )
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", "claude-haiku-4-5", prompt],
            capture_output=True,
            text=True,
            timeout=25,
        )
        if result.returncode != 0:
            return None
        m = re.search(r"\{[^{}]+\}", result.stdout)
        if not m:
            return None
        d = json.loads(m.group(0))
        # Consistency guard: a high/medium-severity "skip" is a logic error
        # (e.g. an insurance bill flagged high but marked skip). Promote to engage.
        if d.get("decision") == "skip" and d.get("severity") in ("high", "medium"):
            d["decision"] = "engage"
            d["reason"] = "auto-promoted: " + d.get("reason", "important")
        return d
    except Exception:
        return None


def triage(sender: str, subject: str, body: str) -> dict[str, Any]:
    """Main entry point. Returns decision dict (see module docstring)."""
    vip = _load_vip()
    text_for_terms = f"{subject}\n{body[:1000]}"

    # Rule 1: domain term match → critical
    term = _contains_domain_term(text_for_terms, vip)
    if term:
        return {
            "decision": "escalate",
            "severity": "critical",
            "reason": f"contains domain-critical term: {term}",
            "tags": ["domain_critical", term],
        }

    # Rule 2: sender tier match
    tier, why = _sender_tier(sender, vip)
    if tier == "tier_S_critical" or tier == "russian_ecosystem_critical":
        return {
            "decision": "escalate",
            "severity": "critical",
            "reason": f"sender on {tier}: {why}",
            "tags": [tier, "vip_sender"],
        }
    if tier == "tier_A_high":
        return {
            "decision": "engage",
            "severity": "high",
            "reason": f"sender on {tier}: {why}",
            "tags": [tier, "vip_sender"],
        }
    if tier == "tier_B_medium_for_engagement":
        return {
            "decision": "engage",
            "severity": "medium",
            "reason": f"sender on {tier}: {why}",
            "tags": [tier, "vip_sender"],
        }

    # Rule 3: cheap LLM classifier
    llm = _cheap_llm_decision(subject, body, sender)
    if llm:
        llm.setdefault("tags", ["llm_classified"])
        return llm

    # Fallback: don't drop on LLM failure
    return {
        "decision": "engage",
        "severity": "low",
        "reason": "fallback — LLM unreachable, default to engage/low",
        "tags": ["fallback"],
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        out = triage(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        # JSON on stdin
        msg = json.loads(sys.stdin.read())
        out = triage(msg.get("sender", ""), msg.get("subject", ""), msg.get("body", ""))
    print(json.dumps(out, ensure_ascii=False, indent=2))
