# 🧠 Mémoire Globale du Projet : IoT Data Simulator

> **Dernière MAJ** : 2026-10-21 | **Statut** : Production / Opérationnel | **Conformité** : CIS Docker Benchmark & PEP 8

---

## 🎯 Vue d'Ensemble & Objectif
- **Description** : Simulateur de données IoT industriel pour démonstrations dynamiques sur **ThingsBoard** et plateformes compatibles MQTT (**Home Assistant**, **Datacake**, etc.). Permet la génération de signaux mathématiques purs paramétrables, le rejeu de séries temporelles (points/CSV), l'injection d'anomalies en direct (*Chaos Button*) et le forçage manuel.
- **Stack Technique** : Python 3.11+ (FastAPI, asyncio, Paho-MQTT v2, Pydantic v2), Eclipse Mosquitto 2.0, MQTTX Web, Docker Compose multi-stage non-root.
- **Point d'Entrée Principal** : [`app/main.py`](file:///home/pierre/Projets/iot-data-simulator/app/main.py)
- **Ports Exposés** :
  - `8000` : Web GUI & API REST
  - `8080` : MQTTX Web Inspector
  - `1883` : Broker MQTT Mosquitto TCP
  - `9001` : Mosquitto WebSockets

---

## 🚀 Commandes Essentielles
| Action | Commande | Notes / Contexte |
| :--- | :--- | :--- |
| **Docker Up** | `docker compose up -d` | Démarre la stack complète (Simulateur + Mosquitto + MQTTX Web) |
| **Docker Logs** | `docker compose logs -f simulator` | Suivi des logs applicatifs en temps réel |
| **Docker Down** | `docker compose down` | Arrêt propre (conserve les volumes `./data` et `./mosquitto/data`) |
| **Dev Local (sans Docker)** | `python3 -m uvicorn app.main:app --reload` | Nécessite `pip install -r requirements.txt` |
| **Check Santé** | `curl http://localhost:8000/healthz` | Vérification de la sonde HTTP liveness/readiness |

---

## 🗺️ Index des Sous-Modules (Cartographie Hiérarchique)
Pour intervenir sur un sous-module spécifique sans surcharger le contexte en tokens, chargez directement sa sous-mémoire :

| Sous-Dossier / Module | Rôle & Responsabilité | Sous-Mémoire IA |
| :--- | :--- | :--- |
| `app/core/` | Moteur de simulation `asyncio`, signaux mathématiques purs et rejeu de points | [app/core/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/core/MEMORY.md) |
| `app/platforms/` | Adaptateurs IoT (ThingsBoard, Home Assistant, Datacake, Generic) | [app/platforms/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/platforms/MEMORY.md) |
| `app/mqtt/` | Client Paho-MQTT v2, reconnexion, sessions TLS 1.2+ et multi-tokens | [app/mqtt/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/mqtt/MEMORY.md) |
| `app/storage/` | Persistance atomique JSON (`data/simulator_state.json`) et bootstrapping démo | [app/storage/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/storage/MEMORY.md) |
| `app/api/` | Routes FastAPI REST, WebSocket streaming (`/ws/live`), import CSV | [app/api/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/api/MEMORY.md) |
| `Documentation/` | Documentation exhaustive structurée (Développeur, DevOps, Utilisateur) | [Documentation/](file:///home/pierre/Projets/iot-data-simulator/Documentation/) |

---

## 📌 État Actuel & Feuille de Route
### ✅ Implémenté & Validé
- [x] Architecture modulaire par Adapters (`BasePlatformAdapter`)
- [x] Support ThingsBoard natif : télémétrie horodatée milliseconde, attributs, tokens par équipement
- [x] Moteur mathématique déterministe (Sinus, Cosinus, Triangle, Carré, Dent de scie, Rampe, Random walk, Gaussien, Constante) sans `eval()`
- [x] Rejeu temporel avec interpolation linéaire et upload CSV
- [x] Injection de pannes à la volée (*Spike*, *Drift*, *Freeze*, *Timeout*)
- [x] Dockerfile multi-stage durci conforme CIS Benchmark (non-root `UID 10001`, `no-new-privileges`, `cap_drop: [ALL]`)
- [x] Broker Mosquitto local + UI Web d'inspection MQTTX Web
- [x] Web GUI responsive avec sparklines temps réel Chart.js et WebSockets

### 🚧 Évolutions Futures Potentielles
- [ ] Connecteur AWS IoT Core / Azure IoT Hub natif (modèle documenté dans `Documentation/developer/extending_platforms.md`)
- [ ] Support des certificats mTLS X.509 clients par équipement
- [ ] Générateur de profils industriels par templates en 1 clic (HVAC, Éolienne, Ligne d'embouteillage)

---

## ⚠️ Pièges Globaux & Directives de Sécurité (Gotchas)
1. **Zéro `eval()` / `exec()`** : Toute formule mathématique doit impérativement passer par `MathSignalGenerator` pour préserver l'intégrité de la sandbox.
2. **Écriture Disque Atomique** : Toujours utiliser le pattern de fichier temporaire + `os.replace` implémenté dans `StorageRepository` pour éviter la corruption du fichier JSON en environnement conteneurisé.
3. **Isolation Réseau & Permissions CIS** : Le conteneur s'exécute avec toutes les capacités Linux révoquées (`cap_drop: [ALL]`). Ne jamais introduire de dépendance nécessitant des privilèges root ou des sockets brutes.
4. **Variables d'Environnement** :
   - `MQTT_BROKER_HOST` (défaut: `mosquitto`)
   - `MQTT_BROKER_PORT` (défaut: `1883`)
   - `MQTT_USE_TLS` (défaut: `false`)
   - `MQTT_USERNAME` / `MQTT_PASSWORD` (optionnels)
