---
name: morning-digest
description: "Compose Sergei daily brand-pulse digest at 06:00 UTC (09:00 MSK). Rolls up last 24h events, drafts pending, discoveries, metric deltas. Writes to reports repo + sends Telegram tldr if non-empty."
metadata: { "openclaw": { "emoji": "🌅" } }
---

# morning-digest

The daily report-up from OpenClaw (24/7 runtime) → Claude (build/decision brain) → Sergei.

## Purpose

Each morning, **collect** what happened in the last 24h and **summarize** for Sergei.
This is the primary channel for `low`/`medium` severity events — they roll up here instead of pinging Sergei in real-time.

## When invoked

- **Cron**: every day at `0 6 * * *` UTC (= 09:00 MSK).
- **On-demand**: by Sergei via Telegram `/digest` command.

## Procedure

### 1. Gather data (last 24h)

Query `state.sqlite` (or wherever events are stored):

```sql
-- Events
SELECT source, kind, subject, severity, ts
FROM events
WHERE ts >= datetime('now', '-24 hours')
ORDER BY severity DESC, ts DESC;

-- Drafts created
SELECT d.draft_path, d.channel, d.topic, cv.verdict
FROM drafts d
LEFT JOIN critic_verdicts cv ON d.draft_path = cv.draft_path
WHERE d.created_at >= datetime('now', '-24 hours');

-- Discoveries (grants/CFPs/hackathons)
SELECT 'grant' as type, title, sponsor, deadline, match_score, url
  FROM grant_candidates WHERE first_seen >= date('now','-1 day') AND match_score >= 0.5
UNION ALL
SELECT 'hackathon', name, organizer, start_date, alignment_score, url
  FROM hackathon_events WHERE first_seen >= date('now','-1 day') AND alignment_score >= 0.5
UNION ALL
SELECT 'cfp', title, venue, deadline, match_score, url
  FROM cfp_calls WHERE first_seen >= date('now','-1 day') AND match_score >= 0.5;

-- Published
SELECT channel, post_url, topic, published_at FROM published
WHERE published_at >= datetime('now', '-24 hours');

-- Metric deltas (if weekly snapshot taken)
SELECT * FROM weekly_metrics_snapshot ORDER BY captured_at DESC LIMIT 2;
```

### 2. Compose digest

Call LLM (claude-cli/claude-sonnet-4-6) with system prompt:

> You are composing Sergei Solovev daily brand pulse. Tone — terse, data-first, no fluff, no "great day!" cheerleading. Sergei reads this as a status report, not a pep talk.
>
> Sections (omit if empty):
> 1. **Highlights** — 3-5 bullets, biggest deltas
> 2. **Metrics deltas** — table with arrows
> 3. **New opportunities** — top 5 from discoveries with one-liners on fit
> 4. **Published** — links to anything that went out
> 5. **Pending approval** — drafts awaiting `/approve` from Sergei
> 6. **Action items** — max 3 things Sergei should do today
>
> Max 600 words total. Markdown. No emoji-bashing.

User prompt: paste raw data from step 1.

### 3. Write to reports repo

```bash
cd /opt/reports
DATE=$(date -u +%Y-%m-%d)
mkdir -p reports/daily
cat > reports/daily/${DATE}.md <<EOF
# Daily Brand Pulse — ${DATE}

_Generated: $(date -u -Iseconds) by openclaw morning-digest_

{LLM-composed digest body here}

---

## Audit pointers
- Full event log: \`audit/$(date -u +%Y-%m)/events.jsonl\`
- Inbox items today: $(ls reports/inbox/ 2>/dev/null | grep "^$(date -u +%s -d 'yesterday')" | wc -l)
- Published this day: {count}
EOF
git add reports/daily/${DATE}.md
git -c user.name="openclaw-agent" -c user.email="agent@sergeisolovev.com" \
  commit -m "Daily digest ${DATE}"
git push origin main
```

### 4. Telegram TLDR (only if there's anything actionable)

If digest has any non-empty section in {2,3,5} (deltas, opportunities, pending approval), send a Telegram message with a short tldr (max 600 chars):

```
🌅 Morning Pulse — {DATE}

{2-3 most important bullets}

Full digest: github.com/SergeySolovyev/sergei-brand-agent-reports/blob/main/reports/daily/{DATE}.md
```

If everything is silent (`low` severity tick, no discoveries, no drafts), skip Telegram.

## Inputs

None — cron-driven. On-demand override: `lookback_hours` (default 24).

## Outputs

- `digest_path`: `reports/daily/{YYYY-MM-DD}.md`
- `telegram_message_id` (if sent)
- `events_summarized`, `discoveries_summarized`, `drafts_summarized` counts

## Failure handling

- **SQLite read fails**: write minimal digest "DB unreachable, please investigate", commit anyway, escalate via `emit-critical-event` severity=`critical`.
- **LLM fails**: write the raw data as a structured markdown (no narrative), commit, do NOT send Telegram (only Sergei reading raw is too low quality).
- **git push fails**: log to syslog, retry on next cron tick.
- **Telegram fails**: log, ignore (digest is already in repo, Sergei will see via `git pull`).

## When NOT to invoke

- More than once per day for the same date — idempotency check on `reports/daily/{date}.md` existence.
- During `emergency_pause` agent state.
