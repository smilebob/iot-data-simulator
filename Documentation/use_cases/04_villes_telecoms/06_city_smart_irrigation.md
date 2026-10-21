# Cas d'Usage Métier : Arrosage Intelligent Espaces Verts & Parcs

> **Secteur d'Activité** : Villes Durables & Télécoms  
> **Identifiant du Modèle** : `city_smart_irrigation`  
> **Protocole Recommandé** : `HTTP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `sprout`

---

## 1. Contexte & Enjeux Métier

Préservation de la ressource en eau pour parcs municipaux, terrains de sport et ronds-points. Déclenchement automatique de l'arrosage uniquement lorsque le sol en a besoin.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `city_smart_irrigation` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Arrosage Intelligent Espaces Verts & Parcs)"]
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
| `tension_matricielle_sol_cbar` | **Tension Hydrique Sol (Tensiomètre)** | `telemetry` | `float` | `cbar` | 5.0s | Dent de scie [15, 65] cbar | Indice de sécheresse racinaire du sol |
| `temp_sol_10cm` | **Température Sol (-10cm)** | `telemetry` | `float` | `°C` | 5.0s | Sinusoïde [14, 22] °C | Évite d'arroser en cas de gel matinal |
| `debit_arrosage_lmin` | **Débit Injecté Électrovanne** | `telemetry` | `float` | `l/min` | 3.0s | Carré [0, 45] l/min | Consommation d'eau instantanée |
| `conso_eau_session_m3` | **Volume Arrosage Session** | `telemetry` | `float` | `m³` | 10.0s | Rampe [0, 1.8] m³ | Comptage cumulé de la séquence |
| `vanne_secteur_ouverte` | **État Électrovanne Secteur** | `attribute` | `boolean` | `-` | 30.0s | Constante (True) | Commande asservie d'ouverture |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "tension_matricielle_sol_cbar": 24.5,
  "temp_sol_10cm": 24.5,
  "debit_arrosage_lmin": 24.5,
  "conso_eau_session_m3": 24.5
}
```

### 4.2 Attributs d'État Partagés & Client
```json
{
  "vanne_secteur_ouverte": false
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
> Fuite sur canalisation d'arrosage (débit sans coupure), blocage de l'électrovanne en position fermée.

---

## 6. Recommandations de Visualisation & Tableaux de Bord

Pour restituer la valeur métier de cet équipement sur ThingsBoard, les widgets suivants sont conseillés :

- Indice d'humidité racinaire avec seuil d'arrosage
- Bilan d'eau économisée par rapport au calendrier fixe
- Statut des électrovannes par zone
