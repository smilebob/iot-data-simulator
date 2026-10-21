# 🌐 API REST & Protocole WebSockets

## Contrats d'API REST

Tous les endpoints sont préfixés par `/api`. Les requêtes et réponses utilisent le format JSON standard.

### 1. Équipements (`/api/devices`)
* **`GET /api/devices`** : Retourne la liste de tous les équipements configurés.
* **`POST /api/devices`** : Crée ou met à jour un équipement.
  * *Body* : `{ "id": "comp_01", "name": "Compresseur", "platform": "thingsboard", "token": "TOKEN_SECRET", "enabled": true }`
* **`DELETE /api/devices/{id}`** : Supprime un équipement ainsi que toutes les variables qui lui sont rattachées.

### 2. Variables (`/api/variables`)
* **`GET /api/variables`** : Liste toutes les variables (filtrable avec `?device_id=...`).
* **`POST /api/variables`** : Crée ou édite une variable.
* **`DELETE /api/variables/{id}`** : Supprime la variable spécifiée.

### 3. Contrôle & Défaillances
* **`POST /api/variables/{id}/anomaly`** :
  * *Body* : `{ "anomaly": "spike" | "drift" | "freeze" | "timeout" | "none", "magnitude": 50.0 }`
* **`POST /api/variables/{id}/override`** :
  * *Body* : `{ "manual_override": true, "manual_value": 42.5 }`
* **`POST /api/variables/{id}/csv`** :
  * Upload Multipart d'un fichier CSV pour alimenter la table de points.

### 4. État du Simulateur & Broker
* **`GET /api/status`** : Retourne l'état du moteur (`engine_running`), l'état de connexion MQTT (`mqtt_connected`), et le compteur de messages publiés.
* **`POST /api/simulation/start`** : Démarre la boucle de simulation.
* **`POST /api/simulation/stop`** : Met en pause la boucle de simulation.
* **`GET /api/broker`** / **`POST /api/broker`** : Lecture et modification à chaud de la configuration du broker MQTT.

### 5. Export / Import de Scénario
* **`GET /api/scenario/export`** : Télécharge l'état complet du simulateur en JSON.
* **`POST /api/scenario/import`** : Restaure un scénario complet et applique la configuration broker à chaud.

---

## ⚡ Streaming WebSockets (`/ws/live`)

Le frontend établit une connexion WebSocket permanente sur `/ws/live`.
Dès qu'une variable calcule une nouvelle valeur et publie sur MQTT, un événement JSON est diffusé à tous les clients connectés :

```json
{
  "type": "telemetry",
  "data": {
    "variable_id": "temperature",
    "device_id": "tb_station_01",
    "value": 24.52,
    "unit": "°C",
    "timestamp": 1729506400.123,
    "published": true,
    "topic": "v1/devices/me/telemetry",
    "anomaly": "none"
  }
}
```
Ce flux permet le rafraîchissement sans rechargement de page, l'animation du flash visuel et l'alimentation en direct des graphiques sparklines.
