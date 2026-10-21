# ========================================================
# Étape 1 : Builder (Compilation & Dépendances)
# ========================================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Installation des dépendances dans un dossier temporaire isolé
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ========================================================
# Étape 2 : Image Finale Minimale Sécurisée (Conforme CIS)
# ========================================================
FROM python:3.11-slim-bookworm AS runner

# Métadonnées
LABEL maintainer="IoT Engineering Team" \
      description="IoT Data Simulator for ThingsBoard & Multi-Platform" \
      version="1.0.0"

# Définition des variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH

WORKDIR /app

# CIS Benchmark Rule 4.1 : Création d'un utilisateur non-root dédié (UID 10001)
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -m -d /home/appuser -s /sbin/nologin -c "Application User" appuser && \
    mkdir -p /app/data /app/mosquitto && \
    chown -R appuser:appuser /app /home/appuser

# Copie des packages Python depuis le builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copie du code source de l'application
COPY --chown=appuser:appuser app/ /app/app/

# Exécution sous utilisateur non privilégié (CIS Rule 4.1)
USER appuser

# Exposition des ports (8000 : Web GUI & API)
EXPOSE 8000

# CIS Benchmark Rule 4.6 : Sonde de santé intégrée
HEALTHCHECK --interval=20s --timeout=4s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

# Démarrage sécurisé du serveur ASGI
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
