#!/usr/bin/env bash
# install-pi.sh — bootstraps Shan Growth Agent on a Raspberry Pi (Debian/RPi OS).
#
# Idempotent. Safe to re-run. Designed for: ssh giuseppe@192.168.1.30
#
# Usage (on the Pi):
#   curl -fsSL <url>/install-pi.sh | sudo bash
# Or after `git pull` in the repo:
#   sudo ./deploy/install-pi.sh

set -euo pipefail

APP_USER="${APP_USER:-giuseppe}"
APP_DIR="${APP_DIR:-/opt/shan-growth-agent}"
REPO_URL="${REPO_URL:-}"  # optional: if set, performs a fresh clone

log()  { printf '\033[1;36m[shan]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[shan]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[shan]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Run as root (use sudo)."

log "Installing system dependencies"
apt-get update -y
apt-get install -y --no-install-recommends \
    ca-certificates curl git ufw

# --- Docker ---
if ! command -v docker >/dev/null 2>&1; then
    log "Installing Docker via official convenience script"
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker "$APP_USER" || warn "Could not add $APP_USER to docker group"
fi

if ! docker compose version >/dev/null 2>&1; then
    die "Docker Compose v2 plugin missing. Install docker-compose-plugin."
fi

systemctl enable --now docker

# --- App directory ---
if [[ -n "$REPO_URL" && ! -d "$APP_DIR/.git" ]]; then
    log "Cloning repo into $APP_DIR"
    mkdir -p "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
    chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
fi

[[ -d "$APP_DIR" ]] || die "App dir $APP_DIR missing. scp the project or set REPO_URL."

cd "$APP_DIR"

if [[ ! -f .env ]]; then
    log "Creating .env from .env.example (EDIT IT BEFORE STARTING)"
    cp .env.example .env
    chmod 600 .env
    chown "$APP_USER":"$APP_USER" .env
    warn "Edit $APP_DIR/.env with real secrets, then re-run this script (or run 'docker compose up -d')."
fi

mkdir -p data secrets
chown -R "$APP_USER":"$APP_USER" data secrets
chmod 700 secrets

# --- Firewall (UFW) — LAN-only access on port 8765 ---
if command -v ufw >/dev/null 2>&1; then
    log "Configuring UFW: allow SSH + dashboard from LAN 192.168.1.0/24"
    ufw allow OpenSSH || true
    ufw allow from 192.168.1.0/24 to any port 8765 proto tcp || true
    yes | ufw enable >/dev/null 2>&1 || true
fi

log "Building and starting Shan stack"
docker compose pull 2>/dev/null || true
docker compose build
docker compose up -d

log "Status:"
docker compose ps

log "Done. Dashboard: http://$(hostname -I | awk '{print $1}'):8765/"
log "Tail logs with: docker compose logs -f shan"
