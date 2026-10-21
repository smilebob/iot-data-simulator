# 🚀 Documentation DevOps : Déploiement & Exploitation

Bienvenue dans la documentation opérationnelle du projet **IoT Data Simulator**. Ce guide est destiné aux ingénieurs DevOps et administrateurs systèmes chargés de déployer, sécuriser, monitorer et maintenir la solution en environnement de test, pré-production ou production.

---

## 🧭 Sommaire DevOps

1. [Conteneurisation & Conformité CIS Benchmark](docker_and_cis.md) : Analyse détaillée du `Dockerfile` multi-stage, options de sécurité Linux dans `docker-compose.yml`, non-root execution et principes de moindre privilège.
2. [Durcissement du Broker Mosquitto](mosquitto_hardening.md) : Configuration TLS 1.2/1.3, génération de certificats X.509, gestion des mots de passe et fichiers ACL.
3. [Supervision, Sondes & Logs](monitoring_and_health.md) : Endpoint `/healthz`, sondes de vivacité/disponibilité (Kubernetes / Docker healthcheck), centralisation des logs.
4. [Déploiement Distant & Reverse Proxy](remote_deployment.md) : Mise en production sur serveur dédié/cloud (VPS, EC2), reverse proxy Nginx / Traefik avec HTTPS (Let's Encrypt), variables d'environnement.

---

## ⚡ Commandes d'Exploitation Rapides

### Démarrage de la stack
```bash
docker compose up -d
```

### Vérification de l'état des conteneurs
```bash
docker compose ps
```

### Consultation des logs en direct
```bash
# Logs applicatifs (FastAPI + Simulation)
docker compose logs -f simulator

# Logs du broker Mosquitto
docker compose logs -f mosquitto

# Logs du visualiseur MQTTX Web
docker compose logs -f mqtt-web
```

### Arrêt et nettoyage propre
```bash
docker compose down
```
*(Les données de configuration restent préservées dans `./data/` et `./mosquitto/data/`)*
