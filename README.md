# sergei-brand-agent

> Autonomous AI agent that promotes Sergei Solovev's personal commercial brand.
> Hermes Agent foundation · Triad (Strategist + Composer + Critic) · Browser-Use
> + Anthropic Computer Use · RentAHuman MCP escalation · Anthropic Managed Agents
> harness pattern · VPS-deployed in Docker sandbox.

## Goal

Establish Sergei's technical authority in the eyes of: potential commercial
clients of his DeFi and ML products, grant committees (Russian innovation funds,
ETH Foundation, crypto research grants), DeFi investors (VCs, angels, ecosystem
treasuries), and the academic community. Grow `sergeisolovev.com` as the
central hub.

## Architecture (3 layers)

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: COGNITIVE AGENTS (3 LLM personas, event-triggered)     │
│   personas/strategist.md  ─  weekly orchestrator                │
│   personas/composer.md    ─  channel-aware writer (blog/LI/X/TG)│
│   personas/critic.md      ─  adversarial reviewer               │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: TOOL CAPABILITIES                                      │
│   Browser-Use  ─  universal channel access (LinkedIn, X, etc.)  │
│   Anthropic Computer Use  ─  desktop fallback                   │
│   MCP servers  ─  GitHub, Telegram, filesystem, SQLite          │
│   RentAHuman MCP  ─  judgment escalation                        │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: HARNESS (Anthropic Managed Agents pattern)             │
│   Session · Sandbox · Trace/Eval · Credentials · Context        │
└─────────────────────────────────────────────────────────────────┘
```

Applies 5 Anthropic patterns: Orchestrator-Workers (Strategist → Composer/Critic),
Evaluator-Optimizer (Composer ↔ Critic loop), Routing (channel-specific sub-personas
inside Composer), Parallelization (discovery scans), Prompt Chaining (sense → think → act).

## Directory layout

```
sergei-brand-agent/
├── SOUL.md                              ← identity (5-10 line USER section TODO)
├── personas/                            ← 3 cognitive agent prompts
├── knowledge_base/                      ← pre-ingested assets + playbook (120+ tactics)
│   ├── identity.json                    ← from JSON-LD Person + CV
│   ├── preprints.json                   ← from BIBTEX_ENTRIES.bib
│   ├── brand_voice_corpus.md            ← past writing for tone-matching
│   ├── glossary.md                      ← preferred terms + BANNED phrases
│   └── promotion_playbook.md            ← 120+ tactics catalog
├── skills/                              ← agentskills.io-compatible YAMLs
│   ├── monitoring/                      ← check_research_visibility, etc.
│   ├── discovery/                       ← scan_cfp_calls, scan_grants, etc.
│   ├── composition/                     ← compose_blog_post, compose_linkedin, etc.
│   ├── engagement/                      ← draft_reply, etc.
│   ├── action/                          ← publish_blog_post, publish_linkedin, etc.
│   ├── escalation/                      ← rah_judgment, human_approval
│   └── reporting/                       ← daily_pulse, weekly_executive_summary
├── data/
│   ├── state.sqlite                     ← event store + audit log
│   ├── traces/YYYY-MM-DD/               ← JSONL per-session traces
│   ├── drafts/                          ← Composer outputs awaiting review
│   ├── pulse/                           ← daily summaries
│   └── plans/                           ← Strategist weekly plans
├── scripts/
│   ├── load_knowledge_base.py           ← ingests D:\DeFi assets
│   ├── provision_vps.sh                 ← Hetzner CX21 setup
│   ├── deploy.sh                        ← end-to-end deploy
│   ├── setup_telegram_bot.md            ← @BotFather walkthrough
│   ├── setup_openrouter.md              ← API key setup
│   └── setup_rentahuman_mcp.md          ← MCP config
├── tests/                               ← brand-safety + sandbox-isolation tests
├── docker-compose.yml                   ← sandbox stack
├── Dockerfile.agent                     ← Hermes + Browser-Use + Chromium
├── config.yaml                          ← Hermes config
├── .env.template                        ← secrets skeleton
└── README.md                            ← this file
```

## Tiered autonomy

| Tier | What | Examples | Gate |
|---|---|---|---|
| 1 | Full auto | Telegram personal channel, internal state, audit logs | none |
| 2 | Auto with Critic PASS | sergeisolovev.com blog posts, paper landing page edits | Critic adversarial review |
| 3 | Human approval | LinkedIn, X, outreach emails, grant applications | Sergei `/approve` via TG |
| 4 | RAH escalation | Captcha, phone verification, judgment edge cases | RentAHuman MCP |

## Quick start

### Prerequisites (manual setup)
1. Hetzner Cloud account + API token
2. OpenRouter account + API key (free models OK for MVP)
3. Anthropic API key (for Composer + Critic LLM calls; ~$30/mo projected)
4. Telegram bot token from @BotFather + your numeric user ID from @userinfobot
5. 1Password Connect token OR HashiCorp Vault dev mode

### Deployment
```bash
# Local clone (this directory)
git clone https://github.com/SergeySolovyev/sergei-brand-agent.git
cd sergei-brand-agent

# Populate secrets
cp .env.template .env
# Edit .env with your values

# Provision VPS
./scripts/provision_vps.sh hetzner-cx21

# Deploy
./scripts/deploy.sh

# Verify
docker logs sergei-brand-agent
```

### First-run actions

After deploy:
1. Open `SOUL.md` and replace the TODO section with your 5-10 line identity statement
2. Run `python scripts/load_knowledge_base.py` to ingest existing brand assets
3. Send `/start` to your Telegram bot — agent introduces itself
4. Send `/plan_week` to trigger Strategist
5. Review first Composer draft via `/drafts`
6. Approve or reject; iterate

## Brand-safety guardrails

The **Critic** is the heart of safety. Read `personas/critic.md` for the full
checklist (factual checks, tone checks, safety checks, channel-specific checks).

Key safeguards:
- Every public-facing draft passes Critic adversarial review
- Tier 3 actions (LinkedIn, X, outreach) require Sergei's `/approve` in Telegram
- All actions logged as JSONL to `data/traces/YYYY-MM-DD/`
- Daily cost budget cap with auto-throttle
- Sandbox isolation: outbound HTTPS only, restricted filesystem
- Credential boundary: secrets mounted on-demand from Vault

## Cost estimate

| Component | $/мес |
|---|---|
| VPS Hetzner CX21 (2vCPU, 4GB) | $5 |
| Anthropic Claude (Composer + Critic) | $15-25 |
| OpenRouter free models (Strategist) | $0-2 |
| Browser-Use Cloud (optional) | $0-10 |
| RentAHuman (Phase 2) | $20-50 |
| 1Password Connect | $5 |
| **Total** | **~$45-100/мес** |

## Roadmap

- **Phase 1 (now)**: Triad + Browser-Use + 5 priority skills + Telegram approval bot
- **Phase 2 (months 2-3)**: RAH integration, deeper discovery, outreach skills
- **Phase 3 (months 4-6)**: Optional Researcher agent for deep opportunity analysis

See `C:\Users\1\.claude\plans\glistening-singing-hearth.md` for full plan.

## License

MIT for code. Content (preprints, brand voice) © Sergei Solovev.
