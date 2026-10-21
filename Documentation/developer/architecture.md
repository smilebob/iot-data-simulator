# 🏛️ Architecture Logicielle & Design Patterns

## Vue d'ensemble du Système

L'application **IoT Data Simulator** est articulée autour d'une architecture modulaire et découplée :

```
┌────────────────────────────────────────────────────────┐
│                   Couche Présentation                   │
│      app/static/ (HTML5, Tailwind CSS, Chart.js)       │
└───────────────────────────▲────────────────────────────┘
                            │ REST & WebSockets
┌───────────────────────────▼────────────────────────────┐
│                    Couche Contrôleur                    │
│   app/api/ (FastAPI Routes, WebSocket Manager, RBAC)   │
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  Couche Moteur Métier                   │
│     app/core/ (SimulationEngine, Generators, Replay,   │
│     Physics, EquipmentCatalog, SCADA Dashboard Gen)    │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
              ▼                            ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  Couche Plateformes IoT  │  │ Couche Transports Réseau │
│  app/platforms/          │  │ app/transports/          │
│  (ThingsBoard, HA, ...)  │  │ (MQTT, HTTP v1, CoAP UDP)│
└──────────────────────────┘  └──────────────────────────┘
              │                            │
              └─────────────┬──────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Couche Persistance                    │
│   app/storage/ (StorageRepository, JSON atomique)      │
└────────────────────────────────────────────────────────┘
```

---

## Les Composants Clés

### 1. `app/models/` (Schémas de Données & Typage)
Utilise **Pydantic v2** pour valider et sérialiser chaque entité :
* `VariableConfig` : Représente une grandeur physique ou consigne. Contient le type (`telemetry` ou `attribute`), le typage interne (`float`, `int`, `boolean`, `string`), le mode de simulation, et les paramètres mathématiques associés.
* `DeviceConfig` : Représente un équipement virtuel regroupant des variables, avec son token d'authentification plateforme.
* `BrokerConfig` : Paramètres de connexion MQTT (hôte, port, TLS, identifiants).

### 2. `app/core/` (Moteur de Simulation & Évaluateurs)
* `SimulationEngine` : Orchestrateur central asynchrone (`asyncio`). Toutes les 500ms, il passe en revue les variables actives, calcule leur valeur à l'instant $t$, vérifie si le délai de publication est atteint, formate le message via l'adapter adapté, publie sur MQTT et diffuse sur WebSocket.
* `MathSignalGenerator` : Table de calcul déterministe pure (aucun appel `eval()`).
* `ReplayEngine` : Gère le rejeu de séries temporelles avec calcul de phase cyclique, interpolation linéaire et accélération de vitesse.

### 3. `app/platforms/` (Pattern Stratégie / Adaptateur)
Tous les connecteurs dérivent de la classe abstraite `BasePlatformAdapter` :
```python
class BasePlatformAdapter(ABC):
    @abstractmethod
    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        ...

    @abstractmethod
    def format_message(self, device, variable, value, timestamp_ms) -> Tuple[str, str]:
        ...
```
Cette abstraction permet d'ajouter n'importe quelle plateforme cible sans jamais modifier le moteur de simulation ou le client MQTT.

### 4. `app/mqtt/` (Gestionnaire Réseau Résilient)
* `MqttConnection` : Encapsule un client `paho.mqtt.client` avec reconnexion automatique exponentielle, sécurisation TLS 1.2+ stricte et publication thread-safe.
* `MqttManager` : Gère dynamiquement le client MQTT global ainsi que les clients dédiés par équipement si chaque device ThingsBoard possède son propre token d'authentification.

### 5. `app/storage/` (Persistance Atomique)
* `StorageRepository` : Sauvegarde sous format JSON avec écriture atomique (écriture dans un fichier `.tmp` suivie d'un `os.replace` atomique sur le système de fichiers Linux) évitant toute corruption en cas d'arrêt brutal du conteneur.

### 6. `app/transports/` (Aiguillage Multi-Protocoles)
* `TransportManager` : Route chaque trame télémétrique selon le protocole de l'équipement :
  * **MQTT** : via `MqttManager` (TCP standard port 1883/8883 ou WebSockets port 443).
  * **HTTP REST** : via `ThingsBoardHttpClient` (API v1 `POST /api/v1/{token}/telemetry`, HTTPS port 443 natif pour traverser les proxys Cloudflare).
  * **CoAP** : via `ThingsBoardCoapClient` (RFC 7252 sur UDP 5683 avec options `Uri-Path` et `Content-Format: application/json`).

### 7. `app/core/` (Sous-système Tableaux de Bord SCADA & Catalogue)
* `dashboard_generator.py` : Générateur dynamique de fichiers JSON ThingsBoard v3.x avec alias d'entité `singleEntity`, thème Light haute lisibilité (fond `#F1F5F9`, cartes `#FFFFFF`, WCAG AA) et widgets normalisés (`system.cards.html_value_card`, `system.digital_gauges.simple_gauge_justgage`, `system.charts.basic_timeseries`, `system.cards.entities_table`).
* `scada_synoptics.py` : Moteur de rendu vectoriel SVG fournissant **32 synoptiques SCADA industriels dédiés** (P&ID, SLD, GTB) avec tuyauteries animées, rotors en mouvement et souscription temps réel aux grandeurs via `${key}`.
* `equipment_catalog.py` : Référentiel des 32 presets métiers (Industrie, Tertiaire, Infrastructures, Villes & Télécoms).
* `physics.py` : Résolution causale multi-passes des variables dérivées et intégrateurs continus temporels (énergie en kWh/MWh).

### 8. `app/auth/` (Contrôle d'Accès RBAC & Sécurité CIS)
* `service.py` & `models.py` : Gestion des rôles `ADMIN`, `OPERATOR`, `VIEWER`, hachage cryptographique Scrypt RFC 7914, sessions par cookies signés JWT HttpOnly et ségrégation stricte des secrets dans `data/users.json` (droits `0600`).
