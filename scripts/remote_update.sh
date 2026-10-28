#!/usr/bin/env bash
# ==============================================================================
# IoT Data Simulator - Remote SSH Hot-Reload Deployment Script
# ==============================================================================
# Synchronizes local project source code or releases to a target host over SSH,
# builds the container image remotely, and performs hot-reloading with zero MQTT
# broker downtime.
#
# If target host/user parameters are not provided as CLI arguments or environment
# variables, the script prompts the user interactively at runtime.
#
# Usage:
#   ./scripts/remote_update.sh [USER@HOST] [HTTP_PORT]
#
# Examples:
#   ./scripts/remote_update.sh
#   ./scripts/remote_update.sh user@192.168.1.100
#   ./scripts/remote_update.sh user@192.168.1.100 8032
# ==============================================================================

set -euo pipefail

# Terminal color tokens
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Resolve Target (CLI argument > Environment variable > Interactive prompt)
TARGET="${1:-${REMOTE_TARGET:-}}"
if [ -z "${TARGET}" ]; then
    echo -e "${YELLOW}Remote SSH target not specified.${NC}"
    read -rp "Enter remote SSH target (e.g. user@hostname_or_ip): " TARGET
    if [ -z "${TARGET}" ]; then
        echo -e "${RED}❌ Error: Remote target is required. Exiting.${NC}"
        exit 1
    fi
fi

# Extract host part (IP or hostname) and user part
if [[ "${TARGET}" == *"@"* ]]; then
    HOST_IP="${TARGET#*@}"
    REMOTE_USER="${TARGET%@*}"
else
    HOST_IP="${TARGET}"
    REMOTE_USER="$(whoami)"
fi

# 2. Resolve Remote Directory
DEFAULT_REMOTE_DIR="~/iot-data-simulator"
if [ -z "${REMOTE_DIR:-}" ]; then
    if [ -t 0 ] && [ $# -lt 1 ]; then
        read -rp "Enter remote directory [${DEFAULT_REMOTE_DIR}]: " USER_REMOTE_DIR
        REMOTE_DIR="${USER_REMOTE_DIR:-$DEFAULT_REMOTE_DIR}"
    else
        REMOTE_DIR="${DEFAULT_REMOTE_DIR}"
    fi
fi

# 3. Resolve HTTP Port
DEFAULT_APP_PORT="8032"
if [ -n "${2:-}" ]; then
    APP_PORT="${2}"
elif [ -n "${SIMULATOR_PORT:-}" ]; then
    APP_PORT="${SIMULATOR_PORT}"
else
    if [ -t 0 ] && [ $# -lt 2 ]; then
        read -rp "Enter remote HTTP port [${DEFAULT_APP_PORT}]: " USER_APP_PORT
        APP_PORT="${USER_APP_PORT:-$DEFAULT_APP_PORT}"
    else
        APP_PORT="${DEFAULT_APP_PORT}"
    fi
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  IoT Data Simulator - Remote SSH Hot-Reload Update   ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "Remote target       : ${YELLOW}${TARGET}${NC}"
echo -e "Remote directory    : ${YELLOW}${REMOTE_DIR}${NC}"
echo -e "Expected HTTP port  : ${YELLOW}${APP_PORT}${NC}"
echo ""

# 4. SSH Connectivity pre-flight check
echo -e "${BLUE}[1/4] Checking SSH connectivity...${NC}"
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${TARGET}" "echo 'SSH OK'" >/dev/null 2>&1; then
    echo -e "${RED}❌ Unable to establish SSH connection to ${TARGET}.${NC}"
    echo "Verify target machine is reachable and public key is authorized in ~/.ssh/authorized_keys."
    exit 1
fi
echo -e "${GREEN}✓ SSH connection established successfully.${NC}"

# 2. Source tree streaming synchronization
echo -e "${BLUE}[2/4] Streaming source archive to ${TARGET}:${REMOTE_DIR}...${NC}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

# Stream tar archive over SSH while strictly excluding runtime data, credentials, and venvs
tar --exclude="__pycache__" \
    --exclude=".pytest_cache" \
    --exclude="venv" \
    --exclude=".venv" \
    --exclude="mosquitto/data/*" \
    --exclude="mosquitto/log/*" \
    --exclude="data/simulator_state.json" \
    --exclude="data/users.json" \
    --exclude="data/*.bak" \
    --exclude=".env" \
    -czf - . | ssh "${TARGET}" "mkdir -p ${REMOTE_DIR} && tar -xzf - -C ${REMOTE_DIR}"

echo -e "${GREEN}✓ Source tree synchronized live.${NC}"

# 3. Remote build and zero-downtime hot-reload
echo -e "${BLUE}[3/4] Rebuilding Docker image and hot-reloading simulator service...${NC}"
ssh "${TARGET}" "cd ${REMOTE_DIR} && \
    docker compose -f docker-compose.portainer.yml build simulator && \
    docker compose -f docker-compose.portainer.yml up -d --no-deps simulator"

echo -e "${GREEN}✓ Simulator service container recreated.${NC}"

# 4. HTTP readiness probe verification (healthcheck)
echo -e "${BLUE}[4/4] Polling healthcheck endpoint /healthz...${NC}"
HEALTH_URL="http://${HOST_IP}:${APP_PORT}/healthz"
echo "Querying ${HEALTH_URL}..."

ATTEMPTS=0
MAX_ATTEMPTS=15
HEALTH_OK=false

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    HTTP_STATUS=$(curl -s -o /tmp/health_res.json -w "%{http_code}" "${HEALTH_URL}" || true)
    if [ "$HTTP_STATUS" = "200" ]; then
        HEALTH_OK=true
        break
    fi
    ATTEMPTS=$((ATTEMPTS+1))
    echo "Waiting for service availability (attempt ${ATTEMPTS}/${MAX_ATTEMPTS})..."
    sleep 2
done

if [ "$HEALTH_OK" = true ]; then
    VERSION=$(grep -o '"version":"[^"]*"' /tmp/health_res.json | cut -d'"' -f4 || echo "unknown")
    echo ""
    echo -e "${GREEN}======================================================${NC}"
    echo -e "${GREEN}✅ Remote update succeeded on ${HOST_IP}!${NC}"
    echo -e "   Active version : ${YELLOW}v${VERSION}${NC}"
    echo -e "   Web GUI access : ${BLUE}http://${HOST_IP}:${APP_PORT}${NC}"
    echo -e "${GREEN}======================================================${NC}"
    rm -f /tmp/health_res.json
    exit 0
else
    echo -e "${RED}⚠️ Simulator failed readiness probe after $((MAX_ATTEMPTS*2)) seconds.${NC}"
    echo "Inspect remote container logs using:"
    echo "  ssh ${TARGET} 'docker logs --tail 50 iot-sim-app'"
    exit 1
fi
