#!/usr/bin/env bash
# ==============================================================================
# IoT Data Simulator - Script de Déploiement & Mise à Jour à Distance
# ==============================================================================
# Met à jour l'instance distante en synchronisant le code local ou les releases
# et en redémarrant à chaud les conteneurs Docker sans interruption du broker.
#
# Usage :
#   ./scripts/remote_update.sh [UTILISATEUR@HOTE] [PORT_HTTP]
#
# Exemples :
#   ./scripts/remote_update.sh
#   ./scripts/remote_update.sh proth@192.168.10.114
#   ./scripts/remote_update.sh proth@192.168.10.114 8032
# ==============================================================================

set -euo pipefail

# Paramètres par défaut
TARGET="${1:-${REMOTE_TARGET:-proth@192.168.10.114}}"
REMOTE_DIR="${REMOTE_DIR:-/home/proth/iot-data-simulator}"
HOST_IP="${TARGET#*@}"
APP_PORT="${2:-${SIMULATOR_PORT:-8032}}"

# Couleurs pour le terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  IoT Data Simulator - Mise à Jour à Distance SSH     ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "Cible distante       : ${YELLOW}${TARGET}${NC}"
echo -e "Répertoire distant   : ${YELLOW}${REMOTE_DIR}${NC}"
echo -e "Port HTTP attendu    : ${YELLOW}${APP_PORT}${NC}"
echo ""

# 1. Vérification de la connectivité SSH
echo -e "${BLUE}[1/4] Vérification de la connexion SSH...${NC}"
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${TARGET}" "echo 'SSH OK'" >/dev/null 2>&1; then
    echo -e "${RED}❌ Impossible de se connecter en SSH à ${TARGET}.${NC}"
    echo "Vérifiez que la machine est allumée et que votre clé SSH est autorisée."
    exit 1
fi
echo -e "${GREEN}✓ Connexion SSH établie avec succès.${NC}"

# 2. Synchronisation du code source
echo -e "${BLUE}[2/4] Synchronisation des fichiers sources vers ${TARGET}:${REMOTE_DIR}...${NC}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

# Transfert rapide par flux d'archive tar chiffré en préservant les données de prod distantes
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

echo -e "${GREEN}✓ Code source synchronisé en direct.${NC}"

# 3. Compilation et relance du conteneur applicatif
echo -e "${BLUE}[3/4] Compilation de l'image et redémarrage à chaud de la stack...${NC}"
ssh "${TARGET}" "cd ${REMOTE_DIR} && \
    docker compose -f docker-compose.portainer.yml build simulator && \
    docker compose -f docker-compose.portainer.yml up -d --no-deps simulator"

echo -e "${GREEN}✓ Conteneur simulator mis à jour et relancé.${NC}"

# 4. Vérification de l'état de santé HTTP
echo -e "${BLUE}[4/4] Vérification de la sonde de disponibilité (healthcheck)...${NC}"
HEALTH_URL="http://${HOST_IP}:${APP_PORT}/healthz"
echo "Interrogation de ${HEALTH_URL}..."

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
    echo "En attente du démarrage complet (tentative ${ATTEMPTS}/${MAX_ATTEMPTS})..."
    sleep 2
done

if [ "$HEALTH_OK" = true ]; then
    VERSION=$(grep -o '"version":"[^"]*"' /tmp/health_res.json | cut -d'"' -f4 || echo "inconnue")
    echo ""
    echo -e "${GREEN}======================================================${NC}"
    echo -e "${GREEN}✅ Mise à jour terminée avec succès sur ${HOST_IP} !${NC}"
    echo -e "   Version active : ${YELLOW}v${VERSION}${NC}"
    echo -e "   Accès Web GUI  : ${BLUE}http://${HOST_IP}:${APP_PORT}${NC}"
    echo -e "${GREEN}======================================================${NC}"
    rm -f /tmp/health_res.json
    exit 0
else
    echo -e "${RED}⚠️ Le simulateur n'a pas répondu au healthcheck après $((MAX_ATTEMPTS*2)) secondes.${NC}"
    echo "Consultez les logs distants avec :"
    echo "  ssh ${TARGET} 'docker logs --tail 50 iot-sim-app'"
    exit 1
fi
