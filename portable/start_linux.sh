#!/usr/bin/env bash
# ==============================================================================
# IoT Data Simulator — Lanceur Portable Linux / macOS (0 droit administrateur)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

export IOT_SIM_PORTABLE=1
USER_ENV_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/iot-data-simulator"
VENV_DIR="${USER_ENV_DIR}/venv"

echo "================================================================"
echo "  IoT Data Simulator — Mode Portable Linux (Sans Droits Admin)"
echo "================================================================"

# 1. Priorité à uv (ultra-rapide, gère automatiquement Python + dépendances)
if command -v uv >/dev/null 2>&1; then
    echo "[INFO] 'uv' détecté. Démarrage du simulateur..."
    exec uv run --with-requirements "${PROJECT_ROOT}/requirements.txt" python3 "${PROJECT_ROOT}/launcher.py" "$@"
fi

# 2. Fallback sur python3 standard + venv isolé dans ~/.local/share
if command -v python3 >/dev/null 2>&1; then
    if [ ! -x "${VENV_DIR}/bin/python" ]; then
        echo "[INFO] Création de l'environnement virtuel utilisateur dans ${VENV_DIR}..."
        mkdir -p "${USER_ENV_DIR}"
        python3 -m venv "${VENV_DIR}"
        echo "[INFO] Installation des dépendances Python (1ère exécution uniquement)..."
        "${VENV_DIR}/bin/pip" install --upgrade pip --quiet
        "${VENV_DIR}/bin/pip" install -r "${PROJECT_ROOT}/requirements.txt"
    fi
    exec "${VENV_DIR}/bin/python" "${PROJECT_ROOT}/launcher.py" "$@"
fi

echo "[ERREUR] Ni 'uv' ni 'python3' n'est disponible sur cette machine."
echo "         Utilisez le binaire autonome IoT-Data-Simulator-Linux-x64.zip depuis GitHub Releases."
exit 1
