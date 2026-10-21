# Cas d'Usage Métier : Contrôle d'Accès & Flux Bâtiment

> **Secteur d'Activité** : Tertiaire & Smart Building  
> **Identifiant du Modèle** : `bldg_access_flow`  
> **Protocole Recommandé** : `HTTP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `users`

---

## 1. Contexte & Enjeux Métier

Hypervision des accès, badges RFID et jauges de sécurité pour sièges sociaux et sites industriels. Permet le comptage temps réel des personnes présentes pour les plans d'évacuation pompiers.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `bldg_access_flow` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Contrôle d'Accès & Flux Bâtiment)"]
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
| `flux_entrees_min` | **Cadence Entrées Visiteurs/Employés** | `telemetry` | `integer` | `pers/min` | 5.0s | Sinusoïde [2, 35] | Passages horaires aux tripodes d'entrée |
| `flux_sorties_min` | **Cadence Sorties Tourniquets** | `telemetry` | `integer` | `pers/min` | 5.0s | Sinusoïde [1, 28] | Départ des salariés en fin de journée |
| `jauge_occupation_pct` | **Jauge d'Occupation Globale Site** | `telemetry` | `integer` | `%` | 5.0s | Sinusoïde [25, 88] % | Effectif total présent vs capacité d'accueil max |
| `tentatives_refusees_h` | **Tentatives Accès Refusées** | `telemetry` | `integer` | `rejets/h` | 10.0s | Gaussienne [0, 6] | Badges non reconnus ou zones interdites |
| `issues_secours_verrouillees` | **Issues de Secours Sous Contrôle** | `attribute` | `boolean` | `-` | 30.0s | Constante (True) | Supervision des gâches et ventouses électromagnétiques |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "flux_entrees_min": 42,
  "flux_sorties_min": 42,
  "jauge_occupation_pct": 42,
  "tentatives_refusees_h": 42
}
```

### 4.2 Attributs d'État Partagés & Client
```json
{
  "issues_secours_verrouillees": false
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
> Tentatives d'accès répétées avec badge invalide (suspicion d'intrusion), issue de secours ouverte sans alarme incendie.

---

## 6. Recommandations de Visualisation & Tableaux de Bord

Pour restituer la valeur métier de cet équipement sur ThingsBoard, les widgets suivants sont conseillés :

- Jauge temps réel du nombre d'occupants dans l'immeuble
- Flux comparatif entrées/sorties
- Statut de conformité de sécurité incendie
