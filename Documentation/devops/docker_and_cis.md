# 🛡️ Conteneurisation & Conformité CIS Docker Benchmark

Ce document détaille les mesures techniques mises en œuvre pour assurer la conformité avec le standard international de sécurité **CIS Docker Benchmark**.

---

## 📋 Tableau de Correspondance CIS Benchmark

| Règle CIS | Intitulé | Implémentation dans le Projet |
| :--- | :--- | :--- |
| **Rule 4.1** | *Ensure a user for the container has been created* | L'image crée explicitement l'utilisateur `appuser` (`UID 10001`, `GID 10001`) avec `USER appuser`. L'application ne tourne **jamais** en `root`. |
| **Rule 4.3** | *Ensure unnecessary packages are not installed in image* | Utilisation d'un **Multi-stage build** : les outils d'installation (`pip`) et compilateurs restent dans l'étape `builder` ; l'image `runner` ne contient que le runtime minimal Debian Slim. |
| **Rule 4.4** | *Ensure images are scanned and free of vulnerabilities* | Base `python:3.11-slim-bookworm` à jour, zéro dépendance superflue. |
| **Rule 4.5** | *Ensure Content trust for Docker is enabled / No secrets in image* | Aucun mot de passe, clé privée ou token n'est codé en dur dans le Dockerfile. Tout passe par variables d'environnement (`.env`). |
| **Rule 4.6** | *Ensure HEALTHCHECK instructions have been added to the container image* | Instruction `HEALTHCHECK` intégrée interrogeant `/healthz` toutes les 20 secondes. |
| **Rule 5.16** | *Ensure Linux Kernel Capabilities are restricted* | `cap_drop: [ALL]` appliqué dans `docker-compose.yml` : toutes les capacités root du kernel Linux sont révoquées. |
| **Rule 5.17** | *Ensure no-new-privileges flag is set* | `security_opt: ["no-new-privileges:true"]` configuré sur tous les services de la stack pour empêcher l'élévation de privilèges via `setuid`. |

---

## 🔍 Analyse du Dockerfile Multi-Stage

Dans [Dockerfile](file:///home/pierre/Projets/iot-data-simulator/Dockerfile) :

```dockerfile
# 1. Étape Builder
FROM python:3.11-slim-bookworm AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 2. Étape Runner
FROM python:3.11-slim-bookworm AS runner
WORKDIR /app

# Création explicite utilisateur non privilégié
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -m -d /home/appuser -s /sbin/nologin appuser && \
    mkdir -p /app/data /app/mosquitto && \
    chown -R appuser:appuser /app /home/appuser

# Copie des packages sans aucun outil de compilation
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser app/ /app/app/

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=4s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1
```

---

## 🔒 Analyse du Durcissement `docker-compose.yml`

Dans [docker-compose.yml](file:///home/pierre/Projets/iot-data-simulator/docker-compose.yml) :
* Réseau bridge dédié et isolé (`iot-simulator-net`).
* Configuration `mosquitto` montée en lecture seule (`:ro`) : empêche toute modification du fichier de configuration depuis l'intérieur du conteneur.
* Persistance découplée : volumes `./data` et `./mosquitto/data`.
