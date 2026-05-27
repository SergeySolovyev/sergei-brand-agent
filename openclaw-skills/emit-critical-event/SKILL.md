---
name: emit-critical-event
description: "Single choke-point for all brand-event emissions. Routes by severity to git (always durable) + Telegram (real-time for high/critical) + retry loop for critical. Adopted from dual-channel architecture lesson."
metadata: { "openclaw": { "emoji": "🚨" } }
---

# emit-critical-event

This is **the** choke-point. Every monitoring tick, every draft-ready notification, every discovery hit must route through here. Single point of truth for severity classification and dual-channel delivery.

## When to invoke

Whenever a skill has noticed something worth recording:
- New citation discovered (OpenAlex, Scholar, figshare downloads)
- A draft is ready, awaiting review
- Discovery hit — grant / hackathon / CFP / speaking opportunity
- Inbound mention on LinkedIn, X, GitHub, Discord, email
- Critic verdict (PASS / REVISE / REJECT)
- Runtime error or degradation

## Hard contract

1. **Always git-commit first** to `/opt/reports`. Durable record beats real-time.
2. **Then Telegram push** for severities `high` and `critical`.
3. For `critical`: enqueue retry in `~/.openclaw/ack_pending.sqlite` so a cron tick re-sends every 30 min until Sergei replies `/ack <slug>`.
4. Always append to `audit/YYYY-MM/events.jsonl` for high and critical.

Ordering matters: if Telegram succeeds but git fails, we lose durable record. Reverse is recoverable on next session.

## Severity routing

Read `/opt/reports/severity_routing.yaml` for the routing table. Quick reference:

| severity | git commit | Telegram | retry |
|---|---|---|---|
| `low`      | daily aggregate | no | none |
| `medium`   | daily aggregate | no (rolled into morning tldr) | none |
| `high`     | reports/inbox/ file | once | none |
| `critical` | reports/inbox/ file | + every 30 min | up to 4h then escalate |

### Auto-classify as `critical` when

- Citation by user with >50000 followers (Vitalik / Aave-founder tier)
- Inbound DM from verified high-signal sender requesting meeting
- MIPT / AIRI / grant deadline less than 48h with no action started
- More than 5 skill failures in last hour (runtime degraded)
- Brand violation detected (someone misrepresenting Sergei's work negatively at scale)

### Auto-classify as `high` when

- New OpenAlex citation by author with >5000 followers
- Tier-3 draft awaiting Sergei `/approve`
- Grant deadline within 7-14 days with `match_score` >= 0.7
- Inbound DM from sender with >2000 followers

## Procedure

1. Determine severity per rules above. Default to `medium` if no rule matches.

2. Generate slug from title: lowercased, ASCII-safe, max 50 chars.

3. Compute filepath:
   - high/critical → `reports/inbox/{unix}_{kind}_{slug}.md`
   - low/medium → `reports/daily/{YYYY-MM-DD}.md` (append section)

4. Pull latest reports repo:
   ```bash
   cd /opt/reports && git pull --quiet origin main
   ```

5. Write event file. For inbox (create):
   ```
   ---
   unix: {unix}
   kind: {kind}
   severity: {severity}
   detected_at: {iso}
   ---
   # {title}

   {body markdown}

   ## Suggested actions
   - `/approve {slug}-{action}` — {action description}
   ```
   For daily (append):
   ```
   ## [{iso}] {kind}: {title}

   {body}
   ```

6. Commit and push:
   ```bash
   git add {filepath}
   git -c user.name=openclaw-agent -c user.email=agent@sergeisolovev.com \
     commit -m "{severity}: {kind} — {title:60chars}"
   git push origin main
   ```

7. For high and critical: append to audit JSONL:
   ```bash
   cd /opt/reports
   MONTH=$(date -u +%Y-%m)
   mkdir -p audit/$MONTH
   echo '{"unix":...,"iso":"...","kind":"...","severity":"...","slug":"...","title":"...","filepath":"..."}' >> audit/$MONTH/events.jsonl
   git add audit/$MONTH/events.jsonl
   git commit -m "audit: log {kind}"
   git push
   ```

8. For high and critical: POST to Telegram via curl:
   ```bash
   curl -sX POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
     -d chat_id=$TELEGRAM_HOME_CHANNEL \
     -d parse_mode=Markdown \
     --data-urlencode "text=$(cat <<EOF
   {emoji} {kind}: {title}

   {body_truncated_500}

   Details: https://github.com/SergeySolovyev/sergei-brand-agent-reports/blob/main/{filepath}

   {ACK_LINE if critical}
   EOF
   )"
   ```
   `{emoji}` = 🚨 if critical, 🔔 if high.

9. For `critical`: enqueue retry row:
   ```sql
   INSERT INTO ack_pending (slug, kind, title, severity, telegram_message_id, first_sent_at, last_retry_at, retry_count, max_retries, give_up_at)
   VALUES ('{slug}', '{kind}', '{title}', 'critical', {msg_id}, '{iso}', '{iso}', 0, 6, datetime('{iso}', '+4 hours'));
   ```

10. Return `{ inbox_url, telegram_message_id, ack_required }`.

## Inputs

- `kind` (required, snake_case identifier)
- `title` (required, one-line headline)
- `body` (required, markdown body)
- `severity` (optional, explicit override)
- `slug` (optional, defaults to slugified title)
- `suggested_actions` (optional list)

## Outputs

- `inbox_url`: github link
- `telegram_message_id` (if pushed)
- `ack_required`: true for critical

## Failure handling

- **Git push fails**: log to syslog, do NOT abort. Try Telegram anyway. Retry git on next cron tick.
- **Telegram 4xx**: log, do not retry (probably malformed).
- **Telegram 5xx**: retry 3x with 60s backoff.
- **Telegram rate-limit**: sleep_and_retry per Retry-After header.

## When NOT to invoke

- Routine cron tick where nothing new is found — be silent.
- Internal self-diagnostic — write to logs/, not events.
- Completed-action confirmations — those go into `audit/decisions.jsonl`.
