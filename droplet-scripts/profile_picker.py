"""profile_picker — LLM picks the right identity profile for an inbound context.

Reads /opt/brand-agent/knowledge_base/identity.json, sends the email
sender+subject+body excerpt to Haiku, returns:

    { "profile_key": "academic_hse", "confidence": 0.9,
      "reasoning": "academic research webinar with quant topic" }

The picker_principle baked into identity.json biases the LLM toward
academic_hse unless there's a strong non-academic signal.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

IDENTITY_PATH = Path("/opt/brand-agent/knowledge_base/identity.json")


def _load_identity() -> dict:
    return json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))


def pick(sender: str, subject: str, body: str) -> dict:
    identity = _load_identity()
    profiles = identity.get("profiles", {})
    default = identity.get("default_profile", list(profiles.keys())[0])
    principle = identity.get(
        "_picker_principle",
        "Pick the profile whose use_for keywords best match the context.",
    )

    # Deterministic sender_overrides — skip LLM if sender domain matches
    overrides = {
        k.lower(): v for k, v in identity.get("sender_overrides", {}).items()
        if not k.startswith("_")
    }
    sender_lower = (sender or "").lower()
    for domain, forced_profile in overrides.items():
        if domain in sender_lower and forced_profile in profiles:
            return {
                "profile_key": forced_profile,
                "confidence": 1.0,
                "reasoning": f"sender_override: {domain} → {forced_profile}",
            }

    # Compact profile summary for the prompt
    profile_summary = []
    for key, p in profiles.items():
        profile_summary.append(
            f"- {key}: {p.get('label', '')} | use_for: "
            f"{', '.join(p.get('use_for', [])[:8])}"
        )

    prompt = (
        "Pick the right identity profile for Sergei Solovev given an inbound message.\n\n"
        f"Picker principle: {principle}\n\n"
        f"Profiles available:\n{chr(10).join(profile_summary)}\n\n"
        f"Default if uncertain: {default}\n\n"
        f"Inbound message:\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Body excerpt: {body[:800]}\n\n"
        'Respond with ONLY a JSON object: '
        '{"profile_key":"<key>","confidence":<0..1>,"reasoning":"<10 words>"}'
    )
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", "claude-haiku-4-5", prompt],
            capture_output=True, text=True, timeout=25,
        )
        if result.returncode != 0:
            return {"profile_key": default, "confidence": 0.5,
                    "reasoning": "LLM failed — using default"}
        m = re.search(r"\{[^{}]+\}", result.stdout)
        if not m:
            return {"profile_key": default, "confidence": 0.5,
                    "reasoning": "could not parse LLM response"}
        out = json.loads(m.group(0))
        if out.get("profile_key") not in profiles:
            out["profile_key"] = default
            out["reasoning"] = f"unknown key, fell back. {out.get('reasoning','')}"
        return out
    except Exception as e:
        return {"profile_key": default, "confidence": 0.0,
                "reasoning": f"picker exception: {e}"}


def get_profile(key: str) -> dict:
    """Return profile dict with globals merged in."""
    identity = _load_identity()
    p = dict(identity["profiles"][key])
    p.update({"globals": identity.get("globals", {})})
    p["phone_policy"] = identity.get("phone_policy", "never_provide_escalate_if_required")
    p["marketing_opt_out"] = identity.get("marketing_opt_out", True)
    return p


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        out = pick(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        msg = json.loads(sys.stdin.read())
        out = pick(msg.get("sender", ""), msg.get("subject", ""), msg.get("body", ""))
    print(json.dumps(out, ensure_ascii=False, indent=2))
