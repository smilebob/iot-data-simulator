# 📦 Mémoire du Module : Core Simulation Engine

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/core/` | **Dernière MAJ** : 2026-10-23 | **Version** : 2.2.0

## 🎯 Rôle & Responsabilité
Moteur d'exécution asynchrone non-bloquant responsable du calcul périodique (tick 500ms), de l'évaluation mathématique sécurisée, du rejeu de séries temporelles, de l'injection d'anomalies, du pilotage bidirectionnel (Attributs Partagés ThingsBoard et RPC) et de la gestion de la bibliothèque de cas d'usage métiers (32 natifs + personnalisés importés/exportés).

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`engine.py:SimulationEngine`](file:///home/pierre/Projets/iot-data-simulator/app/core/engine.py) | Boucle `asyncio`, écoute Attributs Partagés (`_poll_http_attributes_worker`), RPC (`_poll_http_rpc_worker`), publication & broadcast WS | `start()`, `stop()`, `trigger_anomaly(var_id, anomaly)` |
| [`generators.py:MathSignalGenerator`](file:///home/pierre/Projets/iot-data-simulator/app/core/generators.py) | Générateur mathématique pur déterministe (sans `eval`) | `generate(mode, config, elapsed, prev_val, data_type)` -> `Any` |
| [`replay.py:ReplayEngine`](file:///home/pierre/Projets/iot-data-simulator/app/core/replay.py) | Évaluateur de tables de points avec interpolation & parseur CSV | `evaluate(config, elapsed, data_type)` -> `Any`, `parse_csv_points(str)` -> `List[TimestampedPoint]` |
| [`equipment_catalog.py`](file:///home/pierre/Projets/iot-data-simulator/app/core/equipment_catalog.py) | Référentiel des 32 presets d'usine, persistance thread-safe des presets personnalisés (`custom_presets.json`), packages d'exportation v2.1.0 et moteur d'importation | `get_equipment_catalog()`, `load_custom_presets()`, `save_custom_preset()`, `delete_custom_preset()`, `build_preset_export_package()`, `build_all_presets_export_package()`, `import_preset_data()`, `instantiate_preset()` |
| [`dashboard_generator.py:generate_thingsboard_dashboard`](file:///home/pierre/Projets/iot-data-simulator/app/core/dashboard_generator.py) | Générateur de tableaux de bord ThingsBoard 4.3 / 3.x avec interrupteurs `single_switch` (Action Widgets sur `SHARED_SCOPE`) | `generate_thingsboard_dashboard(device, vars)` -> `dict (JSON TB)` |
| [`scada_synoptics.py:get_scada_synoptic_html`](file:///home/pierre/Projets/iot-data-simulator/app/core/scada_synoptics.py) | Rendu vectoriel SVG des 32 synoptiques SCADA P&ID/SLD animés | `get_scada_synoptic_html(device, vars, preset_id)` -> `str (HTML/SVG)` |
| [`physics.py:PhysicsEvaluator`](file:///home/pierre/Projets/iot-data-simulator/app/core/physics.py) | Résolution causale multi-passes des variables dérivées et intégrateurs | `evaluate_derived_variables(...)`, `evaluate_integrators(...)` |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `app/models/variable.py`, `app/platforms/`, `app/storage/repository.py`, `app/mqtt/client.py`, `app/transports/manager.py`.
- **Utilisé par** : `app/main.py` (cycle de vie FastAPI) et `app/api/routes.py` (contrôle et injection).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Sécurité)** : Interdiction d'ajouter des évaluateurs dynamiques type `eval()` ou `ast.literal_eval()`. Tout calcul doit rester mathématiquement strict et pur.
- **Règle 2 (Anomalies)** : L'anomalie `SPIKE` s'auto-réinitialise après 3 ticks via `_anomaly_counters` pour ne pas corrompre le signal de façon permanente.
- **Règle 3 (Timeout)** : `AnomalyType.TIMEOUT` n'interrompt pas le calcul de valeur, mais saute l'appel de publication MQTT (`continue`), simulant une rupture de transmission radio.
- **Règle 4 (ThingsBoard 4.3 Data Binding)** : Dans `dashboard_generator.py`, pour le widget `html_value_card`, le champ `label` des `dataKeys` DOIT TOUJOURS être égal au nom technique `clean_key` (ex: `debit_vehicules`), car le moteur de templates de ThingsBoard 4.3 associe les balises `${cle}` uniquement avec le `label` du dataKey.
- **Règle 5 (Pilotage Bidirectionnel & Attributs Partagés)** : Pour chaque variable de type ATTRIBUTE booléen, `dashboard_generator.py` génère désormais un interrupteur `system.single_switch` configuré en Action Widget (`action: SET_ATTRIBUTE`, `scope: SHARED_SCOPE`). Ce mécanisme évite les erreurs 504 Gateway Timeout propres au routage RPC ThingsBoard. Dans `engine.py`, `_poll_http_attributes_worker` écoute en Long-Polling HTTP `/api/v1/{token}/attributes/updates?timeout=20000`, intercepte les modifications en < 50ms, met à jour la variable, force l'état manuel (`manual_override = True`), acquitte l'attribut client sur ThingsBoard et propage par WebSocket.
- **Règle 6 (Robustesse de la boucle _run_loop)** : Toujours importer `PlatformType` et `TransportProtocol` dans `engine.py` et accéder à leurs valeurs via `getattr(obj, "value", str(obj))` pour tolérer les instances désérialisées sans validation stricte. `TransportProtocol` contient uniquement `MQTT`, `HTTP` et `COAP` (aucun membre `MQTTS` ou `WSS`). Tout appel WebSocket doit impérativement respecter la structure `{"type": "telemetry", "data": {...}}`.
- **Règle 7 (Modèles Personnalisés & Packages v2.1.0)** : Les modèles personnalisés sont persistés dans `data/custom_presets.json` sous un verrou ré-entrant `threading.RLock()`. Les 32 modèles d'usine natifs sont immuables et protégés (tentative de suppression = ValueError). En cas de conflit d'identifiant à l'import, un suffixe `_custom` est automatiquement attribué. Tout export de package doit inclure les 4 volets (`preset`, `dashboard_template`, `csv_template`, `instantiation_spec`).
