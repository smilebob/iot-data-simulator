# Cas d'Usage Métier : Salle Blanche & CTA Stérile (ISO 5 à 8)

> **Secteur d'Activité** : Industrie & Automatismes  
> **Identifiant du Modèle** : `ind_cleanroom_cta`  
> **Protocole Recommandé** : `COAP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `shield-alert`

---

## 1. Contexte & Enjeux Métier

Environnements à contamination contrôlée (laboratoires pharmaceutiques P3/P4, salles d'opérations, photolithographie). Garantie de confinement par cascade de pression et filtration HEPA.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `ind_cleanroom_cta` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Salle Blanche & CTA Stérile (ISO 5 à 8))"]
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
| `surpression_salle_pa` | **Cascade Surpression Salle** | `telemetry` | `float` | `Pa` | 2.0s | Gaussienne [22.0, 35.0] Pa | Différentiel de pression entre sas et zone stérile |
| `renouvellement_air_volh` | **Taux de Renouvellement** | `telemetry` | `float` | `vol/h` | 5.0s | Sinusoïde [18.0, 24.0] vol/h | Débit horaire ramené au volume net de la salle |
| `comptage_particules_05` | **Particules ≥ 0.5 µm** | `telemetry` | `integer` | `part/m³` | 5.0s | Marche aléatoire [150, 850] | Compteur laser optique de particules en suspension |
| `humidite_absolue_gkg` | **Humidité Absolue Précision** | `telemetry` | `float` | `g/kg` | 5.0s | Sinusoïde [6.2, 8.5] g/kg | Évite les décharges électrostatiques sur wafers |
| `alarme_depressurisation` | **Alerte Rupture Surpression** | `attribute` | `boolean` | `-` | 30.0s | Constante (False) | Alarme sonore/visuelle enclenchée si P < 15 Pa |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "surpression_salle_pa": 24.5,
  "renouvellement_air_volh": 24.5,
  "comptage_particules_05": 42,
  "humidite_absolue_gkg": 24.5
}
```

### 4.2 Attributs d'État Partagés & Client
```json
{
  "alarme_depressurisation": false
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
> Rupture de surpression (inversion de flux d'air contaminé), percement d'un filtre terminal avec pic particulaire.

---

## 6. Recommandations de Visualisation & Tableaux de Bord

Pour restituer la valeur métier de cet équipement sur ThingsBoard, les widgets suivants sont conseillés :

- Baromètre différentiel avec seuil de sécurité critique
- Classement ISO en direct (calcul dynamique)
- Courbe de propreté particulaire
