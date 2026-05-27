#!/bin/bash
# =============================================================================
# sergei-brand-agent — DigitalOcean cloud-init / startup script
# =============================================================================
# Drop this entire file into:
#   DO Create Droplet → Additional Options → Startup scripts → paste below
#
# What this does on first boot (≈5-7 min, fully automatic):
#   1. Update apt + install base tooling
#   2. Install Docker + Compose plugin
#   3. Configure UFW firewall (22, 80, 443, 8443 for caddy webhooks)
#   4. Create non-root user `agent` (Docker socket access)
#   5. Clone sergei-brand-agent repo
#   6. Create .env template with placeholders
#   7. Start docker compose in idle mode (waiting for credentials)
#   8. Write status file: /var/lib/brand-agent/STATUS
#
# After this runs:
#   - SSH in as root, `cd /opt/sergei-brand-agent`
#   - Edit `.env` to fill credentials (TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY, ...)
#   - `docker compose up -d` (it'll pick up real .env)
#   - Watch logs: `docker compose logs -f orchestrator`
#
# Every step logged to /var/log/cloud-init-output.log
# Visible in DO UI → droplet → Activity tab
# =============================================================================

set -euo pipefail

LOG=/var/log/brand-agent-bootstrap.log
exec > >(tee -a "$LOG") 2>&1

echo "===== $(date -u) ====="
echo "[bootstrap] sergei-brand-agent provisioning starting"

# -----------------------------------------------------------------------------
# 1. Base system update + tools
# -----------------------------------------------------------------------------
echo "[1/8] System update + base tools..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    ca-certificates curl gnupg lsb-release \
    git jq ufw fail2ban htop tmux vim less unzip \
    python3 python3-pip python3-venv \
    sqlite3 \
    rsync

# -----------------------------------------------------------------------------
# 2. Install Docker Engine + Compose v2
# -----------------------------------------------------------------------------
echo "[2/8] Installing Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list >/dev/null
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

# -----------------------------------------------------------------------------
# 3. UFW firewall — allow only what's needed
# -----------------------------------------------------------------------------
echo "[3/8] Firewall (UFW)..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP (Caddy for Lets Encrypt)'
ufw allow 443/tcp comment 'HTTPS (Caddy reverse proxy)'
ufw allow 8443/tcp comment 'Optional webhook ingress'
ufw --force enable

# -----------------------------------------------------------------------------
# 4. fail2ban — basic SSH hardening
# -----------------------------------------------------------------------------
echo "[4/8] fail2ban..."
cat > /etc/fail2ban/jail.local <<'JAIL'
[sshd]
enabled = true
port    = ssh
filter  = sshd
backend = systemd
maxretry = 5
bantime  = 1h
findtime = 10m
JAIL
systemctl enable --now fail2ban

# -----------------------------------------------------------------------------
# 5. Non-root `agent` user
# -----------------------------------------------------------------------------
echo "[5/8] Creating agent user..."
if ! id -u agent &>/dev/null; then
    useradd -m -s /bin/bash -G docker agent
    # Copy root's authorized_keys so agent gets same SSH access
    mkdir -p /home/agent/.ssh
    cp /root/.ssh/authorized_keys /home/agent/.ssh/ 2>/dev/null || true
    chown -R agent:agent /home/agent/.ssh
    chmod 700 /home/agent/.ssh
    chmod 600 /home/agent/.ssh/authorized_keys 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# 6. Clone repo + .env template
# -----------------------------------------------------------------------------
echo "[6/8] Cloning sergei-brand-agent..."
REPO_DIR=/opt/sergei-brand-agent
if [ ! -d "$REPO_DIR/.git" ]; then
    git clone https://github.com/SergeySolovyev/sergei-brand-agent.git "$REPO_DIR"
fi
chown -R agent:agent "$REPO_DIR"

# Build .env template (DO NOT overwrite if user has already edited it)
ENV_FILE="$REPO_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<'ENVTPL'
# =============================================================================
# sergei-brand-agent runtime credentials
# Fill these in, then: docker compose up -d
# =============================================================================

# ── LLM ─────────────────────────────────────────────────────────────────────
# OpenRouter for cheap inference (free models for monitoring/composition)
OPENROUTER_API_KEY=

