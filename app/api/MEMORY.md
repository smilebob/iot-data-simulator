# 📦 Mémoire du Module : API REST & WebSockets

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/api/` | **Dernière MAJ** : 2026-10-23 | **Version** : 2.2.0

## 🎯 Rôle & Responsabilité
Contrôleurs HTTP FastAPI (CRUD, configuration broker, forçage manuel, injection d'anomalies, import CSV, génération et import/export exhaustif de cas d'usage métiers ThingsBoard) et gestionnaire de connexions WebSockets pour la télémétrie en temps réel.

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`routes.py:router`](file:///home/pierre/Projets/iot-data-simulator/app/api/routes.py) | Router APIRouter FastAPI (préfixe `/api`) | Endpoints REST (`/devices`, `/variables`, `/broker`, `/broker/test`, `/logs`, `/status`, `/scenario`, `/presets/catalog`, `/presets/instantiate`, `/presets/{id}/export`, `/presets/export/all`, `/presets/import`, `DELETE /presets/{id}`) |
| [`websocket.py:WebSocketManager`](file:///home/pierre/Projets/iot-data-simulator/app/api/websocket.py) | Hub de diffusion WebSocket non-bloquant | `connect()`, `disconnect()`, `broadcast_json(message)` (télémétrie & logs) |
| [`auth.py:auth_router`](file:///home/pierre/Projets/iot-data-simulator/app/api/auth.py) | Routes d'authentification et gestion RBAC | `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `/api/users` |
| [`main.py:/healthz`](file:///home/pierre/Projets/iot-data-simulator/app/main.py#L86-L110) | Sonde de santé CIS Rule 4.6 enrichie | Retourne version, statut moteur/MQTT, devices, `http_rpc_listeners`, `http_attribute_listeners`, 10 derniers logs |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `fastapi`, `app/models/`, `app/storage/repository.py`, `app/core/engine.py`, `app/core/equipment_catalog.py`, `app/mqtt/client.py`, `app/mqtt/diagnostics.py`, `app/core/logger.py`.
- **Utilisé par** : `app/main.py` (`app.include_router(api_router)`).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Nettoyage des sockets mortes)** : Dans `broadcast_json()`, toute socket levant une exception d'envoi est automatiquement isolée et retirée de la liste active pour éviter les fuites de descripteurs de fichiers.
- **Règle 2 (MQTT Discovery Home Assistant)** : Lors de l'enregistrement d'une variable (`save_variable`), si l'équipement est de type `homeassistant`, les trames retain de découverte sont immédiatement transmises au broker.
- **Règle 3 (Synchronisation clients MQTT et devices)** : Lors de la modification ou suppression d'un équipement (`save_device` / `delete_device`), appeler impérativement `mqtt.remove_device_client(device_id)` pour fermer la socket existante et forcer sa recréation avec les nouveaux paramètres/tokens.
- **Règle 4 (Diffusion Temps Réel RPC/Attributs)** : Lorsque le moteur `SimulationEngine` reçoit un ordre RPC ou un attribut partagé ThingsBoard modifiant une variable, un message WebSocket `variable_updated` est immédiatement diffusé pour synchroniser l'affichage de l'IHM web sans rechargement.
- **Règle 5 (Contrôle Asynchrone du Moteur)** : Les routes `start_simulation` et `stop_simulation` (`/api/scenario/start` et `/api/scenario/stop`) DOIVENT être `async def` afin de s'exécuter dans la boucle d'événements principale FastAPI. Déclarer ces méthodes en `def` synchrone provoquait l'exécution dans un thread pool `anyio` sans boucle active (`RuntimeError: no running event loop`), bloquant le moteur.
- **Règle 6 (Import / Export de Presets)** : `POST /api/presets/import` prend en charge à la fois `multipart/form-data` (upload direct de fichier depuis l'IHM) et `application/json` (API REST). La route `DELETE /api/presets/{preset_id}` bloque toute tentative de suppression d'un modèle d'usine avec un statut 400. Les routes d'exportation fixent systématiquement le header `Content-Disposition: attachment; filename="..."`.
