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

## 3. Gestion et Centralisation des Logs

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

### Export vers Stack ELK / Loki / Promtail
Les conteneurs écrivent sur `stdout` et `stderr`. Le driver standard de Docker (`json-file`) permet l'aspiration automatique par Promtail, Fluentbit ou Logstash sans aucun agent supplémentaire dans le conteneur.
