# Cas d'Usage Métier : Pompe à Chaleur Réversible (PAC)

> **Secteur d'Activité** : Tertiaire & Smart Building  
> **Identifiant du Modèle** : `bldg_heatpump`  
> **Protocole Recommandé** : `HTTP` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `flame`

---

## 1. Contexte & Enjeux Métier

Système thermodynamique air/eau ou eau/eau pour chauffage hivernal et rafraîchissement estival. Régulation inverter et surveillance pression circuit primaire.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `bldg_heatpump` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Pompe à Chaleur Réversible (PAC))"]
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
| `temp_depart_eau` | **Température Eau Départ PAC** | `telemetry` | `float` | `°C` | 4.0s | Sinusoïde [42, 48] °C | Eau chaude envoyée vers ventilo-convecteurs |
| `puissance_thermique_kw` | **Puissance Thermique Fournie** | `telemetry` | `float` | `kW` | 3.0s | Sinusoïde [15, 55] kW | Énergie calorifique délivrée par la pompe |
| `pression_circuit` | **Pression Circuit Primaire** | `telemetry` | `float` | `bar` | 5.0s | Gaussienne [1.8, 2.3] bar | Pression statique du circuit de chauffage |
| `mode_chaud` | **Mode Fonctionnement Chaud** | `attribute` | `boolean` | `-` | 60.0s | Constante (True) | Régime saisonnier (Hiver: True / Été: False) |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "temp_depart_eau": 24.5,
  "puissance_thermique_kw": 24.5,
  "pression_circuit": 24.5
}
```

### 4.2 Attributs d'État Partagés & Client
```json
{
  "mode_chaud": false
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
> Perte de pression circuit primaire (fuite réseau radiateurs), givrage de l'échangeur extérieur en hiver.

---

## 6. Pilotage Interactif & Tableaux de Bord ThingsBoard 4.3

Le tableau de bord officiel préconfiguré [`dashboards/thingsboard/02_tertiaire/bldg_heatpump.json`](file:///home/pierre/Projets/iot-data-simulator/dashboards/thingsboard/02_tertiaire/bldg_heatpump.json) intègre :

- **Synoptique SCADA Vectoriel P&ID** : Circuit frigorifique R32 avec compresseur Scroll inverter, vanne 4 voies d'inversion, échangeur à plaques hydro et ventilateur hélicoïde animé.
- **Interrupteur de Pilotage Interactif (*Round Switch*)** : Widget dédié permettant à l'opérateur de basculer en direct le `mode_chaud` (Chaud = ON / Froid = OFF) depuis ThingsBoard 4.3, avec prise en compte instantanée par le simulateur (RPC bidirectionnel).
- **Jauges JustGage** : Température de départ eau (42-48°C), puissance thermique (15-55 kW) et pression circuit primaire (1.8-2.3 bar).
- **Courbes Temps Réel & Table d'Attributs** : Historique glissant et état opérationnel de la PAC.
