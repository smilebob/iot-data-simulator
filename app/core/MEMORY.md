# 📦 Mémoire du Module : Core Simulation Engine

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/core/` | **Dernière MAJ** : 2026-10-21

## 🎯 Rôle & Responsabilité
Moteur d'exécution asynchrone non-bloquant responsable du calcul périodique (tick 500ms), de l'évaluation mathématique sécurisée, du rejeu de séries temporelles, et de l'injection d'anomalies.

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`engine.py:SimulationEngine`](file:///home/pierre/Projets/iot-data-simulator/app/core/engine.py) | Boucle `asyncio`, trigger de publication MQTT & broadcast WS | `start()`, `stop()`, `trigger_anomaly(var_id, anomaly)` |
| [`generators.py:MathSignalGenerator`](file:///home/pierre/Projets/iot-data-simulator/app/core/generators.py) | Générateur mathématique pur déterministe (sans `eval`) | `generate(mode, config, elapsed, prev_val, data_type)` -> `Any` |
| [`replay.py:ReplayEngine`](file:///home/pierre/Projets/iot-data-simulator/app/core/replay.py) | Évaluateur de tables de points avec interpolation & parseur CSV | `evaluate(config, elapsed, data_type)` -> `Any`, `parse_csv_points(str)` -> `List[TimestampedPoint]` |
| [`equipment_catalog.py:get_equipment_catalog`](file:///home/pierre/Projets/iot-data-simulator/app/core/equipment_catalog.py) | Référentiel des 32 presets d'équipements métiers classés par secteur | `EQUIPMENT_CATALOG`, `get_preset_by_id(id)` |
| [`dashboard_generator.py:generate_thingsboard_dashboard`](file:///home/pierre/Projets/iot-data-simulator/app/core/dashboard_generator.py) | Générateur de tableaux de bord ThingsBoard 4.3 / 3.x en thème Light | `generate_thingsboard_dashboard(device, vars)` -> `dict (JSON TB)` |
| [`scada_synoptics.py:get_scada_synoptic_html`](file:///home/pierre/Projets/iot-data-simulator/app/core/scada_synoptics.py) | Rendu vectoriel SVG des 32 synoptiques SCADA P&ID/SLD animés | `get_scada_synoptic_html(device, vars, preset_id)` -> `str (HTML/SVG)` |
| [`physics.py:PhysicsEvaluator`](file:///home/pierre/Projets/iot-data-simulator/app/core/physics.py) | Résolution causale multi-passes des variables dérivées et intégrateurs | `evaluate_derived_variables(...)`, `evaluate_integrators(...)` |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `app/models/variable.py`, `app/platforms/`, `app/storage/repository.py`, `app/mqtt/client.py`.
- **Utilisé par** : `app/main.py` (cycle de vie FastAPI) et `app/api/routes.py` (contrôle et injection).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Sécurité)** : Interdiction d'ajouter des évaluateurs dynamiques type `eval()` ou `ast.literal_eval()`. Tout calcul doit rester mathématiquement strict et pur.
- **Règle 2 (Anomalies)** : L'anomalie `SPIKE` s'auto-réinitialise après 3 ticks via `_anomaly_counters` pour ne pas corrompre le signal de façon permanente.
- **Règle 3 (Timeout)** : `AnomalyType.TIMEOUT` n'interrompt pas le calcul de valeur, mais saute l'appel de publication MQTT (`continue`), simulant une rupture de transmission radio.
- **Règle 4 (ThingsBoard 4.3 Data Binding)** : Dans `dashboard_generator.py`, pour le widget `html_value_card`, le champ `label` des `dataKeys` DOIT TOUJOURS être égal au nom technique `clean_key` (ex: `debit_vehicules`), car le moteur de templates de ThingsBoard 4.3 associe les balises `${cle}` uniquement avec le `label` du dataKey.
- **Règle 5 (Pilotage Bidirectionnel & RPC)** : Pour chaque variable de type ATTRIBUTE, `dashboard_generator.py` génère un widget de contrôle interactif (`round_switch` pour les booléens, `update_multiple_attributes` pour les grandeurs réglables). Dans `engine.py`, `_handle_rpc` intercepte les requêtes RPC et les Shared Attributes, met à jour la variable, acquitte auprès de ThingsBoard (`v1/devices/me/rpc/response/+`) et propage par WebSocket.
- **Règle 6 (Robustesse de la boucle _run_loop)** : Toujours importer `PlatformType` et `TransportProtocol` dans `engine.py` et accéder à leurs valeurs via `getattr(obj, "value", str(obj))` pour tolérer les instances désérialisées sans validation stricte. `TransportProtocol` contient uniquement `MQTT`, `HTTP` et `COAP` (aucun membre `MQTTS` ou `WSS`). Tout appel WebSocket doit impérativement respecter la structure `{"type": "telemetry", "data": {...}}`.
