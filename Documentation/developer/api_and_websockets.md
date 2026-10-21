# 🌐 API REST & Protocole WebSockets

## Contrats d'API REST

Tous les endpoints sont préfixés par `/api`. Les requêtes et réponses utilisent le format JSON standard. L'accès aux endpoints est contrôlé par le module RBAC (Admin, Opérateur, Observateur).

### 0. Authentification & Gestion des Utilisateurs
* **`POST /api/auth/login`** : Authentifie l'utilisateur (`username`, `password`) et émet un cookie `access_token` HTTP-Only sécurisé.
* **`POST /api/auth/logout`** : Clôture la session et révoque le cookie d'authentification.
* **`GET /api/auth/me`** : Retourne les informations de l'utilisateur connecté (`username`, `role`, `full_name`).
* **`POST /api/auth/change-password`** : Permet à l'utilisateur connecté de modifier son mot de passe.
* **`GET /api/users`** *(Admin)* : Liste tous les utilisateurs enregistrés avec leurs rôles.
* **`POST /api/users`** *(Admin)* : Crée un compte (`username`, `full_name`, `role`, `password`).
* **`DELETE /api/users/{username}`** *(Admin)* : Supprime un compte utilisateur (protection du dernier admin).
* **`POST /api/users/{username}/reset-password`** *(Admin)* : Réinitialise le mot de passe d'un utilisateur.

### 1. Équipements (`/api/devices`)
* **`GET /api/devices`** : Retourne la liste de tous les équipements configurés.
* **`POST /api/devices`** : Crée ou met à jour un équipement.
  * *Body* : `{ "id": "comp_01", "name": "Compresseur", "platform": "thingsboard", "protocol": "mqtt" | "http" | "coap", "token": "TOKEN_SECRET", "custom_host": null, "custom_port": null, "use_tls": true, "enabled": true }`
* **`DELETE /api/devices/{id}`** : Supprime un équipement ainsi que toutes les variables qui lui sont rattachées.
* **`POST /api/devices/{id}/test`** : Exécute un test de communication immédiat avec la plateforme (MQTT, HTTP, ou CoAP) pour cet équipement.
* **`POST /api/devices/test-custom`** : Teste la communication avec une configuration d'équipement à la volée avant son enregistrement.

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
* **`GET /api/status`** : Retourne l'état du moteur (`engine_running`), l'état de connexion MQTT (`mqtt_connected`), le compteur de messages publiés et le numéro de version de l'application.
* **`POST /api/simulation/start`** : Démarre la boucle de simulation.
* **`POST /api/simulation/stop`** : Met en pause la boucle de simulation.
* **`GET /api/broker`** / **`POST /api/broker`** : Lecture et modification à chaud de la configuration du broker MQTT (hôte, port, transport `tcp`/`websockets`, `ws_path`, TLS, identifiants).
* **`POST /api/broker/test`** : Teste la connectivité directe vers le broker spécifié (résolution DNS, détection CDN Cloudflare, socket TCP/TLS ou WebSockets, calcul de latence et recommandations).

### 5. Journaux & Diagnostics
* **`GET /api/logs`** : Récupère les entrées de logs applicatifs récentes conservées en mémoire vive (tampon circulaire de 200 lignes, filtrable par `?level=...` et `?limit=...`).
* **`DELETE /api/logs`** : Purge la file de journaux en mémoire vive.

### 6. Export / Import de Scénario
* **`GET /api/scenario/export`** : Télécharge l'état complet du simulateur en JSON.
* **`POST /api/scenario/import`** : Restaure un scénario complet et applique la configuration broker à chaud.

---

## ⚡ Streaming WebSockets (`/ws/live`)

Le frontend établit une connexion WebSocket permanente sur `/ws/live`.
Deux types de trames JSON sont diffusées en temps réel :

1. **Événements de Télémétrie (`type: "telemetry"`)** :
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

2. **Événements de Journalisation (`type: "log"`)** :
```json
{
  "type": "log",
  "data": {
    "timestamp": "2026-10-21T14:30:00.123456",
    "level": "ERROR",
    "name": "iot_sim.mqtt",
    "message": "Erreur de connexion broker mosquitto:1883 : Connection refused"
  }
}
```
Ce flux permet le rafraîchissement sans rechargement de page, l'affichage instantané des alertes d'erreurs et la consultation de la console de logs intégrée sans avoir à ouvrir de terminal Docker.
