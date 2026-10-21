# Cas d'Usage Métier : Conteneur Déchets & Point d'Apport Volontaire (PAV)

> **Secteur d'Activité** : Villes Durables & Télécoms  
> **Identifiant du Modèle** : `city_waste_bin`  
> **Protocole Recommandé** : `COAP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `trash-2`

---

## 1. Contexte & Enjeux Métier

Conteneurs enterrés ou semi-enterrés de tri sélectif (verre, carton, ordures ménagères). Réduction de 30% des tournées des camions bennes grâce à la collecte à la demande.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `city_waste_bin` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Conteneur Déchets & Point d'Apport Volontaire (PAV))"]
    TRANS["Transport (COAP)"]
    TB["ThingsBoard IoT Gateway / Platform"]
    DB[("Base Télémétrique")]
    DASH["Tableaux de Bord & Alertes"]

    DEV -->|Télémétrie périodique| TRANS
    TRANS --> TB
    TB --> DB
    TB --> DASH
```

- **Transport standard** : `COAP`
- **Topic MQTT / Endpoint HTTP / CoAP** :
  - **MQTT** : `v1/devices/me/telemetry` (télémétrie) et `v1/devices/me/attributes` (attributs)
  - **HTTP** : `POST /api/v1/{token}/telemetry`
  - **CoAP** : `coap://thingsboard:5683/api/v1/{token}/telemetry`

---

## 3. Dictionnaire Détaillé des Variables

| Clé (ID) | Grandeur Lisible | Type | Format | Unité | Période | Générateur / Plage | Rôle Métier & Description |
|---|---|---|---|---|---|---|---|
| `taux_remplissage_pct` | **Taux Remplissage Cuve** | `telemetry` | `integer` | `%` | 10.0s | Rampe [15, 98] % | Sonde ultrason de hauteur de déchets |
| `temp_interne_cuve` | **Température Interne Cuve** | `telemetry` | `float` | `°C` | 10.0s | Sinusoïde [12, 28] °C | Détection précoce d'échauffement ou feu |
| `batterie_autonomie_pct` | **Niveau Batterie Capteur** | `telemetry` | `integer` | `%` | 60.0s | Rampe [70, 99] % | Pile lithium longue durée (5 ans) |
| `alerte_incendie` | **Détection Fumée / Feu Bac** | `attribute` | `boolean` | `-` | 30.0s | Constante (False) | Alerte prioritaire vers le centre de secours |
| `alerte_basculement` | **Capteur Choc / Basculement** | `attribute` | `boolean` | `-` | 30.0s | Constante (False) | Choc véhicule ou vandalisme |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "taux_remplissage_pct": 42,
  "temp_interne_cuve": 24.5,
  "batterie_autonomie_pct": 42
}
```

### 4.2 Attributs d'État Partagés & Client
```json
{
  "alerte_incendie": false,
  "alerte_basculement": false
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
> Dépassement du seuil de remplissage de 90%, départ de feu de détritus dans le bac détecté par la sonde thermique.

---

## 6. Recommandations de Visualisation & Tableaux de Bord

Pour restituer la valeur métier de cet équipement sur ThingsBoard, les widgets suivants sont conseillés :

- Carte des conteneurs avec code couleur de remplissage
- Algorithme d'optimisation d'itinéraire de ramassage
- Indicateur d'autonomie des batteries
