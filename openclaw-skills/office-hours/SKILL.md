---
name: office-hours
description: "YC-style 6-forcing-questions session that challenges a content idea BEFORE drafting. Adopted from Garry Tan GStack pattern. Output - verdict + structured brief for downstream composer."
metadata: { "openclaw": { "emoji": "🎯" } }
---

# office-hours

The forcing function that prevents writing the **obvious** post instead of the **right** post.

## When to invoke

- BEFORE any content draft (LinkedIn, X, blog, Telegram). No exception.
- BEFORE submitting a grant or hackathon application.
- When Sergei says "I should post about X" — challenge the framing FIRST.

## Modes

### challenge_mode (default)
Adversarial. Interrogative. Uncomfortable by design.
**Goal**: kill weak ideas before they consume attention.

### generative_mode
Collaborative. Used when expanding an already-validated direction into concrete posts.

## The 6 YC forcing questions

For challenge_mode, work through these IN ORDER. Document each.

### 1. DEMAND REALITY
Whose specific Twitter/LinkedIn/email inbox would react to this with "finally, someone said it"?
If you can NOT name the specific persona, the idea is weak — stop here.

### 2. STATUS QUO
What does that persona currently do without this post?
Is your post 10× better than their current alternative, or 1.2×?
1.2× doesn't move anyone — push for 10×.

### 3. DESPERATE SPECIFICITY
Replace every abstract term with a concrete one:
- Not "DeFi protocols" — "Aave v3 borrowers on Base who got liquidated last month"
- Not "AI agents" — "Python script with Anthropic API and 2 MCP tools"
- Not "researchers" — "PhD students in smart-contract security working on Solidity vuln detection"

### 4. NARROWEST WEDGE
If the reader walks away remembering ONE sentence, what is it?
Write that sentence in under 20 words.
If you can not — the idea is too broad.

### 5. OBSERVATION AND SURPRISE
What does Sergei know that the audience does not?
What is the surprising bit — the line that makes them forward it?
If there is no surprise, it is a corporate blog post. Kill it.

### 6. FUTURE-FIT
In 3 months, will Sergei look back at this post and think "that landed something"?
Or "that was throwaway"?
If throwaway — kill now.

## Procedure

1. Read context: `/opt/brand-agent/knowledge_base/identity.json`, `preprints.json`, `brand_voice_corpus.md`, `glossary.md`, `promotion_playbook.md`.
2. Query state.sqlite for `published` table — last 30 days, to know what was already covered.
3. Query state.sqlite for `grant_candidates`, `hackathon_events`, `cfp_calls` — deadlines that could be hooked into.
4. Apply 6 questions to the raw request. Output structured JSON with all 6 question results plus an `overall_verdict` of one: `proceed_strong | proceed_weak | kill | reframe_required`.
5. If verdict is `proceed_strong` or `proceed_weak`, produce a brief for the composer with these fields: narrowest_wedge, target_audience, pain_addressed, falsifiable_premises (list), recommended_channels (list), recommended_hook_angles (list of: counterintuitive_finding | tactical_takeaway | framework | before_after | case_study), what_NOT_to_do (list), success_signal (single measurable signal).
6. Write the full session to `data/plans/office_hours/{unix}-{slug}.md`.
7. Commit to brand-agent repo: `cd /opt/brand-agent && git add data/plans/office_hours/ && git commit && git push`.
8. Emit `office_hours_complete` event via `emit-critical-event` skill with severity=`low` (just goes into daily digest).

## Examples to challenge

**INPUT**: "Write a LinkedIn post about my new AI-Yield-Vault preprint"
**LIKELY OUTPUT**: `proceed_weak` — the preprint is technically interesting but a generic "I wrote a paper" post will not move CTOs. **Reframe**: "Why most ERC-4626 vaults skip MCDM (and one we built that uses it)" — narrower wedge, surprise embedded.

**INPUT**: "I should be more active on X about smart contract auditing"
**LIKELY OUTPUT**: `reframe_required` — too vague. Push for concrete: "Post 1 thread per week about ONE Solidity bug pattern XGBoost caught that human auditors missed."

**INPUT**: "Make a thread about the LOB paper"
**LIKELY OUTPUT**: `proceed_strong` IF narrowest_wedge is "Weighted Pearson rho_w = 0.266 with feature ablation showing volume features HURT" — that is counterintuitive and specific.

## When NOT to invoke

- Replying to a single mention in DM — overhead too high.
- Daily routine ack messages.
- Internal-only state writes.
