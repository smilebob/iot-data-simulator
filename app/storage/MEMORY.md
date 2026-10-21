# 📦 Mémoire du Module : Storage & Persistence

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/storage/` | **Dernière MAJ** : 2026-10-21

## 🎯 Rôle & Responsabilité
Couche de persistance atomique thread-safe assurant la sauvegarde et la restauration de la configuration complète (équipements, variables, broker) sous forme de fichier JSON unique.

## 🗂️ Fichiers & Composants Clés
| Fichier / Export | Rôle | Entrées / Sorties Principales |
| :--- | :--- | :--- |
| [`repository.py:StorageRepository`](file:///home/pierre/Projets/iot-data-simulator/app/storage/repository.py) | Référentiel en mémoire avec écriture atomique sur disque | `get_devices()`, `save_device()`, `get_variables()`, `save_variable()`, `export_scenario()`, `import_scenario()` |

## 🔄 Dépendances & Flux de Données
- **Dépend de** : `app/models/` (validation Pydantic), `json`, `os`, `threading`.
- **Fichier Persistant** : `data/simulator_state.json` (monté en volume Docker).
- **Utilisé par** : `app/core/engine.py` (lecture des variables à exécuter) et `app/api/routes.py` (CRUD).

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Écriture Atomique)** : Ne jamais écrire directement dans `self.file_path` ! L'écriture se fait toujours dans un fichier temporaire `*.tmp` suivi d'un `os.replace()` atomique pour garantir l'absence de corruption en cas de coupure de courant ou `kill -9`.
- **Règle 2 (Suppression en cascade)** : `delete_device(device_id)` supprime automatiquement toutes les variables associées à cet équipement pour éviter les orphelins.
- **Règle 3 (Bootstrapping)** : Si le fichier `data/simulator_state.json` est absent, `_init_defaults()` injecte automatiquement les deux équipements de démo réalistes (Station Météo ThingsBoard + Compresseur Industriel).
