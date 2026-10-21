# 🧠 Mémoire Globale du Projet : IoT Data Simulator

> **Dernière MAJ** : 2026-10-21 | **Version** : 1.9.8 | **Statut** : Production / Opérationnel | **Licence** : Apache 2.0 | **Conformité** : CIS Docker Benchmark & PEP 8 | **Plateforme Cible** : ThingsBoard 4.3

---

## 🎯 Vue d'Ensemble & Objectif
- **Description** : Simulateur de données IoT industriel pour démonstrations dynamiques sur **ThingsBoard 4.3** et plateformes compatibles MQTT (**Home Assistant**, **Datacake**, etc.). Permet la génération de signaux mathématiques purs paramétrables, le rejeu de séries temporelles (points/CSV), l'injection d'anomalies en direct (*Chaos Button*) et le forçage manuel.
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
- [x] Sécurisation des Secrets & Déploiement Automatisé Portainer / CI-CD (v1.9.3) :
  - **Suppression des Tokens des Dashboards (CIS / OWASP)** : éradication complète de l'affichage des Access Tokens ThingsBoard dans les bandeaux d'en-tête HTML, les cartouches de synoptiques SCADA et les métadonnées de description des 32 tableaux de bord. Remplacement par un statut sécurisé `Authentification: Jeton Sécurisé`.
  - **Pipeline CI/CD GitHub Actions (`.github/workflows/docker-build-push.yml`)** : compilation automatisée multi-architecture (`linux/amd64` et `linux/arm64`) sur chaque push `main` et tag `v*`, et publication sur GitHub Container Registry (`ghcr.io/smilebob/iot-data-simulator:latest`).
  - **Déploiement Portainer Clé en Main** : création de `docker-compose.portainer.yml` (compatible Web Editor et Stack Git avec volumes managés), template applicatif `templates/portainer-template.json`, et support du webhook Portainer pour mise à jour continue sans interruption.
  - **Guide DevOps Portainer** : `Documentation/devops/portainer_deployment.md`.
- [x] Compatibilité ThingsBoard 4.3 & Résolution du Data Binding HTML Value Card (v1.9.4) :
  - **Moteur de rendu ThingsBoard 4.3** : Résolution des balises `${cle:format}` dans les widgets HTML Value Card (`system.cards.html_value_card`) par correspondance stricte avec le champ `label` des `dataKeys` (et non `name`).
  - **Alignement `label = clean_key`** : Définition de `label: clean_key` pour toutes les grandeurs des synoptiques SCADA, tout en maintenant les libellés complets en français sur les jauges numériques JustGage, graphiques temporels et tables d'attributs.
  - **Propriétés de synchronisation TB 4.3** : Ajout de `useDashboardTimewindow: True`, `cardCss`/`css` et `cardHtml`/`html` simultanés sur les widgets de cartes.
- [x] Pilotage Bidirectionnel & Commandes Interactives ThingsBoard 4.3 (v1.9.5) :
  - **Génération de Widgets de Contrôle Interactifs** : Ajout automatique d'interrupteurs rotatifs (`system.control_widgets.round_switch`) et formulaires de saisie (`system.input_widgets.update_multiple_attributes`) sur les 32 tableaux de bord pour piloter les 22 attributs et modes d'exploitation (ex: `mode_chaud` PAC, `etat_marche` compresseur, `registre_air_neuf` CTA, `vanne_secteur_ouverte` arrosage).
  - **Souscription Bidirectionnelle MQTT** : Écoute active de `v1/devices/me/rpc/request/+` (RPC direct) et `v1/devices/me/attributes` (Shared Attributes) dans `app/mqtt/client.py`.
  - **Traitement & Acquittement dans l'Engine** : Résolution des commandes RPC (`setValue`, `set_<key>`, `getValue`), mise à jour instantanée de la simulation, acquittement sur `v1/devices/me/rpc/response/{id}`, rétro-publication d'attribut et notification WebSocket en direct.
- [x] Documentation Intégrale & Réseau de Mémoires IA (v1.9.6) :
  - **32 Cas d'Usage Métiers Actualisés** : Mise à jour de Section 6 (pilotage interactif TB 4.3, widgets Switch/Form, synoptiques SCADA P&ID vectoriels) et Section 4.2 (RPC & Attributs partagés) pour l'intégralité des 32 modèles industriels.
  - **Répertoire Exhaustif des Commandes** : Tableau de synthèse des 18 commandes interactives dans `Documentation/user/thingsboard_dashboards.md`.
  - **Tutoriel Pas-à-Pas de Pilotage TB 4.3** : Ajout de l'Étape 6 dans `Documentation/user/thingsboard_tutorial.md`.
  - **Documentation Développeur du Moteur de Simulation** : Boucle d'interruption RPC synchrone et extension multi-plateformes dans `Documentation/developer/`.
  - **Système de Mémoire Hiérarchique IA** : Réseau structuré `PROJECT_MEMORY.md` et sous-mémoires `app/*/MEMORY.md` conforme au standard `project-memory`.
