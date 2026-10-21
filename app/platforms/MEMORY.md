# 📦 Mémoire du Module : IoT Platform Adapters

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/platforms/` | **Dernière MAJ** : 2026-10-21

## 🎯 Rôle & Responsabilité
Couche d'abstraction (Pattern Adapter / Strategy) isolant les spécificités des protocoles et formats de données de chaque plateforme IoT (ThingsBoard, Home Assistant, Datacake, Generic).

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`base.py:BasePlatformAdapter`](file:///home/pierre/Projets/iot-data-simulator/app/platforms/base.py) | Classe abstraite imposant le contrat d'interface | `get_default_topic()`, `format_message()`, `get_discovery_messages()` |
| [`thingsboard.py:ThingsBoardAdapter`](file:///home/pierre/Projets/iot-data-simulator/app/platforms/thingsboard.py) | Télémétrie horodatée (`ts`, `values`), Attributs et analyse RPC | Sortie : `{"ts": ..., "values": {var_id: val}}` sur `v1/devices/me/telemetry` |
| [`homeassistant.py:HomeAssistantAdapter`](file:///home/pierre/Projets/iot-data-simulator/app/platforms/homeassistant.py) | MQTT Discovery auto & state topic | Sortie : config sur `homeassistant/sensor/.../config` |
| [`datacake.py:DatacakeAdapter`](file:///home/pierre/Projets/iot-data-simulator/app/platforms/datacake.py) | Format JSON avec champ `timestamp` en secondes | Sortie : `datacake/{device.id}/telemetry` |
| [`generic.py:GenericMqttAdapter`](file:///home/pierre/Projets/iot-data-simulator/app/platforms/generic.py) | Topic libre ou `{device.id}/{var.id}` | JSON générique avec métadonnées |
| [`__init__.py:get_adapter`](file:///home/pierre/Projets/iot-data-simulator/app/platforms/__init__.py) | Factory retournant l'instance singleton de l'adaptateur | `get_adapter(PlatformType)` -> `BasePlatformAdapter` |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `app/models/device.py`, `app/models/variable.py`.
- **Utilisé par** : `app/core/engine.py` (formatage avant publication MQTT) et `app/api/routes.py` (auto-découverte HA).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1** : Si l'utilisateur a renseigné un topic explicite dans `variable.topic`, l'adaptateur **doit** le respecter en priorité au lieu du topic par défaut.
- **Règle 2** : Pour ThingsBoard, l'horodatage `ts` est impérativement en **millisecondes** (`int(now * 1000)`), alors que Datacake attend des **secondes** (`int(now)`).
- **Règle 3 (ThingsBoard 4.3 Attributs & RPC)** : Les attributs partagés sont publiés et reçus sur `v1/devices/me/attributes`. Les commandes directes transitent par `v1/devices/me/rpc/request/{id}` et requièrent une réponse sur `v1/devices/me/rpc/response/{id}` pour satisfaire les widgets interactifs de ThingsBoard 4.3 (Round Switch, Input Forms).
