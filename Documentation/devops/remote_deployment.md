# 🌐 Déploiement Distant & Reverse Proxy

Ce guide décrit comment déployer l'application sur un serveur distant (VPS, VM Cloud, instance AWS EC2, Scaleway, Hetzner) avec un nom de domaine et un certificat SSL/TLS gratuit Let's Encrypt.

---

## 1. Schéma d'Architecture de Production

```
Internet (Navigateur Client & Plateforme ThingsBoard)
                │ (Ports 80 & 443)
                ▼
      ┌──────────────────┐
      │   Reverse Proxy  │ (Terminaison HTTPS / WSS)
      │  (Nginx/Traefik) │
      └─────────┬────────┘
                │
     ┌──────────┴──────────┐
     ▼                     ▼
Port 8000              Port 8080
[Simulateur Web & API] [MQTTX Web]
```

---

## 2. Configuration d'un Reverse Proxy Nginx avec Support WebSockets

Voici un exemple de bloc de configuration Nginx complet pour votre domaine (ex: `simulator.mondomaine.com`) :

```nginx
server {
    listen 80;
    server_name simulator.mondomaine.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name simulator.mondomaine.com;

    ssl_certificate /etc/letsencrypt/live/simulator.mondomaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/simulator.mondomaine.com/privkey.pem;

    # Protocoles stricts
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Application Simulateur
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Support obligatoire des WebSockets pour la télémétrie temps réel
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

---

## 3. Configuration des Variables d'Environnement

Sur votre serveur de production, créez un fichier `.env` :

```bash
# Pointer vers ThingsBoard Cloud ou un broker distant
MQTT_BROKER_HOST=mqtt.thingsboard.cloud
MQTT_BROKER_PORT=1883
MQTT_USE_TLS=false
MQTT_USERNAME=VOTRE_TOKEN_THINGSBOARD
MQTT_PASSWORD=
```
Puis démarrez avec :
```bash
docker compose --env-file .env up -d
```
