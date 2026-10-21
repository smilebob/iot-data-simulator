# 📊 Supervision, Sondes de Santé & Logs

Ce document présente la stratégie de monitoring, les métriques exposées et l'analyse des journaux d'événements.

---

## 1. Sondes de Santé (Healthchecks)

### Endpoint Applicatif `/healthz`
L'application expose une sonde de santé HTTP GET légère :
```bash
curl http://localhost:8000/healthz
```
*Réponse HTTP 200 OK :*
```json
{
  "status": "healthy",
  "engine_running": true,
  "mqtt_connected": true
}
```
*Si le client MQTT est déconnecté ou que la simulation a planté, le champ `status` permet aux orchestrateurs (Kubernetes / Docker Swarm) de détecter une anomalie.*

### Configuration Kubernetes
Pour un déploiement dans un cluster Kubernetes :
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 15
readinessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## 2. Métriques & Monitoring Temps Réel

Le endpoint `/api/status` fournit l'état opérationnel complet :
* `engine_running` (booléen) : État de la tâche d'arrière-plan.
* `mqtt_connected` (booléen) : État de la session MQTT active.
* `messages_published` (entier) : Compteur incrémental de paquets télémétriques transmis avec succès.
* `devices_count` / `variables_count` : Volume d'entités simulées.

---

## 3. Gestion, Diagnostic & Centralisation des Logs

### Format standardisé des logs
Les logs applicatifs utilisent la journalisation standard Python au format :
```
YYYY-MM-DD HH:MM:SS [LEVEL] [LOGGER_NAME]: Message
```
Exemple :
```
2026-10-21 12:35:10,123 [INFO] [iot_sim.engine]: Moteur de simulation démarré.
2026-10-21 12:35:10,145 [INFO] [iot_sim.mqtt]: Connecté au broker MQTT mosquitto:1883
```

### Tampon Circulaire en Mémoire Vive (In-Memory Ring Buffer)
Un gestionnaire de journalisation personnalisé (`InMemoryLogHandler` dans `app/core/logger.py`) capture les 200 derniers événements générés par le moteur et les clients MQTT. 
- **Diffusion Temps Réel** : Tout log produit est immédiatement retransmis par WebSocket (`type: "log"`) vers le frontend.
- **Accès API REST** : L'endpoint `GET /api/logs?level=ERROR&limit=100` permet l'interrogation programmatique ou le chargement initial dans l'IHM.
- **Console d'Administration Intégrée** : Le bouton *Logs* de l'IHM ouvre un terminal visuel avec coloration syntaxique des sévérités (INFO, WARNING, ERROR), recherche/filtrage et compteur d'erreurs non lues.

### Outil de Diagnostic Réseau Direct (`POST /api/broker/test`)
Pour faciliter le débogage lors du paramétrage d'un broker externe (notamment ThingsBoard Cloud ou serveurs d'entreprise protégés par reverse proxy) :
- **Résolution DNS** : Valide que le nom d'hôte est résolu en IPv4/IPv6.
- **Détection de Reverse Proxy CDN (Cloudflare)** : Vérifie si l'adresse IP appartient aux plages Cloudflare (qui bloquent par défaut le TCP brut sur les ports 1883/8883 sans Cloudflare Spectrum).
- **Test de Socket TCP & Handshake TLS** : Évalue l'ouverture du port et mesure la latence en millisecondes.
- **Recommandations Dynamiques** : Propose des solutions concrètes (ex: basculer en WebSockets sur le port 443, ouvrir les ports sur le pare-feu ou corriger le certificat).

### Export vers Stack ELK / Loki / Promtail
Les conteneurs écrivent simultanément sur `stdout` et `stderr`. Le driver standard de Docker (`json-file`) permet l'aspiration automatique par Promtail, Fluentbit ou Logstash sans aucun agent supplémentaire dans le conteneur.
