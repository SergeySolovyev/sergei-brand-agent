---
name: learn-pattern
description: "Persistent pattern memory across sessions. Captures durable lessons from outcomes (strong_signal/rejected/etc) and replays them in downstream skills (composer, critic). GBrain-inspired."
metadata: { "openclaw": { "emoji": "🧠" } }
---

# learn-pattern

Cross-session memory layer. When a draft lands well or fails badly, this skill extracts the **durable lesson** and stores it. Downstream skills read matching patterns before drafting/reviewing similar work.

## Pattern types

| Type | Captures |
|---|---|
| `voice` | tone, word choice, register decisions that matched Sergei's brand |
| `structure` | hook shapes, paragraph flow, closer patterns that worked |
| `taboo` | what triggered Critic REJECT or human /reject (LLM tells, fake DOIs, hype) |
| `timing` | day-of-week, channel-mix, cadence that worked |

## Actions

### `capture`
After a publish outcome is settled (T+24h), extract the lesson:

1. Read `inputs.source_draft_path` — the draft text plus its frontmatter.
2. Read `inputs.outcome` (`strong_signal | weak_signal | rejected | neutral`).
3. Call LLM with system prompt that says: "Extract ONE durable lesson from this brand post that {outcome}. Output JSON with fields: pattern_type, title (<5 words), description (1-2 sentence durable lesson, generalized), applies_when (predicate), anti_example, exemplar (snippet), tags (channel/topic/audience)."
4. Insert into `patterns` SQLite table with confidence: 0.9 if strong_signal, 0.7 if rejected (negative lessons strong too), 0.5 otherwise.

### `retrieve`
Before drafting or reviewing:

1. SQL prefilter `patterns` by `confidence >= 0.6` and optional pattern_type.
2. If `inputs.query` given, ask Haiku to score each candidate 0-1 by relevance.
3. Sort by relevance, return top_k (default 5).

### `prune`
Periodic cleanup:

```sql
UPDATE patterns SET confidence = confidence * 0.9
 WHERE id IN (SELECT p.id FROM patterns p
              LEFT JOIN pattern_usage u ON p.id = u.pattern_id
              WHERE p.created_at < date('now','-90 days')
                AND COALESCE(u.use_count, 0) < 2);
DELETE FROM patterns WHERE confidence < 0.2;
```

### `list`
Dump stats by pattern_type for debugging.

## Schema

```sql
CREATE TABLE patterns (
  id INTEGER PRIMARY KEY,
  pattern_type TEXT CHECK(pattern_type IN ('voice','structure','taboo','timing')),
  title TEXT,
  description TEXT,
  applies_when TEXT,
  anti_example TEXT,
  exemplar TEXT,
  tags_json TEXT,
  source_draft_path TEXT,
  outcome TEXT,
  confidence REAL DEFAULT 0.5,
  created_at TEXT
);

CREATE TABLE pattern_usage (
  pattern_id INTEGER REFERENCES patterns(id) ON DELETE CASCADE,
  used_by_skill TEXT,
  used_at TEXT,
  use_count INTEGER DEFAULT 0,
  PRIMARY KEY (pattern_id, used_by_skill)
);
```

## Auto-invocation hooks

These should be wired in SOUL.md so the cognitive layer remembers:

- **Composer**: BEFORE drafting, call `learn-pattern` action=retrieve query=topic pattern_type=structure
- **Critic**: BEFORE reviewing, call `learn-pattern` action=retrieve query=draft_summary pattern_type=taboo
- **After publish + engagement settles (T+24h)**: call `learn-pattern` action=capture with outcome derived from engagement metrics
- **On human `/reject` in Telegram bot**: emit `capture` event with outcome=rejected so the lesson is durable

## Example flow

1. Composer drafts a LinkedIn post about LOB paper.
2. Before drafting, Composer calls `learn-pattern retrieve query="LOB mid-price prediction post for LinkedIn" pattern_type=structure top_k=3`.
3. Result: 2 prior patterns —
   - "specificity wedge" (confidence 0.85): "Lead with one counterintuitive number, e.g. 'feature ablation showed volume features HURT'"
   - "no-emoji-start" (taboo, confidence 0.7): "Never start LinkedIn post with emoji — reads as crypto-bro"
4. Composer drafts with those constraints baked in.
5. Post publishes. Engagement at T+24h: 17 reactions, 2 shares (above mean of 9, 1). Outcome = `strong_signal`.
6. Pulse skill calls `learn-pattern capture` — extracts a NEW pattern: "When LOB content opens with paradox-number, engagement +88%".
7. Pattern goes into table with confidence 0.9.
8. Next LOB-related draft, this pattern surfaces automatically.

## When NOT to invoke

- Routine acks, retries — too noisy.
- Internal-only state changes — no signal.
- Drafts that never published (no outcome to learn from).
