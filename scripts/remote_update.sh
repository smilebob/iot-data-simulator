#!/usr/bin/env bash
# ==============================================================================
# IoT Data Simulator - Remote SSH Hot-Reload Deployment Script
# ==============================================================================
# Synchronizes local project source code or releases to a target host over SSH,
# builds the container image remotely, and performs hot-reloading with zero MQTT
# broker downtime.
#
# Usage:
#   ./scripts/remote_update.sh [USER@HOST] [HTTP_PORT]
#
# Examples:
#   ./scripts/remote_update.sh
#   ./scripts/remote_update.sh proth@192.168.10.114
#   ./scripts/remote_update.sh proth@192.168.10.114 8032
# ==============================================================================

set -euo pipefail

# Default deployment target parameters
TARGET="${1:-${REMOTE_TARGET:-proth@192.168.10.114}}"
REMOTE_DIR="${REMOTE_DIR:-/home/proth/iot-data-simulator}"
HOST_IP="${TARGET#*@}"
APP_PORT="${2:-${SIMULATOR_PORT:-8032}}"

# Terminal color tokens
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  IoT Data Simulator - Remote SSH Hot-Reload Update   ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "Remote target       : ${YELLOW}${TARGET}${NC}"
echo -e "Remote directory    : ${YELLOW}${REMOTE_DIR}${NC}"
echo -e "Expected HTTP port  : ${YELLOW}${APP_PORT}${NC}"
echo ""

# 1. SSH Connectivity pre-flight check
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
