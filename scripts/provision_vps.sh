#!/usr/bin/env bash
# =============================================================================
# provision_vps.sh — Hetzner Cloud CX21 setup for sergei-brand-agent
#
# Usage on a fresh Ubuntu 24.04 VPS:
#   curl -fsSL https://raw.githubusercontent.com/SergeySolovyev/sergei-brand-agent/main/scripts/provision_vps.sh \
#        | sudo bash -s -- --user agent --hostname brand-agent
#
# OR locally:
#   scp provision_vps.sh root@<vps-ip>:/tmp/
#   ssh root@<vps-ip> 'bash /tmp/provision_vps.sh --user agent --hostname brand-agent'
# =============================================================================
set -euo pipefail

USER_NAME="agent"
HOSTNAME_NEW="brand-agent"
SSH_PORT="22"
ALLOW_SSH_FROM=""   # e.g. "1.2.3.4/32"; empty = anywhere

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user) USER_NAME="$2"; shift 2 ;;
    --hostname) HOSTNAME_NEW="$2"; shift 2 ;;
    --ssh-port) SSH_PORT="$2"; shift 2 ;;
    --allow-ssh-from) ALLOW_SSH_FROM="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

log() { echo -e "\033[36m[$(date +%H:%M:%S)] $*\033[0m"; }
fail() { echo -e "\033[31m[ERROR] $*\033[0m" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || fail "Must run as root"
[[ -f /etc/os-release ]] || fail "Not a Linux system"
. /etc/os-release
[[ "$ID" == "ubuntu" ]] || log "WARN: tested on Ubuntu only; you have $ID"

# -----------------------------------------------------------------------------
# 1. Set hostname
# -----------------------------------------------------------------------------
log "Setting hostname to $HOSTNAME_NEW"
hostnamectl set-hostname "$HOSTNAME_NEW"
sed -i "/127.0.1.1/d" /etc/hosts
echo "127.0.1.1  $HOSTNAME_NEW" >> /etc/hosts

# -----------------------------------------------------------------------------
# 2. Update + base packages
# -----------------------------------------------------------------------------
log "Updating packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    curl ca-certificates gnupg lsb-release \
    ufw fail2ban unattended-upgrades \
    htop tmux vim git jq \
    sqlite3

# -----------------------------------------------------------------------------
# 3. Create non-root user with sudo
# -----------------------------------------------------------------------------
if ! id "$USER_NAME" >/dev/null 2>&1; then
    log "Creating user: $USER_NAME"
    useradd -m -s /bin/bash -G sudo,docker "$USER_NAME" || useradd -m -s /bin/bash -G sudo "$USER_NAME"
    passwd -d "$USER_NAME"   # no password — SSH key only
    log "  -> add your SSH public key to /home/$USER_NAME/.ssh/authorized_keys"
else
    log "User $USER_NAME already exists"
fi

# Copy root authorized_keys to new user
if [[ -f /root/.ssh/authorized_keys ]] && [[ ! -f "/home/$USER_NAME/.ssh/authorized_keys" ]]; then
    mkdir -p "/home/$USER_NAME/.ssh"
    cp /root/.ssh/authorized_keys "/home/$USER_NAME/.ssh/"
    chown -R "$USER_NAME:$USER_NAME" "/home/$USER_NAME/.ssh"
    chmod 700 "/home/$USER_NAME/.ssh"
    chmod 600 "/home/$USER_NAME/.ssh/authorized_keys"
fi

# Passwordless sudo for agent user
echo "$USER_NAME ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/$USER_NAME
chmod 0440 /etc/sudoers.d/$USER_NAME

# -----------------------------------------------------------------------------
# 4. Harden SSH
# -----------------------------------------------------------------------------
log "Hardening SSH"
SSHD=/etc/ssh/sshd_config
sed -i -E "s/^#?PermitRootLogin.*/PermitRootLogin no/" "$SSHD"
sed -i -E "s/^#?PasswordAuthentication.*/PasswordAuthentication no/" "$SSHD"
sed -i -E "s/^#?ChallengeResponseAuthentication.*/ChallengeResponseAuthentication no/" "$SSHD"
sed -i -E "s/^#?Port.*/Port $SSH_PORT/" "$SSHD"
grep -q "^MaxAuthTries" "$SSHD" || echo "MaxAuthTries 3" >> "$SSHD"
grep -q "^ClientAliveInterval" "$SSHD" || echo "ClientAliveInterval 300" >> "$SSHD"
systemctl reload sshd || systemctl reload ssh

# -----------------------------------------------------------------------------
# 5. Firewall (ufw)
# -----------------------------------------------------------------------------
log "Configuring firewall"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

if [[ -n "$ALLOW_SSH_FROM" ]]; then
    ufw allow from "$ALLOW_SSH_FROM" to any port "$SSH_PORT" proto tcp
    log "  SSH restricted to $ALLOW_SSH_FROM"
else
    ufw allow "$SSH_PORT/tcp"
    log "  SSH open from anywhere (port $SSH_PORT)"
fi

# Telegram webhook (Phase 2)
# ufw allow 8443/tcp

ufw --force enable

# -----------------------------------------------------------------------------
# 6. fail2ban (anti-bruteforce)
# -----------------------------------------------------------------------------
log "Enabling fail2ban"
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = $SSH_PORT
EOF
systemctl restart fail2ban
systemctl enable fail2ban

# -----------------------------------------------------------------------------
# 7. Unattended-upgrades (automatic security patches)
# -----------------------------------------------------------------------------
log "Enabling unattended-upgrades for security patches"
dpkg-reconfigure -plow unattended-upgrades < /dev/null || true
cat > /etc/apt/apt.conf.d/20auto-upgrades <<EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF

# -----------------------------------------------------------------------------
# 8. Docker + Docker Compose
# -----------------------------------------------------------------------------
log "Installing Docker"
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi
usermod -aG docker "$USER_NAME" || true

# Docker Compose plugin
apt-get install -y -qq docker-compose-plugin

# -----------------------------------------------------------------------------
# 9. Create agent working directory
# -----------------------------------------------------------------------------
log "Creating /opt/sergei-brand-agent"
mkdir -p /opt/sergei-brand-agent/data/{traces,drafts,pulse,plans,repos}
chown -R "$USER_NAME:$USER_NAME" /opt/sergei-brand-agent

# -----------------------------------------------------------------------------
# 10. Set up systemd service for the agent (auto-start on boot)
# -----------------------------------------------------------------------------
cat > /etc/systemd/system/sergei-brand-agent.service <<EOF
[Unit]
Description=Sergei Brand Agent (Hermes + Browser-Use + Triad)
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/opt/sergei-brand-agent
User=$USER_NAME
Group=$USER_NAME
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=5min

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
# Don't enable yet — let user verify deploy first
# systemctl enable sergei-brand-agent

# -----------------------------------------------------------------------------
# 11. Tinyproxy config (egress whitelist)
# -----------------------------------------------------------------------------
log "Writing tinyproxy egress config"
mkdir -p /opt/sergei-brand-agent/scripts
cat > /opt/sergei-brand-agent/scripts/tinyproxy.conf <<'EOF'
# Tinyproxy egress whitelist for sergei-brand-agent
User nobody
Group nobody
Port 8888
Listen 0.0.0.0
Timeout 600
DefaultErrorFile "/usr/share/tinyproxy/default.html"
StatHost "localhost"
StatFile "/usr/share/tinyproxy/stats.html"
LogFile "/var/log/tinyproxy/tinyproxy.log"
LogLevel Connect
PidFile "/run/tinyproxy/tinyproxy.pid"
MaxClients 50
StartServers 5
MinSpareServers 2
MaxSpareServers 10

# WHITELIST — only these destinations allowed outbound
Allow sergeisolovev.com
Allow github.com
Allow api.github.com
Allow raw.githubusercontent.com
Allow linkedin.com
Allow www.linkedin.com
Allow twitter.com
Allow x.com
Allow openalex.org
Allow api.openalex.org
Allow scholar.google.com
Allow figshare.com
Allow api.figshare.com
Allow rentahuman.ai
Allow api.indexnow.org
Allow openrouter.ai
Allow api.anthropic.com
Allow telegram.org
Allow api.telegram.org
Allow web.archive.org

# CONNECT only on HTTPS
ConnectPort 443
ConnectPort 563
EOF
chown -R "$USER_NAME:$USER_NAME" /opt/sergei-brand-agent

# -----------------------------------------------------------------------------
# 12. Summary
# -----------------------------------------------------------------------------
log "VPS provisioning complete"
cat <<EOF

╔══════════════════════════════════════════════════════════════════════╗
║  sergei-brand-agent VPS provisioned                                  ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Hostname:  $HOSTNAME_NEW                                            ║
║  User:      $USER_NAME (passwordless sudo, SSH key only)             ║
║  SSH port:  $SSH_PORT                                                ║
║  Firewall:  active (only SSH open)                                   ║
║  Docker:    installed                                                ║
║  Agent dir: /opt/sergei-brand-agent                                  ║
║                                                                       ║
║  Next steps:                                                         ║
║  1. SSH as $USER_NAME (not root)                                     ║
║  2. cd /opt/sergei-brand-agent                                       ║
║  3. git clone https://github.com/SergeySolovyev/sergei-brand-agent . ║
║  4. cp .env.template .env && nano .env  # fill secrets               ║
║  5. ./scripts/deploy.sh                                              ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝

EOF
