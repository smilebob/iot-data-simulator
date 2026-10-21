# 📦 Mémoire du Module : MQTT Network Layer

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/mqtt/` | **Dernière MAJ** : 2026-10-21

## 🎯 Rôle & Responsabilité
Gestion des sockets réseau MQTT via `paho-mqtt` v2.x, chiffrement strict TLS 1.2+, reconnexion automatique en arrière-plan, et orchestration multi-clients (support de tokens ThingsBoard distincts par équipement).

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`client.py:MqttConnection`](file:///home/pierre/Projets/iot-data-simulator/app/mqtt/client.py) | Client Paho unitaire thread-safe avec context TLS strict | `start()`, `stop()`, `publish(topic, payload, qos=1)` -> `bool` |
| [`client.py:MqttManager`](file:///home/pierre/Projets/iot-data-simulator/app/mqtt/client.py) | Hub multi-clients : gère le client global et les clients dédiés par token | `get_or_create_device_client(device_id, token)` -> `MqttConnection` |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `app/models/broker.py`, `ssl`, `paho.mqtt.client`.
- **Utilisé par** : `app/core/engine.py` (publication des messages), `app/api/routes.py` (modification dynamique du broker).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Multi-Device ThingsBoard)** : Si un équipement possède un `device.token`, il **doit** impérativement émettre via son client dédié créé par `get_or_create_device_client()` (où `username=token`), car ThingsBoard associe l'identité du device au username MQTT de la session.
- **Règle 2 (Thread Safety)** : Les publications appellent `client.publish()` à l'intérieur d'un `with self._lock:` pour éviter toute collision inter-threads lors de rafales télémétriques.
- **Règle 3 (Paho v2 vs v1)** : Le constructeur gère le fallback gracieux `CallbackAPIVersion.VERSION2` vers `VERSION1` pour compatibilité maximale.
