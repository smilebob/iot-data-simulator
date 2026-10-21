# 📦 Mémoire du Module : MQTT Network Layer

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/mqtt/` | **Dernière MAJ** : 2026-10-21

## 🎯 Rôle & Responsabilité
Gestion des sockets réseau MQTT via `paho-mqtt` v2.x, chiffrement strict TLS 1.2+, reconnexion automatique en arrière-plan, et orchestration multi-clients (support de tokens ThingsBoard distincts par équipement).

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`client.py:MqttConnection`](file:///home/pierre/Projets/iot-data-simulator/app/mqtt/client.py) | Client Paho unitaire thread-safe avec TLS strict, support TCP brut & WebSockets | `start()`, `stop()`, `publish(topic, payload, qos=1)` -> `bool` |
| [`client.py:MqttManager`](file:///home/pierre/Projets/iot-data-simulator/app/mqtt/client.py) | Hub multi-clients : gère le client global et les clients dédiés par token | `update_global_config()`, `remove_device_client(device_id)`, `get_or_create_device_client(device_id, token)` |
| [`diagnostics.py:test_broker_connectivity`](file:///home/pierre/Projets/iot-data-simulator/app/mqtt/diagnostics.py) | Diagnostic réseau direct : DNS, détection Cloudflare proxy, test socket & latence | `test_broker_connectivity(config)` -> `dict` |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `app/models/broker.py`, `ssl`, `socket`, `paho.mqtt.client`, `app/core/logger.py`.
- **Utilisé par** : `app/core/engine.py` (publication des messages), `app/api/routes.py` (modification dynamique du broker, test de connectivité).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Multi-Device ThingsBoard)** : Si un équipement possède un `device.token`, il **doit** impérativement émettre via son client dédié créé par `get_or_create_device_client()` (où `username=token`), car ThingsBoard associe l'identité du device au username MQTT de la session.
- **Règle 2 (Cycle de vie & Reconnexion à chaud)** : `MqttManager.update_global_config()` **doit** appeler `self.stop_all()` pour arrêter TOUS les clients de devices existants avant de redémarrer avec le nouvel hôte/port, sinon les anciens clients continuent d'émettre vers le broker précédent ! De même, `remove_device_client(device_id)` doit être appelé lors de la modification ou suppression d'un équipement.
- **Règle 3 (Reverse Proxy CDN / Cloudflare)** : Si l'hôte ThingsBoard est derrière Cloudflare (ex: `easythings.app...`), les ports TCP bruts 1883 et 8883 sont bloqués/dropped. Il faut utiliser le transport `websockets` (WSS) sur le port 443 ou pointer vers l'adresse IP directe / un tunnel compatible.
- **Règle 4 (Thread Safety)** : Les publications appellent `client.publish()` à l'intérieur d'un `with self._lock:` pour éviter toute collision inter-threads lors de rafales télémétriques.