# Anthropic Claude for Critic + Strategist (quality > cost on the Critic loop)
ANTHROPIC_API_KEY=

# Default models — can override per-skill in YAML
COMPOSER_MODEL=claude-sonnet-4-5
CRITIC_MODEL=claude-sonnet-4-5
STRATEGIST_MODEL=claude-sonnet-4-5
HAIKU_MODEL=claude-haiku-4-5

# ── Telegram ────────────────────────────────────────────────────────────────
# Bot token from @BotFather
TELEGRAM_BOT_TOKEN=

# Comma-separated user IDs allowed to use the bot (your @userinfobot ID)
TELEGRAM_ALLOWED_USERS=

# Where weekly digests + escalations go (numeric chat id of your private chat)
TELEGRAM_HOME_CHANNEL=

# Your public broadcast channel (optional, for Tier-1 auto-publishes)
TELEGRAM_PUBLIC_CHANNEL=@sergeisolovev

# ── GitHub ──────────────────────────────────────────────────────────────────
# Fine-grained PAT scoped to public repos
GITHUB_TOKEN=

# ── figshare (optional, for view/download stats; revoke after each use) ─────
FIGSHARE_TOKEN=

# ── Search Console (Phase 2) ────────────────────────────────────────────────
# Service account JSON path inside the container
GOOGLE_APPLICATION_CREDENTIALS=

# ── Browser-Use cookies (LinkedIn / X) — see docs/browser_cookies.md ────────
LINKEDIN_COOKIES_PATH=/workspace/secrets/linkedin_cookies.json
X_COOKIES_PATH=/workspace/secrets/x_cookies.json

# ── Polite User-Agent for academic crawlers ─────────────────────────────────
OPENALEX_POLITE_EMAIL=sesesolovev@edu.hse.ru

# ── Cost & safety caps ──────────────────────────────────────────────────────
DAILY_COST_CAP_USD=8
MAX_PUBLISHES_PER_DAY=5
EMERGENCY_PAUSE=false
ENVTPL
    chmod 600 "$ENV_FILE"
    chown agent:agent "$ENV_FILE"
fi

# -----------------------------------------------------------------------------
# 7. Pre-pull base images so first `docker compose up` is fast
# -----------------------------------------------------------------------------
echo "[7/8] Pre-pulling Docker base images..."
docker pull python:3.12-slim || true
docker pull caddy:2-alpine || true

# -----------------------------------------------------------------------------
# 8. Status marker — agent NOT YET started (waits for .env to be filled)
# -----------------------------------------------------------------------------
echo "[8/8] Writing status..."
mkdir -p /var/lib/brand-agent
cat > /var/lib/brand-agent/STATUS <<EOF
status=PROVISIONED_AWAITING_CREDENTIALS
hostname=$(hostname)
ipv4_public=$(curl -s ifconfig.me || echo unknown)
provisioned_at=$(date -u +%FT%TZ)
next_steps:
  1. SSH in: ssh root@<this-ip>
  2. Edit: nano /opt/sergei-brand-agent/.env
  3. Required: OPENROUTER_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USERS, GITHUB_TOKEN
  4. Start: cd /opt/sergei-brand-agent && docker compose up -d
  5. Watch: docker compose logs -f
EOF
chmod 644 /var/lib/brand-agent/STATUS

echo
echo "============================================================"
echo "  sergei-brand-agent bootstrap COMPLETE"
echo "  $(date -u)"
echo "============================================================"
echo "  ✓ Docker + Compose installed"
echo "  ✓ UFW firewall enabled (22, 80, 443, 8443)"
echo "  ✓ fail2ban guarding SSH"
echo "  ✓ Repo cloned at /opt/sergei-brand-agent"
echo "  ✓ .env template created (chmod 600)"
echo "  ✓ Base images pre-pulled"
echo
echo "  Status file: /var/lib/brand-agent/STATUS"
echo "  Bootstrap log: $LOG"
echo
echo "  Next step (you, after SSH-ing in):"
echo "    1. nano /opt/sergei-brand-agent/.env  # fill credentials"
echo "    2. cd /opt/sergei-brand-agent && docker compose up -d"
echo "============================================================"
