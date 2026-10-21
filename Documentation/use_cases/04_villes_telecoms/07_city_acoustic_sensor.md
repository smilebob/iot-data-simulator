# Cas d'Usage Métier : Sonde Acoustique & Nuisances Sonores Urbaines

> **Secteur d'Activité** : Villes Durables & Télécoms  
> **Identifiant du Modèle** : `city_acoustic_sensor`  
> **Protocole Recommandé** : `HTTP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `volume-2`

---

## 1. Contexte & Enjeux Métier

Observatoire du bruit urbain et surveillance des chantiers BTP ou zones de fret nocturne. Mesure continue des décibels et qualification des événements sonores émergents.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `city_acoustic_sensor` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Sonde Acoustique & Nuisances Sonores Urbaines)"]
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
| `niveau_laeq_dba` | **Pression Acoustique Équivalente LAeq** | `telemetry` | `float` | `dB(A)` | 2.0s | Gaussienne [48, 78] dB(A) | Bruit continu équivalent ressenti par l'oreille humaine |
| `niveau_lcpeak_dbc` | **Niveau Crête Instantané LCpeak** | `telemetry` | `float` | `dB(C)` | 1.0s | Gaussienne [65, 102] dB(C) | Bruit d'impact ou détonation |
| `batterie_solaire_v` | **Tension Batterie Solaire** | `telemetry` | `float` | `V` | 15.0s | Gaussienne [12.4, 13.8] V | Alimentation autonome par panneau solaire |
| `depassement_seuil_nocturne` | **Alerte Dépassement Seuil Bruit** | `attribute` | `boolean` | `-` | 10.0s | Constante (False) | Notification de contravention ou chantier hors limites |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "niveau_laeq_dba": 24.5,
  "niveau_lcpeak_dbc": 24.5,
  "batterie_solaire_v": 24.5
}
```

### 4.2 Attributs d'État Partagés & Client
```json
{
  "depassement_seuil_nocturne": false
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
> Dépassement prolongé du seuil légal nocturne de 65 dB(A), décharge de batterie solaire par temps couvert prolongé.

---

## 6. Recommandations de Visualisation & Tableaux de Bord

Pour restituer la valeur métier de cet équipement sur ThingsBoard, les widgets suivants sont conseillés :

- Sonomètre temps réel de rue (Vert/Orange/Rouge)
- Courbe temporelle LAeq heure par heure
- Indicateur de dépassement du seuil OMS
