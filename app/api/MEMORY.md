# 📦 Mémoire du Module : API REST & WebSockets

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/api/` | **Dernière MAJ** : 2026-10-21

## 🎯 Rôle & Responsabilité
Contrôleurs HTTP FastAPI (CRUD, configuration broker, forçage manuel, injection d'anomalies, import CSV) et gestionnaire de connexions WebSockets pour la télémétrie en temps réel.

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`routes.py:router`](file:///home/pierre/Projets/iot-data-simulator/app/api/routes.py) | Router APIRouter FastAPI (préfixe `/api`) | Endpoints REST (`/devices`, `/variables`, `/broker`, `/status`, `/scenario`) |
| [`websocket.py:WebSocketManager`](file:///home/pierre/Projets/iot-data-simulator/app/api/websocket.py) | Hub de diffusion WebSocket non-bloquant | `connect()`, `disconnect()`, `broadcast_json(message)` |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `fastapi`, `app/models/`, `app/storage/repository.py`, `app/core/engine.py`, `app/mqtt/client.py`.
- **Utilisé par** : `app/main.py` (`app.include_router(api_router)`).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Nettoyage des sockets mortes)** : Dans `broadcast_json()`, toute socket levant une exception d'envoi est automatiquement isolée et retirée de la liste active pour éviter les fuites de descripteurs de fichiers.
- **Règle 2 (MQTT Discovery Home Assistant)** : Lors de l'enregistrement d'une variable (`save_variable`), si l'équipement est de type `homeassistant`, les trames retain de découverte sont immédiatement transmises au broker.