- [x] Contrôle Bidirectionnel Universel (MQTT & HTTP Long-Polling) & Persistance Renforcée (v1.9.7) :
  - **Support RPC HTTP Long-Polling ThingsBoard** : Écoute active descendante `GET /api/v1/{token}/rpc?timeout=15000` et réponse synchrone `POST /api/v1/{token}/rpc/{id}` dans `SimulationEngine` et `ThingsBoardHttpClient` pour tous les équipements ThingsBoard utilisant le protocole HTTP (notamment les instances sous Cloudflare où les ports TCP 1883/8883 sont bloqués).
  - **Correction Widgets Round Switch ThingsBoard 4.3** : Résolution du parsing JS (`parseValueFunction` traitant les objets JSON `{status, value}`), ajout de `valueKey` et rattachement à `CLIENT_SCOPE`.
  - **Persistance et Résilience Étendue** : Sauvegarde miroir `.bak` automatique, chargement résilient des équipements en cas d'erreur de schéma, backup d'urgence `.corrupted.{ts}` (zéro perte de données en cas de crash/coupure de courant).
  - **Volume Nommé Persistant & Découplage Git** : `docker-compose.yml` et `docker-compose.portainer.yml` unifiés sur le volume nommé `iot_simulator_data` (`simulator_data:/app/data`), `data/simulator_state.json` ignoré dans Git pour ne jamais être écrasé lors d'un `git pull` Portainer.
- [x] Correction Régression Boucle Moteur & Robustesse des Types (v1.9.8) :
  - **Import et Validation des Types de Protocoles** : Import explicite de `PlatformType` et `TransportProtocol` dans `app/core/engine.py` et suppression de la référence invalide à `TransportProtocol.MQTTS`/`WSS` qui bloquait le moteur avec une exception silencieuse à chaque tick.
  - **Résilience du Listener Bidirectionnel** : Sécurisation de `_sync_device_listeners` avec extraction insensible au type via `getattr(dev.protocol, "value", str(dev.protocol))` et encapsulation `try...except` isolant chaque équipement.
  - **Transmission des Paramètres Hôte/Port/TLS MQTT par Équipement** : `MqttManager.get_or_create_device_client` applique désormais les surcharges `custom_host`, `custom_port` et `use_tls` des équipements.
  - **Ajout de `save_variables` dans `StorageRepository`** : Permet la sauvegarde groupée atomique des variables lors des commandes RPC et attributs partagés.
  - **Format WebSocket Conforme pour RPC** : Encapsulation stricte sous `{"type": "telemetry", "data": {...}}` lors de l'application d'ordres de contrôle.
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
4. **Moteur ThingsBoard 4.3 (`html_value_card`)** :
   - Dans ThingsBoard 4.3, le widget `system.cards.html_value_card` remplace les balises de type `${cle:format}` **UNIQUEMENT si le `label` du dataKey correspond exactement à `cle`** (la plateforme ignore le champ `name` pour cette substitution de template).
   - Tout modèle de carte ou de synoptique vectoriel SVG dynamique DOIT avoir `dataKey.label == 'cle_technique'`.
5. **Acquittement RPC Obligatoire ThingsBoard 4.3** :
   - Pour tout équipement virtuel recevant une requête RPC sur `v1/devices/me/rpc/request/{id}`, il est impératif de répondre immédiatement sur `v1/devices/me/rpc/response/{id}` avec un statut de succès (ex: `{"status": "SUCCESS", "value": val}`) et QoS 1.
   - Sans cette réponse synchrone, ThingsBoard 4.3 lève une alerte de timeout (délai dépassé) et le widget interrupteur (*Round Switch*) se met en défaut avant de revenir automatiquement à sa position antérieure.
6. **Variables d'Environnement** :
   - `MQTT_BROKER_HOST` (défaut: `mosquitto`)
   - `MQTT_BROKER_PORT` (défaut: `1883`)
   - `MQTT_USE_TLS` (défaut: `false`)
   - `MQTT_USERNAME` / `MQTT_PASSWORD` (optionnels)

---

## 📜 Règles de Travail et de Maintenance (Consignes Utilisateur)
1. **Documentation vivante automatique** : À chaque évolution ou refonte d'une partie de l'application, mettre à jour automatiquement l'ensemble des documentations concernées (`Documentation/developer/`, `Documentation/devops/`, `Documentation/user/`) ainsi que les mémoires IA (`MEMORY.md` / `PROJECT_MEMORY.md`).
2. **Gestion Git / GitHub** : Ne JAMAIS effectuer de `git push` sur GitHub sans demande explicite de l'utilisateur. Les modifications restent locales jusqu'à instruction explicite.
3. **Exigence stricte de Cybersécurité & Stack à jour (Zero-Legacy / Zero-CVE)** : L'application et l'intégralité de sa stack (OS Debian du conteneur, runtime Python, dépendances pip, broker Mosquitto, images Docker et bibliothèques frontend) doivent TOUJOURS utiliser les versions maintenues les plus récentes exemptes de vulnérabilités connues (CVE). Tout nouvel ajout de composant doit faire l'objet d'un audit de sécurité systématique.
4. **Environnement Cible ThingsBoard 4.3** : L'instance cible de référence de l'utilisateur est **ThingsBoard 4.3**. Tout développement, export JSON de dashboard, mapping d'alias, widget ou protocole de transport doit impérativement être testé et maintenu conforme aux spécifications et particularités de cette version.
