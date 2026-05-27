#!/usr/bin/env bash
# =============================================================================
# deploy.sh — end-to-end deploy of sergei-brand-agent
#
# Run on the VPS, in /opt/sergei-brand-agent/ after git clone.
# =============================================================================
set -euo pipefail

log() { echo -e "\033[36m[$(date +%H:%M:%S)] $*\033[0m"; }
fail() { echo -e "\033[31m[ERROR] $*\033[0m" >&2; exit 1; }

cd "$(dirname "$0")/.."

# -----------------------------------------------------------------------------
# 1. Sanity checks
# -----------------------------------------------------------------------------
[[ -f .env ]] || fail ".env not found. Copy from .env.template and fill secrets first."
[[ -f docker-compose.yml ]] || fail "docker-compose.yml not found (wrong directory?)"
[[ -f Dockerfile.agent ]] || fail "Dockerfile.agent not found"

# Verify required secrets are set in .env (not the template placeholders)
log "Validating .env"
for var in ANTHROPIC_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_ALLOWED_USERS GITHUB_TOKEN; do
    val=$(grep -E "^${var}=" .env | head -1 | cut -d= -f2-)
    if [[ -z "$val" ]] || [[ "$val" == *"XXXXXXXXXXX"* ]] || [[ "$val" == "sk-ant-api03-XXXXXXXXXXXXXXXXXXXXX" ]]; then
        fail "$var not set in .env (still template placeholder)"
    fi
done
log "  ✓ required secrets present"

# -----------------------------------------------------------------------------
# 2. Ingest knowledge base (if D:/DeFi assets are available)
# -----------------------------------------------------------------------------
if [[ -d /workspace/defi-assets ]] || [[ -d ../defi-assets ]]; then
    log "Loading knowledge base from D:/DeFi assets"
    python3 scripts/load_knowledge_base.py --defi-root ../defi-assets
else
    log "WARN: no D:/DeFi assets found locally; using pre-committed knowledge_base/"
fi

# -----------------------------------------------------------------------------
# 3. Build the agent image
# -----------------------------------------------------------------------------
log "Building Docker image (sergei-brand-agent:latest)"
docker compose build agent

# -----------------------------------------------------------------------------
# 4. Initialize state.sqlite with required schema
# -----------------------------------------------------------------------------
log "Initializing state.sqlite schema"
mkdir -p data
sqlite3 data/state.sqlite <<'EOF'
-- Events table (monitor + composer + critic + publisher all write here)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    kind TEXT NOT NULL,
    subject TEXT,
    delta INTEGER DEFAULT 0,
    severity TEXT CHECK(severity IN ('low','medium','high')),
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    raw TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);

-- Approval queue (Tier 3 gates)
CREATE TABLE IF NOT EXISTS approval_queue (
    queue_id TEXT PRIMARY KEY,
    draft_path TEXT NOT NULL,
    channel TEXT NOT NULL,
    critic_verdict_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected','revise','expired')),
    feedback TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_aq_status ON approval_queue(status);

-- Snapshots (for diff-based monitoring)
CREATE TABLE IF NOT EXISTS snapshots (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cost tracking
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    persona TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_llm_ts ON llm_calls(ts);

-- Drafts catalog (mirror of data/drafts/ filesystem)
CREATE TABLE IF NOT EXISTS drafts (
    draft_path TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    topic TEXT,
    status TEXT NOT NULL CHECK(status IN ('composing','critic_review','approved','published','rejected','expired')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    critic_rounds INTEGER DEFAULT 0
);
EOF
log "  ✓ state.sqlite initialized"

# -----------------------------------------------------------------------------
# 5. Start the stack
# -----------------------------------------------------------------------------
log "Starting docker compose stack"
docker compose up -d agent egress-proxy
sleep 5

# -----------------------------------------------------------------------------
# 6. Verify healthy
# -----------------------------------------------------------------------------
log "Waiting for agent healthcheck"
for i in {1..30}; do
    status=$(docker inspect --format='{{.State.Health.Status}}' sergei-brand-agent 2>/dev/null || echo "starting")
    if [[ "$status" == "healthy" ]]; then
        log "  ✓ agent healthy"
        break
    fi
    sleep 3
    if [[ $i -eq 30 ]]; then
        log "WARN: agent not healthy after 90s; check 'docker logs sergei-brand-agent'"
    fi
done

# -----------------------------------------------------------------------------
# 7. Quick smoke tests
# -----------------------------------------------------------------------------
log "Running smoke tests"

# Test 1: Sandbox isolation (cannot reach private IPs)
log "  test 1: sandbox isolation"
if docker exec sergei-brand-agent curl -s --max-time 5 http://10.0.0.1 2>/dev/null; then
    log "    FAIL: agent reached 10.0.0.1 (should be blocked)"
else
    log "    ✓ private IP blocked"
fi

# Test 2: Can reach sergeisolovev.com (whitelisted)
log "  test 2: whitelisted domain reachable"
if docker exec sergei-brand-agent curl -sI --max-time 10 https://sergeisolovev.com | grep -q "200"; then
    log "    ✓ sergeisolovev.com reachable"
else
    log "    FAIL: sergeisolovev.com not reachable from sandbox"
fi

# Test 3: Telegram bot can /getMe
log "  test 3: telegram bot auth"
TG_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env | cut -d= -f2-)
if docker exec sergei-brand-agent curl -sI --max-time 10 "https://api.telegram.org/bot${TG_TOKEN}/getMe" | grep -q "200"; then
    log "    ✓ Telegram bot authenticated"
else
    log "    WARN: Telegram getMe failed"
fi

# Test 4: Knowledge base loaded
log "  test 4: knowledge base"
PREPRINTS_COUNT=$(docker exec sergei-brand-agent jq '.preprints | length' /workspace/knowledge_base/preprints.json 2>/dev/null || echo "0")
if [[ "$PREPRINTS_COUNT" == "5" ]]; then
    log "    ✓ 5 preprints loaded"
else
    log "    WARN: expected 5 preprints, found $PREPRINTS_COUNT"
fi

# -----------------------------------------------------------------------------
# 8. Enable autostart
# -----------------------------------------------------------------------------
log "Enabling systemd autostart"
sudo systemctl enable sergei-brand-agent || log "  WARN: systemd unit not found; skipping"

# -----------------------------------------------------------------------------
# 9. First-run instructions
# -----------------------------------------------------------------------------
log "Deploy complete"
cat <<EOF

╔══════════════════════════════════════════════════════════════════════╗
║  sergei-brand-agent is running                                       ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Status:   docker compose ps                                         ║
║  Logs:     docker compose logs -f agent                              ║
║  Stop:     docker compose down                                       ║
║  Restart:  docker compose restart agent                              ║
║                                                                       ║
║  First-run actions:                                                  ║
║  1. Send /start to your Telegram bot — agent introduces itself       ║
║  2. Edit SOUL.md and replace the TODO with your identity statement   ║
║  3. One-time browser login: docker exec -it sergei-brand-agent \\    ║
║       browser-use auth-init linkedin                                 ║
║     (then login manually in the headed browser; cookies persist)     ║
║  4. Trigger first weekly plan: /plan_week in Telegram bot            ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝

EOF
