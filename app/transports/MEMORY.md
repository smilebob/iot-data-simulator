# 📦 Mémoire du Module : Transports Réseau & Multi-Protocoles (MQTT, HTTP, CoAP)

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/transports/` | **Dernière MAJ** : 2026-10-21

## 🎯 Rôle & Responsabilité
Couche d'abstraction et d'aiguillage des protocoles de transport IoT pour ThingsBoard et les autres plateformes :
1. **MQTT** (Courtier TCP persistant / WebSockets via `MqttManager`)
2. **HTTP REST** (API ThingsBoard v1 en HTTPS/HTTP via `ThingsBoardHttpClient`)
3. **CoAP** (Constrained Application Protocol RFC 7252 sur UDP via `ThingsBoardCoapClient`)

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`manager.py:TransportManager`](file:///home/pierre/Projets/iot-data-simulator/app/transports/manager.py) | Aiguilleur centralisé des flux télémétriques selon `device.protocol` | `publish(...)` -> `(success, protocol, channel_info)` |
| [`http_client.py:ThingsBoardHttpClient`](file:///home/pierre/Projets/iot-data-simulator/app/transports/http_client.py) | Client HTTP/HTTPS asynchrone pour l'API ThingsBoard v1 | `post_payload(...)`, `test_connectivity(...)` |
| [`coap_client.py:ThingsBoardCoapClient`](file:///home/pierre/Projets/iot-data-simulator/app/transports/coap_client.py) | Client UDP RFC 7252 natif avec encodage d'options (Uri-Path, Content-Format) | `send_payload(...)`, `test_connectivity(...)` |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `app/models/`, `app/mqtt/`, `app/platforms/`, `app/storage/`, `httpx` (avec fallback `urllib`).
- **Utilisé par** : `app/core/engine.py` (boucle d'envoi), `app/api/routes.py` (tests directs).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Contournement Cloudflare)** : Pour les instances ThingsBoard protégées par reverse proxy Cloudflare (ex: ports 1883/8883 bloqués), le protocole `HTTP` sur le port 443 est la solution native immédiate pour envoyer de la télémétrie.
- **Règle 2 (Encodage RFC 7252 CoAP)** : Les options CoAP doivent impérativement être triées par numéro d'option croissant et encodées avec leurs deltas respectifs (Option 11 pour chaque segment d'Uri-Path, puis Option 12 pour `Content-Format: application/json`).
