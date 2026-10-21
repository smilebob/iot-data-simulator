# Cas d'Usage Métier : Onduleur Solaire Photovoltaïque

> **Secteur d'Activité** : Infrastructures & Énergie  
> **Identifiant du Modèle** : `infra_solar_pv`  
> **Protocole Recommandé** : `HTTP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `sun`

---

## 1. Contexte & Enjeux Métier

Centrale solaire en toiture ou au sol. Conversion de la puissance continue (DC) des panneaux en courant alternatif (AC) synchronisé réseau, avec calcul du rendement MPPT.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `infra_solar_pv` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Onduleur Solaire Photovoltaïque)"]
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
| `puissance_injection_kw` | **Puissance AC Injectée** | `telemetry` | `float` | `kW` | 2.0s | Sinusoïde [0, 125] kW | Puissance réinjectée sur le réseau public |
| `ensoleillement` | **Irradiation Pyranomètre** | `telemetry` | `float` | `W/m²` | 3.0s | Sinusoïde [50, 980] W/m² | Flux solaire incident reçu par unité de surface |
| `tension_dc_string` | **Tension DC Chaîne PV** | `telemetry` | `float` | `V` | 2.0s | Gaussienne [580, 740] V | Tension continue aux bornes du traqueur MPPT |
| `rendement_onduleur` | **Rendement de Conversion** | `telemetry` | `float` | `%` | 5.0s | Gaussienne [96.5, 98.8] % | Rendement de l'électronique de puissance IGBT |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "puissance_injection_kw": 24.5,
  "ensoleillement": 24.5,
  "tension_dc_string": 24.5,
  "rendement_onduleur": 24.5
}
```

### 4.2 Attributs d'État Partagés & Client
```json
{}
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
> Baisse anormale de puissance DC (ombrage, salissure de panneaux, rupture de fusible string).

---

## 6. Recommandations de Visualisation & Tableaux de Bord

Pour restituer la valeur métier de cet équipement sur ThingsBoard, les widgets suivants sont conseillés :

- Courbe de production journalière en cloche
- Rendement instantané MPPT
- Indicateur d'émissions de CO2 évitées
