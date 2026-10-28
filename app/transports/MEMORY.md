# 📦 Mémoire du Module : Transports Réseau & Multi-Protocoles (MQTT, HTTP, CoAP)

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/transports/` | **Dernière MAJ** : 2026-10-22 | **Version** : 2.0.0

## 🎯 Rôle & Responsabilité
Couche d'abstraction et d'aiguillage des protocoles de transport IoT pour ThingsBoard et les autres plateformes :
1. **MQTT** (Courtier TCP persistant / WebSockets via `MqttManager`)
2. **HTTP REST** (API ThingsBoard v1 en HTTPS/HTTP via `ThingsBoardHttpClient`) : Télémétrie, Attributs Clients, Attributs Partagés (`SHARED_SCOPE`) et RPC.
3. **CoAP** (Constrained Application Protocol RFC 7252 sur UDP via `ThingsBoardCoapClient`)

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`manager.py:TransportManager`](file:///home/pierre/Projets/iot-data-simulator/app/transports/manager.py) | Aiguilleur centralisé des flux télémétriques selon `device.protocol` | `publish(...)` -> `(success, protocol, channel_info)` |
| [`http_client.py:ThingsBoardHttpClient`](file:///home/pierre/Projets/iot-data-simulator/app/transports/http_client.py) | Client HTTP/HTTPS asynchrone pour l'API ThingsBoard v1 | `post_payload(...)`, `poll_attribute_updates(...)`, `get_shared_attributes(...)`, `poll_rpc(...)`, `respond_rpc(...)`, `test_connectivity(...)` |
| [`coap_client.py:ThingsBoardCoapClient`](file:///home/pierre/Projets/iot-data-simulator/app/transports/coap_client.py) | Client UDP RFC 7252 natif avec encodage d'options (Uri-Path, Content-Format) | `send_payload(...)`, `test_connectivity(...)` |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `app/models/`, `app/mqtt/`, `app/platforms/`, `app/storage/`, `httpx` (avec fallback `urllib`), annotations futures Python (`from __future__ import annotations`).
- **Utilisé par** : `app/core/engine.py` (boucle d'envoi, écoute des Attributs Partagés et RPC HTTP), `app/api/routes.py` (tests directs).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Contournement WAF Cloudflare & Headers)** : Pour les instances ThingsBoard sous Cloudflare (ex: `thingsboard.example.com`), tout appel HTTP (télémétrie, attributs, long-polling d'attributs `poll_attribute_updates`, RPC `poll_rpc` et réponse `respond_rpc`) DOIT comporter `DEFAULT_HEADERS` avec un `User-Agent` de navigateur standard (`Mozilla/5.0...`) et `Accept: application/json`. Sans cela, Cloudflare renvoie systématiquement une erreur 403 Forbidden.
- **Règle 2 (Pilotage par Attributs Partagés vs RPC)** : Sur les instances ThingsBoard où la Root Rule Chain n'intègre pas le nœud `TbSendRPCRequestNode`, les requêtes RPC (`/api/rpc/oneway`) génèrent un 504 Gateway Timeout. Le pilotage via Attributs Partagés (`SHARED_SCOPE` via `/api/v1/{token}/attributes/updates?timeout=20000`) est le mécanisme industriel 100 % fiable : il s'exécute en < 50ms et ne dépend d'aucun routage de règle RPC.
- **Règle 3 (Typing Python)** : Toujours importer `List` explicitement ou utiliser `from __future__ import annotations` en tête de fichier pour éviter les erreurs `NameError: name 'List' is not defined` à l'initialisation Uvicorn sous Python 3.11+.
- **Règle 4 (Encodage RFC 7252 CoAP)** : Les options CoAP doivent impérativement être triées par numéro d'option croissant et encodées avec leurs deltas respectifs (Option 11 pour chaque segment d'Uri-Path, puis Option 12 pour `Content-Format: application/json`).
