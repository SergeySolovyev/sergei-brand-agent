---
name: triage-mention
description: "Triage an inbound mention from any channel (X, LinkedIn, GitHub, Discord, email, Telegram). Classifies into engage/ignore/escalate using Haiku-cheap pre-filter, then routes to appropriate downstream skill."
metadata: { "openclaw": { "emoji": "🔍" } }
---

# triage-mention

The traffic cop for ALL inbound signals. Cheaply filter noise from real opportunities.

## When invoked

- `monitor` skill (every 4 hours) detects a new mention → calls this for each.
- Telegram DM arrives from non-Sergei user → call this on it.
- GitHub issue/PR mentions Sergei → call this.
- New email arrives matching watch-list (himalaya skill) → call this.

## Procedure

### Step 1 — extract context

Read mention from inbox payload:
- `mention_url` — original message location
- `platform` — x | linkedin | github | discord | telegram | email | reddit | hn
- `author` — handle + display name + follower_count if known
- `text` — the actual message body
- `parent_text` — surrounding thread (if applicable)
- `attachments` — file refs if any

### Step 2 — cheap pre-classify (Haiku call, ~$0.003)

Prompt to claude-haiku-4-5:

> You decide whether to act on this mention or skip it.
>
> **Skip** when:
> - Spam, promotional bait, generic newsletter
> - Hostile, bad-faith tone
> - Off-topic (politics, divisive, unrelated to Sergei's lane)
> - Auto-generated bot reply with no signal
> - Already replied (check published table)
>
> **Engage** when:
> - Genuine technical question Sergei can answer well
> - Citation of Sergei's work that benefits from contextualization
> - Researcher introducing themselves / suggesting collaboration
> - Constructive critique of Sergei's research
> - Investor / commercial inquiry (high signal)
> - Conference / podcast invitation
>
> **Escalate immediately** (severity=critical):
> - Verified high-signal sender (>50k followers OR known investor)
> - Time-sensitive opportunity (deadline <48h)
> - Brand emergency (someone misrepresenting Sergei work negatively at scale)
>
> Output JSON:
> `{ decision: skip|engage|escalate, reason: str, suggested_intent: enum, urgency: low|medium|high }`

### Step 3 — route based on decision

| Decision | Action |
|---|---|
| `skip` | Log to `audit/{YYYY-MM}/triage-skipped.jsonl`. No further action. |
| `engage` | Hand off to `reply-to-mention` skill (Tier 3 — drafts reply, awaits `/approve`). |
| `escalate` | Call `emit-critical-event` skill with severity=`critical`, kind=`inbound_high_signal`. |

### Step 4 — record decision (always)

Append to `audit/{YYYY-MM}/triage-decisions.jsonl`:
```json
{ "ts": "...", "mention_url": "...", "decision": "...", "reason": "...", "haiku_cost_usd": 0.003 }
```

This lets us later analyze triage accuracy (when Sergei manually reads a "skipped" one and disagrees).

## Inputs

- `mention_url` (required)
- `platform` (required, enum above)
- `author` (required, dict with handle/followers/bio if available)
- `text` (required)
- `parent_text` (optional)
- `force_escalate` (optional bool, for hard rules like "this DM is from a known investor")

## Outputs

- `decision`: skip | engage | escalate
- `reason`: human-readable
- `suggested_intent`: add_value | clarify | agree_with_nuance | gently_correct | decline_politely | acknowledge_only
- `routed_to`: name of downstream skill invoked
- `haiku_cost_usd`: tracked for daily budget rollup

## Hard-coded escalation triggers (skip Haiku, jump directly to escalate)

- `author.handle` is in `/opt/brand-agent/knowledge_base/vip_authors.json`
- `author.follower_count` > 50000 AND `platform` in [x, linkedin]
- Text contains regex `\b(invest|investment|funding|seed|series A|angel)\b` AND author is verified
- Text contains regex `\b(deadline|due|by tomorrow|by Friday)\b`
- Platform = email AND sender domain matches known fund/grant org

## Cost discipline

- Cheap pre-filter (Haiku) ≈ $0.003 per mention
- Skip → free
- Engage → ~$0.04 (Sonnet drafts the reply)
- Escalate → ~$0.005 (just emit + Telegram)

Daily budget cap: 50 triages = $0.15-2.00 depending on engage rate.

## When NOT to invoke

- For known internal events (cron heartbeat, self-diagnostic) — never run triage on those.
- For Sergei replying TO an existing thread — different skill (`thread-continuation`).
