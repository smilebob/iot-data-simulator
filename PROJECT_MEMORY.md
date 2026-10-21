# 🧠 Mémoire Globale du Projet : IoT Data Simulator

> **Dernière MAJ** : 2026-10-21 | **Version** : 1.7.0 | **Statut** : Production / Opérationnel | **Licence** : Apache 2.0 | **Conformité** : CIS Docker Benchmark & PEP 8

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
| `app/transports/` | Gestionnaire multi-protocoles (MQTT, HTTP REST v1, CoAP RFC 7252) | [app/transports/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/transports/MEMORY.md) |
| `app/platforms/` | Adaptateurs IoT (ThingsBoard, Home Assistant, Datacake, Generic) | [app/platforms/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/platforms/MEMORY.md) |
| `app/mqtt/` | Client Paho-MQTT v2, reconnexion, sessions TLS 1.2+ et multi-tokens | [app/mqtt/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/mqtt/MEMORY.md) |
| `app/storage/` | Persistance atomique JSON (`data/simulator_state.json`) et bootstrapping démo | [app/storage/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/storage/MEMORY.md) |
| `app/api/` | Routes FastAPI REST, WebSocket streaming (`/ws/live`), import CSV | [app/api/MEMORY.md](file:///home/pierre/Projets/iot-data-simulator/app/api/MEMORY.md) |
| `Documentation/` | Documentation exhaustive structurée (Développeur, DevOps, Utilisateur) | [Documentation/](file:///home/pierre/Projets/iot-data-simulator/Documentation/) |
| `Documentation/use_cases/` | Fiches techniques complètes des 32 cas d'usage métiers pré-configurés | [Documentation/use_cases/](file:///home/pierre/Projets/iot-data-simulator/Documentation/use_cases/) |

---

## 📌 État Actuel & Feuille de Route
### ✅ Implémenté & Validé
- [x] Charte Graphique Industrielle (Rouge Technique `#E2001A`, thème sombre épuré sans logos d'entreprise)
- [x] Regroupement clair et structuré des variables par équipement (sections dédiées)
- [x] Fonctions complètes d'édition et de suppression d'équipements avec nettoyage en cascade
- [x] Architecture modulaire par Adapters (`BasePlatformAdapter`)
- [x] Multi-Protocoles ThingsBoard : support complet de **MQTT**, **HTTP REST v1** (port 443 HTTPS), et **CoAP** (RFC 7252 sur UDP 5683) avec sélecteur par équipement
- [x] Diagnostic et test de communication en direct (bouton Tester pour chaque équipement et dans le modal de création/édition)
- [x] Support des transports MQTT TCP standard et WebSockets (WSS / port 443) pour contourner les proxys CDN Cloudflare
- [x] Console de Logs & Diagnostics temps réel (tampon circulaire 200 entrées, streaming WebSocket, filtrage par niveau et badge d'erreurs)
- [x] Outil de diagnostic direct de connectivité broker MQTT (`POST /api/broker/test`) avec détection reverse proxy CDN Cloudflare et calcul de latence
- [x] Moteur mathématique déterministe (Sinus, Cosinus, Triangle, Carré, Dent de scie, Rampe, Random walk, Gaussien, Constante) sans `eval()`
- [x] Rejeu temporel avec interpolation linéaire et upload CSV
- [x] Injection de pannes à la volée (*Spike*, *Drift*, *Freeze*, *Timeout*)
- [x] Dockerfile multi-stage durci conforme CIS Benchmark (non-root `UID 10001`, `no-new-privileges`, `cap_drop: [ALL]`, `apt-get upgrade` de sécurité)
- [x] Dépendances durcies contre les CVE récentes (Jinja2 >= 3.1.5, python-multipart >= 0.0.31, FastAPI >= 0.115.6)
- [x] Broker Mosquitto local (image `eclipse-mosquitto:2`) + UI Web d'inspection MQTTX Web
- [x] Licence Apache 2.0 (fichier LICENSE et notices légales)
- [x] Numérotation de version automatique et affichage discret en bas de page (v1.9.0)
- [x] Système d'Authentification & Gestion des Utilisateurs RBAC (Admin, Opérateur, Observateur)
- [x] Protection des secrets selon les directives du CIS Benchmark (hachage Scrypt RFC 7914, JWT HttpOnly, droits 0600)
- [x] Compte administrateur par défaut initialisé au boot (`admin` / `Admin_123456!`) avec invite de modification
- [x] IHM de gestion des comptes, réinitialisation et changement autonome de mot de passe
- [x] Catalogue de 32 Modèles d'Équipements Métiers (8 par secteur : Industrie, Tertiaire, Infrastructures, Villes & Télécoms) avec instanciation en 1 clic dans l'IHM (`/api/presets`)
- [x] Dossier documentaire dédié `Documentation/use_cases/` avec 32 fiches techniques détaillées (architectures, variables, payloads ThingsBoard, règles d'alarmes)
- [x] Moteur de Dépendance Physique & Variables Dérivées (`SimMode.DERIVED`, `SimMode.INTEGRATOR`) : évaluation causale en 3 passes, analyseur AST sécurisé sans `eval()`, intégrateurs d'énergie continus (kWh, MWh, m³) et rétro-application aux 32 presets métiers
- [x] Guide d'architecture du moteur physique : `Documentation/developer/physics_and_dependencies.md`
- [x] Configuration de l'intervalle d'envoi (`publish_interval`) au niveau équipement avec écrasement en cascade sur toutes les grandeurs associées, tout en préservant la possibilité de régler des cadences individuelles par variable (v1.8.0)
- [x] Tableaux de Bord SCADA ThingsBoard (v1.9.0) : Intégration de schémas synoptiques professionnels conformes aux règles métiers (P&ID tuyauterie/instrumentation ISO 10628, schémas unifilaires électriques SLD IEC 60617, synoptiques aérauliques GTB/CVC DIN 1946) avec animations de fluides, rotors en mouvement, tags de mesure en temps réel, jauges de process et téléchargement direct en 1 clic avec Token ThingsBoard préconfiguré pour chaque équipement et cas d'usage.
- [x] Correctifs Robustesse Communication & Dashboards Plug-and-Play (v1.9.1) : 
  - Connectivité immédiate dès l'instanciation de presets : sélection par défaut HTTP REST (port 443 HTTPS) avec `use_tls=True`, fallback TLS intelligent pour hôtes distants, et ping de validation instantané au moment de l'instanciation.
  - Résolution des erreurs d'importation ThingsBoard : FQN systèmes conformes (`system.digital_gauges.simple_gauge_justgage`, `system.charts.basic_timeseries`, `system.cards.entities_table`, `system.cards.html_card`), alias d'entité `singleEntity` avec déclenchement automatique de l'assistant de mapping ThingsBoard à l'import, synchronisation des clés de télémétrie courtes sans préfixe polluant (`debit_vehicules`, etc.), et synoptique SCADA dédié au comptage routier et mobilités douces.
- [x] Refonte Graphique Light Theme & 32 Synoptiques SCADA Dédiés (v1.9.2) :
  - **Thème Light Haute Lisibilité (WCAG AA)** : refonte intégrale de l'apparence des 32 tableaux de bord ThingsBoard avec fond `#F1F5F9`, widgets `#FFFFFF`, bordures nettes `#CBD5E1`, textes sombres à fort contraste `#0F172A` / `#475569`, et accent technique rouge `#E2001A` sans logo ni marque déposée.
  - **32 Schémas Synoptiques Vectoriels Dédiés** : fin des synoptiques génériques de secours ; création de représentations vectorielles P&ID / SLD / GTB spécifiques pour les 32 cas d'usage métiers (Centrale d'air comprimé, Broche d'usinage, Chiller, Convoyeur robotisé, Chambre froide négative, Chaudière vapeur, Salle blanche ISO, Four multi-zones, CTA, TGBT, QAI, PAC, SSI incendie, DALI, Compteur thermique, Contrôle d'accès, Transfo HTA, Solaire PV, Borne IRVE, Poste de relevage, Éolienne, BESS stockage, Aiguillage ferroviaire, STEP bassin d'aération, Éclairage public, Station météo, Shelter télécoms, Trafic & mobilités, Conteneur déchets, Arrosage intelligent, Sonde acoustique, Ouvrage d'art SHM).
  - **Cohérence Métier Garantie** : Correction du synoptique de la pompe à chaleur (`bldg_heatpump`) qui affichait à tort une fosse de relevage d'eaux usées (désormais dotée d'un synoptique thermodynamique complet : compresseur scroll inverter, vanne 4 voies d'inversion, échangeur à plaques hydro, batterie extérieure et ventilateur). Maintien strict du synoptique de relevage d'assainissement dédié pour `infra_water_pump`.
  - **Zéro Balise Orpheline** : Alignement exact de 100% des tags de mesure dynamiques `${cle}` avec les noms de variables télémétriques de chaque équipement.
- [x] Guide utilisateur d'importation ThingsBoard SCADA : `Documentation/user/thingsboard_dashboards.md`

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

---

## 📜 Règles de Travail et de Maintenance (Consignes Utilisateur)
1. **Documentation vivante automatique** : À chaque évolution ou refonte d'une partie de l'application, mettre à jour automatiquement l'ensemble des documentations concernées (`Documentation/developer/`, `Documentation/devops/`, `Documentation/user/`) ainsi que les mémoires IA (`MEMORY.md` / `PROJECT_MEMORY.md`).
2. **Gestion Git / GitHub** : Ne JAMAIS effectuer de `git push` sur GitHub sans demande explicite de l'utilisateur. Les modifications restent locales jusqu'à instruction explicite.
3. **Exigence stricte de Cybersécurité & Stack à jour (Zero-Legacy / Zero-CVE)** : L'application et l'intégralité de sa stack (OS Debian du conteneur, runtime Python, dépendances pip, broker Mosquitto, images Docker et bibliothèques frontend) doivent TOUJOURS utiliser les versions maintenues les plus récentes exemptes de vulnérabilités connues (CVE). Tout nouvel ajout de composant doit faire l'objet d'un audit de sécurité systématique.
