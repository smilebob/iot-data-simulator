# Cas d'Usage Métier : Gestion d'Éclairage DALI & Détection Présence

> **Secteur d'Activité** : Tertiaire & Smart Building  
> **Identifiant du Modèle** : `bldg_dali_lighting`  
> **Protocole Recommandé** : `HTTP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `lamp`

---

## 1. Contexte & Enjeux Métier

Télégestion et régulation de l'éclairage de bureaux selon la norme DALI-2 et EN 12464-1. Économies d'énergie par gradation proportionnelle à la lumière du jour et extinction automatique.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `bldg_dali_lighting` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Gestion d'Éclairage DALI & Détection Présence)"]
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
| `eclairement_lux` | **Éclairement Mesuré Plan Travail** | `telemetry` | `float` | `lux` | 3.0s | Sinusoïde [220, 580] lux | Capteur photométrique de surface |
| `taux_presence_zone_pct` | **Taux d'Occupation de Zone** | `telemetry` | `integer` | `%` | 5.0s | Triangle [0, 100] % | Détection infrarouge passif (PIR) de mouvement |
| `gradation_dali_pct` | **Gradation Sortie Ballast DALI** | `telemetry` | `integer` | `%` | 3.0s | Sinusoïde [15, 85] % | Consigne envoyée au driver LED |
| `puissance_eclairage_w` | **Puissance Électrique Circuit** | `telemetry` | `float` | `W` | 3.0s | Sinusoïde [120, 680] W | Consommation cumulée du rail luminaires |
| `heures_fonctionnement_h` | **Heures d'Allumage Cumulées** | `telemetry` | `float` | `h` | 30.0s | Rampe [1200, 1250] h | Suivi d'usure des dalles LED |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "eclairement_lux": 24.5,
  "taux_presence_zone_pct": 42,
  "gradation_dali_pct": 42,
  "puissance_eclairage_w": 24.5,
  "heures_fonctionnement_h": 24.5
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
> Ballast DALI défaillant avec lampe hors service, détecteur PIR bloqué en état occupé.

---

## 6. Recommandations de Visualisation & Tableaux de Bord

Pour restituer la valeur métier de cet équipement sur ThingsBoard, les widgets suivants sont conseillés :

- Jauge luxmètre asservie à la consigne 500 lux
- Courbe de gradation vs Apport naturel de lumière
- Bilan kWh économisés par jour
