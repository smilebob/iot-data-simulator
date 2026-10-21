# Cas d'Usage Métier : Chaudière Industrielle Vapeur & Cogénération

> **Secteur d'Activité** : Industrie & Automatismes  
> **Identifiant du Modèle** : `ind_steam_boiler`  
> **Protocole Recommandé** : `HTTP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `flame`

---

## 1. Contexte & Enjeux Métier

Centrale thermo-énergétique industrielle générant de la vapeur saturée pour les échangeurs et turbines. Optimisation du ratio combustible/air et sécurité pression cuve.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `ind_steam_boiler` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Chaudière Industrielle Vapeur & Cogénération)"]
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
| `pression_vapeur_bar` | **Pression Vapeur Vive** | `telemetry` | `float` | `bar` | 3.0s | Dent de scie [12.5, 16.8] bar | Pression dans le ballon de chaudière |
| `debit_vapeur_th` | **Débit Massique Vapeur** | `telemetry` | `float` | `t/h` | 4.0s | Gaussienne [4.5, 14.0] t/h | Débit vapeur distribué aux usagers du site |
| `temp_fumees` | **Température des Fumées** | `telemetry` | `float` | `°C` | 5.0s | Sinusoïde [145.0, 185.0] °C | Indicateur d'encrassement des faisceaux tubulaires |
| `rendement_combustion_pct` | **Rendement de Combustion** | `telemetry` | `float` | `%` | 10.0s | Gaussienne [89.0, 94.5] % | Performance thermodynamique du brûleur |
| `taux_o2_residuel` | **Teneur O₂ Résiduel** | `telemetry` | `float` | `%` | 5.0s | Gaussienne [2.8, 4.5] % | Qualité du mélange comburant/combustible |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "pression_vapeur_bar": 24.5,
  "debit_vapeur_th": 24.5,
  "temp_fumees": 24.5,
  "rendement_combustion_pct": 24.5,
  "taux_o2_residuel": 24.5
}
```

### 4.2 Attributs d'État Partagés, Client & RPC ThingsBoard

```json
{
  "modele": "Chaudière Industrielle Vapeur",
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
> Perte de tirage entraînant une hausse brutale des fumées, emballement de pression avec déclenchement de soupape.

---

## 6. Pilotage Interactif & Tableaux de Bord ThingsBoard 4.3

Le tableau de bord officiel préconfiguré [`dashboards/thingsboard/01_industrie/ind_steam_boiler.json`](file:///home/pierre/Projets/iot-data-simulator/dashboards/thingsboard/01_industrie/ind_steam_boiler.json) intègre l'ensemble des composants nécessaires à l'exploitation temps réel sous ThingsBoard 4.3 :

- **Synoptique SCADA Vectoriel P&ID (Widget HTML Card)** : Schéma de principe industriel vectoriel SVG haute résolution, adapté aux écrans de contrôle (fond clair pro WCAG AA, animations CSS de flux/rotations). Les pastilles de télémétries dynamiques sont liées par clé technique exacte (`clean_key` comme `dataKey.label`) garantissant une résolution instantanée des variables `${cle:decimales}` sous ThingsBoard 4.3.
- **Mode Opérationnel Autonome & Télémétrie Pure** : Cet équipement fonctionne en régulation automatique continue. Les attributs affichés dans la table récapitulative fournissent les métadonnées d'inventaire technique (modèle constructeur, révision logicielle, protocole de liaison).
- **Jauges Analogiques (JustGage Widgets)** : Restitution visuelle instantanée des grandeurs critiques (Pression Vapeur Vive (bar), Débit Massique Vapeur (t/h), Température des Fumées (°C)) avec paliers de couleur normés (vert = nominal, ambre = vigilance, rouge = seuil critique).
- **Courbes d'Historique Télémétrique & Table d'Attributs** : Graphique temporel multi-courbes synchronisé (fenêtre glissante de 24h) et vue tabulaire des attributs client/partagés.
