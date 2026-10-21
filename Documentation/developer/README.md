# 🛠️ Documentation Développeur : IoT Data Simulator

Bienvenue dans la documentation technique destinée aux développeurs reprenant ou étendant le projet **IoT Data Simulator**.

---

## 🧭 Sommaire de la documentation développeur

1. [Architecture & Principes de Conception](architecture.md) : Découpage en couches, typage strict Pydantic v2, asynchronisme asyncio et threading.
2. [Moteur de Simulation & Évaluation Mathématique](simulation_engine.md) : Fonctionnement de la boucle de calcul, fonctions mathématiques déterministes sûres (sans `eval`), rejeu de points temporels et injection d'anomalies.
3. [Guide d'Extension : Ajouter une Plateforme IoT](extending_platforms.md) : Tutoriel pas-à-pas pour implémenter un nouveau connecteur (ex: AWS IoT, Azure IoT Hub, Kafka, etc.).
4. [API REST & Protocole WebSockets](api_and_websockets.md) : Spécification des endpoints FastAPI, format des messages de streaming télémétrique en temps réel.

---

## 🚀 Environnement de Développement Local

### Prérequis
* Python 3.11+ (ou 3.12 / 3.14)
* Environnement virtuel `venv`
* Un broker MQTT local (Mosquitto) ou un conteneur Docker

### Installation & Lancement en mode Live-Reload
```bash
cd /home/pierre/Projets/iot-data-simulator

# Création et activation de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt

# Démarrage avec hot-reload FastAPI
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📐 Conventions de Code & Standards

* **PEP 8 & Type Hints stricts** : Toutes les fonctions et méthodes publiques doivent être entièrement typées (`typing`, `pydantic`).
* **Validation des données** : Toute entrée réseau ou fichier de configuration doit obligatoirement être validée par un modèle `pydantic.BaseModel`.
* **Sécurité & CIS** :
  * **Interdiction formelle de `eval()` ou `exec()`** dans le code.
  * Pas d'accès direct au système de fichiers sans validation préalable de chemin contre les attaques *Path Traversal*.
  * Tous les logs doivent être structurés avec le logger dédié (`logging.getLogger("iot_sim....")`).
* **Gestion de la concurrence** :
  * Les accès aux dictionnaires partagés en mémoire dans le stockage (`app/storage/repository.py`) et dans le client MQTT sont protégés par des verrous `threading.Lock()`.
  * La boucle principale de simulation tourne dans une tâche `asyncio.Task` non-bloquante avec un intervalle de tick de 500ms.
