# Agent Role Architecture

Based on Anthropic "Building Effective Agents" + 2025-2026 multi-agent research.
Core principle: **one orchestrator with single decision authority, narrow-boundary
specialists invoked on triggers, closed verification loop.** A flat "bag of agents"
amplifies errors ~17x; a centralized+verified topology constrains it to ~4.4x.

## Roster

| Role | File | Model | Fires when | Pattern |
|---|---|---|---|---|
| **Strategist / Orchestrator** | (Claude session) | Opus | Weekly plan; big tasks | Orchestrator-Workers |
| **Router / Triager** | triage.py | Haiku | Every inbound email/TG | Routing |
| **Researcher** | agent_discover, cfp_scanner, ru_grants_scanner | Sonnet | Daily/weekly sweeps | Orchestrator-Workers + Parallelization |
| **Composer** | *_drafter.py, daily_commentary, article_drafter | Sonnet (Opus for grants) | Strategist queues a draft | Prompt Chaining |
| **Critic** | _critique() in drafters | Sonnet | After every draft | Evaluator-Optimizer |
| **Verifier + Citation** | verifier.py | Sonnet (3-vote for high-stakes) | Before external ship | Evaluator-Optimizer + Voting |
| **Memory-Keeper** | memory_keeper.py | Haiku | Nightly 03:00 UTC | Sleep-time consolidation |
| **Monitor** | monitor_health.py | Haiku/code | Every 30 min | Assurance plane |
| **Scheduler** | cron | code | Time triggers | Routing-by-effort |
| **Mediator** | telegram_bot.py buttons | — | Before irreversible action | Human-in-the-loop gate |

## Model economy (the "100% efficiency" policy)

`model_router.py` is the single source of truth. Tiers:

- **Haiku** ($1/$5): triage, classify, route, memory writes, scheduling, monitoring,
  week-ahead bullets, topic-fit checks. Pattern-matching, not reasoning.
- **Sonnet** ($3/$15): all drafting, critique, verification, research, articles,
  summaries. The workhorse for anything that ships to a human.
- **Opus** ($5/$25): weekly strategy, grant applications (high-stakes + irreversible),
  flagship content. Only where a bad decision cascades downstream.

Measured impact: 3-tier routing ≈ 51% cheaper than uniform-Opus; routing broadly
saves 40-70%. Before this, everything was Sonnet — now triage/memory/monitoring run
at 1/3 the cost, and grant applications get Opus quality where it matters.

**20% break-even rule**: `model_router.py report` shows per-task correction rates.
If a Haiku task needs Sonnet-level correction >20% of the time, promote it (the
re-prompt cost eats the 3x advantage).

## Verification discipline (preventing reputational damage)

For an academic brand, a hallucinated stat or fake DOI is reputational damage.
Two-tier gate:

- **Tier 1** (every external output): Critic (quality) + single Sonnet Verifier
  (correctness + citation check against GROUND_TRUTH allowlist).
- **Tier 2** (grants, public research claims): 3-vote Verifier ensemble, Opus
  tiebreaker on split. Then human approval via Telegram buttons.

The Verifier treats the draft as DATA, never instructions — defends against
prompt injection from untrusted inbound content baked into drafts.

## Memory (file-of-record, not vector DB)

Letta benchmark: plain filesystem 74.0% > graph memory 68.5% on LoCoMo. Files win:
auditable, version-controlled, cheap, and the agent is excellent at filesystem tools.

`/opt/reports/memory/`:
- `memory.md` — pointer/index (only relevant files load)
- `daily-log.md` — nightly consolidation (newest first)
- `opportunities.md` / `contacts.md` / `decisions.md` / `deadlines.md` — domain files

Vector DB reserved for the RAG corpus only (papers, prior posts) — semantic recall
across hundreds of docs where structure-based lookup breaks down.

## Installed skills (~/.claude/skills/, 23 total)

- **Content/grant**: doc-coauthoring, internal-comms, skill-creator, pdf, docx, pptx
- **Academic**: deep-research, academic-paper, academic-paper-reviewer, academic-pipeline
- **Security (Sergei's domain)**: solana/ton/cairo/algorand/substrate/cosmos
  -vulnerability-scanner, token-integration-analyzer, guidelines-advisor,
  audit-prep-assistant, code-maturity-assessor, secure-workflow-guide,
  semgrep-rule-creator, differential-review

Sources: anthropics/skills, Imbad0202/academic-research-skills, trailofbits/skills.
