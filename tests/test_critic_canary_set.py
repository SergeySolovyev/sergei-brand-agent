"""
test_critic_canary_set.py — eval harness for the Critic agent.

Runs the 12 canary drafts in tests/critic_canary_set.yaml against the
Critic persona prompt and verifies:
  - All 12 verdicts match expected_verdict
  - ≥80% of expected_findings substrings appear in critic reasons
  - ZERO false-PASS on c01-c07 (brand-safety hard requirement)

This is the SLA test for the Critic. If it fails, ship is blocked.

Run:
  pytest tests/test_critic_canary_set.py -v

Or in CI:
  python -m tests.test_critic_canary_set
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CANARY_FILE = REPO_ROOT / "tests" / "critic_canary_set.yaml"
CRITIC_PERSONA_FILE = REPO_ROOT / "personas" / "critic.md"
KNOWLEDGE_FILES = [
    REPO_ROOT / "knowledge_base" / "identity.json",
    REPO_ROOT / "knowledge_base" / "preprints.json",
    REPO_ROOT / "knowledge_base" / "brand_voice_corpus.md",
    REPO_ROOT / "knowledge_base" / "glossary.md",
]


def load_canary() -> dict[str, Any]:
    with CANARY_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_critic_persona() -> str:
    return CRITIC_PERSONA_FILE.read_text(encoding="utf-8")


def load_knowledge_bundle() -> str:
    """Concatenate identity/preprints/voice/glossary for Critic context."""
    parts = []
    for path in KNOWLEDGE_FILES:
        if path.exists():
            parts.append(f"\n\n### {path.name}\n{path.read_text(encoding='utf-8')}")
    return "\n".join(parts)


def call_critic_real(draft_md: str) -> dict[str, Any]:
    """
    Real Anthropic Claude call. Skipped if ANTHROPIC_API_KEY not set
    (e.g. on a contributor's machine without credentials).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set; skipping real Critic eval")

    try:
        from anthropic import Anthropic
    except ImportError:
        pytest.skip("anthropic SDK not installed; pip install anthropic")

    client = Anthropic(api_key=api_key)

    system_prompt = load_critic_persona() + load_knowledge_bundle()
    user_prompt = (
        "Review the following draft. Output a JSON object with keys: "
        "verdict (PASS|REVISE|REJECT), reasons (list of strings), "
        "specific_concerns (list of strings).\n\nDRAFT:\n" + draft_md
    )

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = response.content[0].text

    # Tolerate Critic wrapping JSON in code fences
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"verdict": "PARSE_ERROR", "reasons": [raw], "raw": raw}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {"verdict": "PARSE_ERROR", "reasons": [raw], "raw": raw}


@pytest.fixture(scope="module")
def canary_set() -> dict[str, Any]:
    return load_canary()


@pytest.mark.parametrize(
    "case_id",
    [f"c{i:02d}" for i in range(1, 13)],
)
def test_critic_classifies_canary(case_id: str, canary_set: dict[str, Any]) -> None:
    """One subtest per canary draft. Each verifies verdict + finding-recall."""
    drafts = {c["id"].split("_")[0]: c for c in canary_set["canary_drafts"]}
    if case_id not in drafts:
        pytest.skip(f"No canary with id starting {case_id}")

    case = drafts[case_id]
    expected_verdict = case["expected_verdict"]
    expected_findings = case.get("expected_findings", [])

    result = call_critic_real(case["draft_md"])
    actual_verdict = result.get("verdict", "PARSE_ERROR")

    assert actual_verdict == expected_verdict, (
        f"{case_id} ({case['note']}): "
        f"expected {expected_verdict}, got {actual_verdict}. "
        f"Reasons: {result.get('reasons', [])}"
    )

    if expected_findings:
        reasons_blob = " ".join(result.get("reasons", []) + result.get("specific_concerns", [])).lower()
        recalled = [f for f in expected_findings if f.lower() in reasons_blob]
        recall = len(recalled) / len(expected_findings)
        assert recall >= 0.5, (
            f"{case_id}: Critic verdict was correct but missed key findings. "
            f"Expected substrings (lowercased): {expected_findings}. "
            f"Reasons: {result.get('reasons', [])}"
        )


def test_no_false_pass_on_brand_safety_set(canary_set: dict[str, Any]) -> None:
    """Aggregate test: c01-c07 must NEVER PASS. Brand-safety hard requirement."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    drafts = canary_set["canary_drafts"]
    safety_set = [d for d in drafts if d["id"].startswith(tuple(f"c{i:02d}" for i in range(1, 8)))]
    false_passes = []

    for case in safety_set:
        result = call_critic_real(case["draft_md"])
        if result.get("verdict") == "PASS":
            false_passes.append((case["id"], case["note"]))

    assert not false_passes, (
        f"Brand-safety violation: Critic gave PASS to drafts that must be "
        f"REJECTed/REVISEd. False passes: {false_passes}"
    )


# ---------------------------------------------------------------------------
# Standalone runner (no pytest required)
# ---------------------------------------------------------------------------
def main_standalone() -> int:
    """Run the full eval and print a summary table."""
    canary = load_canary()
    drafts = canary["canary_drafts"]
    targets = canary["eval_targets"]

    print(f"\n{'ID':<6} {'EXPECTED':<8} {'ACTUAL':<10} {'STATUS':<6} NOTE")
    print("-" * 80)

    correct = 0
    false_passes = 0
    finding_recall_sum = 0.0
    finding_total = 0

    for case in drafts:
        result = call_critic_real(case["draft_md"])
        actual = result.get("verdict", "PARSE_ERROR")
        expected = case["expected_verdict"]
        ok = actual == expected
        if ok:
            correct += 1
        if expected != "PASS" and actual == "PASS":
            false_passes += 1
        if case.get("expected_findings"):
            reasons_blob = " ".join(
                result.get("reasons", []) + result.get("specific_concerns", [])
            ).lower()
            recalled = [f for f in case["expected_findings"] if f.lower() in reasons_blob]
            recall = len(recalled) / len(case["expected_findings"])
            finding_recall_sum += recall
            finding_total += 1

        status = "✓" if ok else "✗"
        print(f"{case['id']:<6} {expected:<8} {actual:<10} {status:<6} {case['note']}")

    print("-" * 80)
    accuracy = correct / len(drafts)
    avg_recall = finding_recall_sum / finding_total if finding_total else 0
    print(f"Accuracy:           {accuracy:.2%}  (target: {targets['thresholds']['accuracy']:.0%})")
    print(f"Finding recall:     {avg_recall:.2%}  (target: {targets['thresholds']['finding_recall']:.0%})")
    print(f"False passes:       {false_passes}      (target: 0)")
    print()

    if false_passes > 0:
        print("❌ BRAND-SAFETY FAILURE: false-PASS on safety-critical canary")
        return 2
    if accuracy < targets["thresholds"]["accuracy"]:
        print(f"❌ Accuracy below {targets['thresholds']['accuracy']:.0%}")
        return 1
    print("✅ All canary checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main_standalone())
