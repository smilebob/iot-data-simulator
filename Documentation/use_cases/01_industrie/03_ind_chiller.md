# Cas d'Usage Métier : Groupe Froid Industriel (Chiller)

> **Secteur d'Activité** : Industrie & Automatismes  
> **Identifiant du Modèle** : `ind_chiller`  
> **Protocole Recommandé** : `HTTP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `snowflake`

---

## 1. Contexte & Enjeux Métier

Production d'eau glacée pour process industriels, thermoformage ou climatisation de grands volumes. Supervision thermodynamique du circuit frigorifique et suivi du COP.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `ind_chiller` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Groupe Froid Industriel (Chiller))"]
    TRANS["Transport (HTTP)"]
    TB["ThingsBoard IoT Gateway / Platform"]
    DB[("Base Télémétrique")]
    DASH["Tableaux de Bord & Alertes"]

    DEV -->|Télémétrie périodique| TRANS
    TRANS --> TB
    TB --> DB
    TB --> DASH
```

- **Transport standard** : `HTTP`
- **Topic MQTT / Endpoint HTTP / CoAP** :
  - **MQTT** : `v1/devices/me/telemetry` (télémétrie) et `v1/devices/me/attributes` (attributs)
  - **HTTP** : `POST /api/v1/{token}/telemetry`
  - **CoAP** : `coap://thingsboard:5683/api/v1/{token}/telemetry`

---

## 3. Dictionnaire Détaillé des Variables

| Clé (ID) | Grandeur Lisible | Type | Format | Unité | Période | Générateur / Plage | Rôle Métier & Description |
|---|---|---|---|---|---|---|---|
| `temp_eau_depart` | **Température Eau Glacée Départ** | `telemetry` | `float` | `°C` | 3.0s | Sinusoïde [6.5, 8.2] °C | Consigne régulée envoyée vers les utilités |
| `temp_eau_retour` | **Température Eau Glacée Retour** | `telemetry` | `float` | `°C` | 3.0s | Sinusoïde [11, 14] °C | Retour des boucles de process réchauffé |
| `pression_hp` | **Pression Haute Pression (HP)** | `telemetry` | `float` | `bar` | 2.0s | Triangle [14, 18.5] bar | Pression en sortie compresseur frigorifique |
| `cop_instantane` | **Coefficient de Performance (COP)** | `telemetry` | `float` | `-` | 5.0s | Gaussienne [3.2, 4.6] | Rendement énergétique calculé (Puissance froid / Puissance élec) |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "temp_eau_depart": 24.5,
  "temp_eau_retour": 24.5,
  "pression_hp": 24.5,
  "cop_instantane": 24.5
}
```

### 4.2 Attributs d'État Partagés, Client & RPC ThingsBoard

```json
{
  "modele": "Groupe Froid Industriel",
  "firmware_version": "v2.4.1",
  "statut_equipement": "OPERATIONNEL"
}
```

---

## 5. Scénarios d'Anomalies & Maintenance Prédictive

Le moteur du simulateur permet d'injecter des défaillances en direct (*Chaos Testing*) pour éprouver les règles d'alertes du serveur :

- **Pic ponctuel anormal (*Spike*)** : Simule un à-coup de pression, un choc mécanique ou une surtension transitoire.
- **Dérive continue (*Drift*)** : Simule l'encrassement progressif, le manque de lubrification ou une fuite d'étanchéité graduelle.
- **Gel de valeur (*Freeze*)** : Simule un blocage mécanique de capteur ou un convertisseur bloqué.
- **Silence radio (*Timeout*)** : Simule une perte d'alimentation du module ou une rupture de liaison télécoms.

> [!WARNING]
> **Cas de défaillance type** :  
> Chute de BP (fuite fluide frigorigène), surpression HP par encrassement du condenseur.

---

## 6. Pilotage Interactif & Tableaux de Bord ThingsBoard 4.3

Le tableau de bord officiel préconfiguré [`dashboards/thingsboard/01_industrie/ind_chiller.json`](file:///home/pierre/Projets/iot-data-simulator/dashboards/thingsboard/01_industrie/ind_chiller.json) intègre l'ensemble des composants nécessaires à l'exploitation temps réel sous ThingsBoard 4.3 :

- **Synoptique SCADA Vectoriel P&ID (Widget HTML Card)** : Schéma de principe industriel vectoriel SVG haute résolution, adapté aux écrans de contrôle (fond clair pro WCAG AA, animations CSS de flux/rotations). Les pastilles de télémétries dynamiques sont liées par clé technique exacte (`clean_key` comme `dataKey.label`) garantissant une résolution instantanée des variables `${cle:decimales}` sous ThingsBoard 4.3.
- **Mode Opérationnel Autonome & Télémétrie Pure** : Cet équipement fonctionne en régulation automatique continue. Les attributs affichés dans la table récapitulative fournissent les métadonnées d'inventaire technique (modèle constructeur, révision logicielle, protocole de liaison).
- **Jauges Analogiques (JustGage Widgets)** : Restitution visuelle instantanée des grandeurs critiques (Température Eau Glacée Départ (°C), Température Eau Glacée Retour (°C), Pression Haute Pression (HP) (bar)) avec paliers de couleur normés (vert = nominal, ambre = vigilance, rouge = seuil critique).
- **Courbes d'Historique Télémétrique & Table d'Attributs** : Graphique temporel multi-courbes synchronisé (fenêtre glissante de 24h) et vue tabulaire des attributs client/partagés.
