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

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `app/models/variable.py`, `app/platforms/`, `app/storage/repository.py`, `app/mqtt/client.py`.
- **Utilisé par** : `app/main.py` (cycle de vie FastAPI) et `app/api/routes.py` (contrôle et injection).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Sécurité)** : Interdiction d'ajouter des évaluateurs dynamiques type `eval()` ou `ast.literal_eval()`. Tout calcul doit rester mathématiquement strict et pur.
- **Règle 2 (Anomalies)** : L'anomalie `SPIKE` s'auto-réinitialise après 3 ticks via `_anomaly_counters` pour ne pas corrompre le signal de façon permanente.
- **Règle 3 (Timeout)** : `AnomalyType.TIMEOUT` n'interrompt pas le calcul de valeur, mais saute l'appel de publication MQTT (`continue`), simulant une rupture de transmission radio.
