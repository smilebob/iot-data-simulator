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

### 4.2 Attributs d'État Partagés, Client & RPC ThingsBoard

#### Topic d'Attributs Partagés (`v1/devices/me/attributes`)
Le simulateur publie et synchronise ses attributs d'état opérationnels :
```json
{
  "mode_chaud": true
}
```

#### Pilotage par RPC Bidirectionnel (`v1/devices/me/rpc/request/{id}`)
L'opérateur peut envoyer une consigne ou basculer un état depuis un widget de tableau de bord ThingsBoard 4.3 :
```json
// Requête descendante ThingsBoard -> Simulateur
{
  "method": "set_mode_chaud",
  "params": true
}

// Réponse immédiate Simulateur -> ThingsBoard (sur v1/devices/me/rpc/response/{id})
{
  "status": "SUCCESS",
  "value": true
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

Le tableau de bord officiel préconfiguré [`dashboards/thingsboard/02_tertiaire/bldg_heatpump.json`](file:///home/pierre/Projets/iot-data-simulator/dashboards/thingsboard/02_tertiaire/bldg_heatpump.json) intègre l'ensemble des composants nécessaires à l'exploitation temps réel sous ThingsBoard 4.3 :

- **Synoptique SCADA Vectoriel P&ID (Widget HTML Card)** : Schéma de principe industriel vectoriel SVG haute résolution, adapté aux écrans de contrôle (fond clair pro WCAG AA, animations CSS de flux/rotations). Les pastilles de télémétries dynamiques sont liées par clé technique exacte (`clean_key` comme `dataKey.label`) garantissant une résolution instantanée des variables `${cle:decimales}` sous ThingsBoard 4.3.
- **Commandes & Pilotage Interactif Bidirectionnel** :
  - **Interrupteur Circulaire (*Round Switch*) - Mode Fonctionnement Chaud** : Commutateur interactif (`system.control_widgets.round_switch`) lié à l'attribut partagé `mode_chaud` (`SHARED_SCOPE`). Permet à l'opérateur de basculer la commande (ON/OFF) depuis ThingsBoard. Le simulateur intercepte la requête RPC (`set_mode_chaud` ou `setValue`), applique immédiatement la consigne avec forçage manuel (`manual_override = True`), acquitte la requête sur `v1/devices/me/rpc/response/{id}` et confirme le nouvel état d'attribut sur `v1/devices/me/attributes`.
- **Jauges Analogiques (JustGage Widgets)** : Restitution visuelle instantanée des grandeurs critiques (Température Eau Départ PAC (°C), Puissance Thermique Fournie (kW), Pression Circuit Primaire (bar)) avec paliers de couleur normés (vert = nominal, ambre = vigilance, rouge = seuil critique).
- **Courbes d'Historique Télémétrique & Table d'Attributs** : Graphique temporel multi-courbes synchronisé (fenêtre glissante de 24h) et vue tabulaire des attributs client/partagés.
