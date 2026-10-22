# ⚡ IoT Data Simulator (ThingsBoard, Home Assistant, Datacake & Multi-Platform)

[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](https://github.com/smilebob/iot-data-simulator)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![CIS Docker](https://img.shields.io/badge/security-CIS%20Benchmark%20Passed-success.svg)](Documentation/devops/docker_and_cis.md)
[![ThingsBoard](https://img.shields.io/badge/ThingsBoard-4.3%20Ready-orange.svg)](Documentation/user/thingsboard_dashboards.md)

Simulateur de données IoT industriel développé en Python (FastAPI + Paho-MQTT v2 + WebSockets + HTTP/CoAP), packagé dans une stack Docker durcie (CIS Benchmark non-root) intégrant le broker MQTT Eclipse Mosquitto.

Conçu spécialement pour réaliser des démonstrations dynamiques et réalistes sur **ThingsBoard 4.3** avec **32 synoptiques SCADA animés**, pilotage bidirectionnel interactif par **Attributs Partagés (`SHARED_SCOPE`)** et **RPC**, et compatible nativement avec **Home Assistant**, **Datacake** et tout broker MQTT distant.

---

## 🚀 Démarrage Rapide (Stack Docker)

### 1. Lancement de la stack
```bash
cd iot-data-simulator
docker compose up -d
```

### 2. Accès aux interfaces Web
* **Simulateur IoT (GUI)** : **[http://localhost:8000](http://localhost:8000)**  
  Gérez vos équipements virtuels, variables, fonctions mathématiques, scénarios et injections d'anomalies.
* **Explorateur Web MQTT (MQTTX)** : **[http://localhost:8080](http://localhost:8080)**  
  Visualisez l'arbre des topics Mosquitto, souscrivez aux topics en temps réel (`#` ou `v1/#`) et inspectez les payloads JSON envoyés par le simulateur.
  > *Pour connecter MQTTX au broker local dans l'interface web :*  
  > Protocole : `ws://` | Hôte : `localhost` | Port : `9001` | Path : `/` ou `/mqtt`

* Le broker Mosquitto écoute sur les ports `1883` (TCP standard) et `9001` (WebSockets).

### 3. Déploiement via Portainer (Clé en main & CI/CD)
La stack peut être déployée en 1 clic dans **Portainer** (CE ou BE) avec images précompilées multi-architectures (`amd64` / `arm64`) et mise à jour automatique via Webhook GitHub Actions.  
👉 Consultez le [Guide de Déploiement Portainer Pas-à-Pas](Documentation/devops/portainer_deployment.md).

---

## 🎛️ Pilotage Bidirectionnel & Tableaux de Bord SCADA ThingsBoard 4.3

* **32 Tableaux de Bord Pré-Générés** : 32 modèles prêts à l'import dans `dashboards/thingsboard/` avec schémas synoptiques P&ID / SLD vectoriels SVG animés en thème Light haute lisibilité.
* **Pilotage par Attributs Partagés (`SHARED_SCOPE`)** : Commutateurs interactifs ThingsBoard (`system.single_switch`) configurés en Action Widgets (`action: SET_ATTRIBUTE`). Exécution immédiate en base en < 50ms sans timeout 504.
* **Écoute Long-Polling HTTP** : Le simulateur écoute en continu les modifications d'attributs via `/api/v1/{token}/attributes/updates?timeout=20000`, applique les consignes avec forçage manuel en direct et synchronise l'IHM locale par WebSockets.
* **Support RPC Descendant** : Traitement synchrone des requêtes RPC (`v1/devices/me/rpc/request/+` en MQTT ou `/api/v1/{token}/rpc` en HTTP) avec acquittement instantané.

---

## 🎯 Connexion avec ThingsBoard

L'application intègre le connecteur natif multi-protocoles ThingsBoard (MQTT, HTTP REST v1, CoAP RFC 7252) :

1. **Création du device dans ThingsBoard** :
   * Rendez-vous sur votre ThingsBoard (ex: *ThingsBoard Cloud* ou instance d'entreprise).
   * Créez un nouvel équipement (Device) et copiez son **Access Token**.
2. **Dans l'interface Web du simulateur** :
   * Cliquez sur **`Paramètres Broker (icône écrou)`** ou configurez l'équipement :
     * Protocole : `MQTT` (port 1883/8883), `HTTP` (port 443 HTTPS avec Long-Polling) ou `CoAP` (UDP 5683).
     * Token : collez le Token ThingsBoard de votre équipement.
3. **Publication automatique** :
   * Les variables de type **Télémétrie** sont envoyées sur `v1/devices/me/telemetry` au format horodaté ThingsBoard :
     ```json
     {"ts": 1729506400000, "values": {"temperature": 24.5}}
     ```
   * Les variables de type **Attribut / Contrôle** sont publiées sur `v1/devices/me/attributes` et synchronisées avec `SHARED_SCOPE`.

---

## 🔌 Interopérabilité Multi-Plateformes

| Plateforme | Connecteur | Fonctionnement |
| :--- | :--- | :--- |
| **ThingsBoard** | `ThingsBoardAdapter` | Format JSON natif avec horodatage milliseconde, Device Tokens, écoute des requêtes RPC. |
| **Home Assistant** | `HomeAssistantAdapter` | **Auto-découverte (MQTT Discovery)** sur `homeassistant/sensor/.../config`. Aucun YAML nécessaire dans HA ! |
| **Datacake** | `DatacakeAdapter` | Télémétrie horodatée structurée pour tableaux de bord Datacake. |
| **Générique / Custom** | `GenericMqttAdapter` | Topics personnalisables à volonté (`usine/batA/compresseur/pression`), formats JSON ou bruts. |

---

## 🧪 Fonctions Démo & Injection d'Anomalies ("Chaos Button")

Pour rendre vos démonstrations percutantes et valider vos **règles d'alarmes (Alarm Rules ThingsBoard)**, chaque variable dispose de commandes rapides en 1 clic :
* 💥 **Pic (Spike)** : Injecte un saut brutal de valeur pour déclencher instantanément une alarme de seuil critique.
* 📈 **Dérive (Drift)** : Simule une dérive thermique ou mécanique progressive.
* ❄️ **Gel (Freeze)** : Bloque la valeur courante pour simuler un capteur grippé.
* 🔇 **Coupure (Timeout)** : Coupe l'émission de la variable pour tester la détection de perte de connectivité ThingsBoard.
* 🎛️ **Forçage Manuel** : Curseur / champ de saisie pour imposer une valeur fixe en temps réel.

---

## 📈 Modes de Génération des Données

* **Signaux Mathématiques purs** :
  * Sinusoïde, Cosinus, Triangulaire, Créneau (Square), Dent de scie, Rampe linéaire, Marche aléatoire (Random Walk), Bruit gaussien, Constante.
  * Réglages : Min, Max, Période du cycle en secondes, Offset et pourcentage de bruit aléatoire superposé.
* **Tableau de points horodatés (Rejeu temporel)** :
  * Définition d'une série de points `(offset_secondes, valeur)`.
  * Support de la répétition en boucle, interpolation linéaire, et import direct de fichiers CSV.

---

## 🔒 Conformité aux Bonnes Pratiques du CIS (Center for Internet Security)

* **CIS Docker Benchmark Rule 4.1 (Non-root user)** :
  * L'application s'exécute sous un utilisateur système non privilégié dédié (`appuser`, UID/GID 10001).
* **CIS Docker Benchmark Rule 5.16 & 5.17 (Moindre privilège)** :
  * Activation de `no-new-privileges: true` et suppression intégrale des capacités du kernel (`cap_drop: [ALL]`).
* **CIS Docker Benchmark Rule 4.3 & 4.4 (Multi-stage build & Surface minimale)** :
  * Image Python Debian épurée, compilateurs et caches purgés.
* **CIS Docker Benchmark Rule 4.6 (Healthcheck)** :
  * Sonde de santé intégrée vérifiant `/healthz`.
* **Sécurité applicative** :
  * Aucun usage de `eval()` ou code dynamique non maîtrisé.
  * En-têtes HTTP sécurisés (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).
  * Support de TLS 1.2+ obligatoire lors des connexions chiffrées MQTTS.

---

## 🛠️ Exécution en local sans Docker (Développement)

```bash
cd iot-data-simulator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📄 Licence

Ce projet est sous licence **Apache 2.0** - voir le fichier [LICENSE](LICENSE) pour plus de détails.  
Copyright (c) 2026 Pierre Roth (smilebob).

