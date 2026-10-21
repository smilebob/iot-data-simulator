# Cas d'Usage Métier : Centrale Sécurité Incendie (SSI) & Désenfumage

> **Secteur d'Activité** : Tertiaire & Smart Building  
> **Identifiant du Modèle** : `bldg_fire_ssi`  
> **Protocole Recommandé** : `MQTT` | **Plateforme Cible** : ThingsBoard, Multi-Plateformes  
> **Icône Applicative** : `bell-ring`

---

## 1. Contexte & Enjeux Métier

Équipement d'Alarme et Système de Mise en Sécurité Incendie (SMSI) conforme NF S 61-931. Assure le désenfumage mécanique, le compartimentage coupe-feu et l'évacuation des personnes.

### Objectifs Opérationnels :
- Acquisition en temps réel des grandeurs physiques critiques sans latence.
- Surveillance continue et détection précoce des dérives ou pannes potentielles.
- Optimisation des consommations d'énergie et réduction des coûts d'exploitation et de maintenance.
- Traçabilité réglementaire et conformité aux standards de sécurité industrielle.

---

## 2. Architecture & Topologie de Communication

L'équipement virtuel `bldg_fire_ssi` s'interface directement avec ThingsBoard ou un broker intermédiaire selon les modalités suivantes :

```mermaid
flowchart LR
    DEV["Équipement Virtuel\n(Centrale Sécurité Incendie (SSI) & Désenfumage)"]
    TRANS["Transport (MQTT)"]
    TB["ThingsBoard IoT Gateway / Platform"]
    DB[("Base Télémétrique")]
    DASH["Tableaux de Bord & Alertes"]

    DEV -->|Télémétrie périodique| TRANS
    TRANS --> TB
    TB --> DB
    TB --> DASH
```

- **Transport standard** : `MQTT`
- **Topic MQTT / Endpoint HTTP / CoAP** :
  - **MQTT** : `v1/devices/me/telemetry` (télémétrie) et `v1/devices/me/attributes` (attributs)
  - **HTTP** : `POST /api/v1/{token}/telemetry`
  - **CoAP** : `coap://thingsboard:5683/api/v1/{token}/telemetry`

---

## 3. Dictionnaire Détaillé des Variables

| Clé (ID) | Grandeur Lisible | Type | Format | Unité | Période | Générateur / Plage | Rôle Métier & Description |
|---|---|---|---|---|---|---|---|
| `opacite_fumee_obsm` | **Opacité Détection Fumée** | `telemetry` | `float` | `obs/m` | 2.0s | Gaussienne [0.01, 0.08] obs/m | Mesure optique infrarouge d'obscurcissement |
| `debit_desenfumage_m3h` | **Débit Extracteur Désenfumage** | `telemetry` | `float` | `m³/h` | 5.0s | Carré [0, 12000] m³/h | Extraction d'air chaud et de fumées toxiques |
| `tension_alim_secours` | **Tension Alimentation Secourue (AES)** | `telemetry` | `float` | `V` | 10.0s | Gaussienne [26.8, 27.5] V | Supervision des batteries stationnaires 24V |
| `declencheur_manuel` | **Déclencheur Manuel Enclenché** | `attribute` | `boolean` | `-` | 30.0s | Constante (False) | Statut des boîtiers bris de glace |
| `statut_clapets_coupe_feu` | **Statut Clapets Coupe-Feu** | `attribute` | `string` | `-` | 60.0s | Constante ('ARMED_OPEN') | Position de sécurité des clapets de compartimentage |

---

## 4. Schémas des Payloads JSON (ThingsBoard)

### 4.1 Télémétrie Périodique
```json
{
  "opacite_fumee_obsm": 24.5,
  "debit_desenfumage_m3h": 24.5,
  "tension_alim_secours": 24.5
}
```

### 4.2 Attributs d'État Partagés, Client & RPC ThingsBoard

#### Topic d'Attributs Partagés (`v1/devices/me/attributes`)
Le simulateur publie et synchronise ses attributs d'état opérationnels :
```json
{
  "declencheur_manuel": true,
  "statut_clapets_coupe_feu": "VALEUR"
}
```

#### Pilotage par RPC Bidirectionnel (`v1/devices/me/rpc/request/{id}`)
L'opérateur peut envoyer une consigne ou basculer un état depuis un widget de tableau de bord ThingsBoard 4.3 :
```json
// Requête descendante ThingsBoard -> Simulateur
{
  "method": "set_declencheur_manuel",
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
> Déclenchement intempestif d'un détecteur optique dans un local technique, rupture de liaison avec un clapet coupe-feu.

---

## 6. Pilotage Interactif & Tableaux de Bord ThingsBoard 4.3

Le tableau de bord officiel préconfiguré [`dashboards/thingsboard/02_tertiaire/bldg_fire_ssi.json`](file:///home/pierre/Projets/iot-data-simulator/dashboards/thingsboard/02_tertiaire/bldg_fire_ssi.json) intègre l'ensemble des composants nécessaires à l'exploitation temps réel sous ThingsBoard 4.3 :

- **Synoptique SCADA Vectoriel P&ID (Widget HTML Card)** : Schéma de principe industriel vectoriel SVG haute résolution, adapté aux écrans de contrôle (fond clair pro WCAG AA, animations CSS de flux/rotations). Les pastilles de télémétries dynamiques sont liées par clé technique exacte (`clean_key` comme `dataKey.label`) garantissant une résolution instantanée des variables `${cle:decimales}` sous ThingsBoard 4.3.
- **Commandes & Pilotage Interactif Bidirectionnel** :
  - **Interrupteur Circulaire (*Round Switch*) - Déclencheur Manuel Enclenché** : Commutateur interactif (`system.control_widgets.round_switch`) lié à l'attribut partagé `declencheur_manuel` (`SHARED_SCOPE`). Permet à l'opérateur de basculer la commande (ON/OFF) depuis ThingsBoard. Le simulateur intercepte la requête RPC (`set_declencheur_manuel` ou `setValue`), applique immédiatement la consigne avec forçage manuel (`manual_override = True`), acquitte la requête sur `v1/devices/me/rpc/response/{id}` et confirme le nouvel état d'attribut sur `v1/devices/me/attributes`.
  - **Formulaire de Consigne (*Update Multiple Attributes*) - Statut Clapets Coupe-Feu** : Widget de saisie interactif (`system.input_widgets.update_multiple_attributes`) permettant de renseigner la consigne `statut_clapets_coupe_feu` (string). Les modifications sont instantanément répercutées dans la simulation physique via l'abonnement aux attributs partagés.
- **Jauges Analogiques (JustGage Widgets)** : Restitution visuelle instantanée des grandeurs critiques (Opacité Détection Fumée (obs/m), Débit Extracteur Désenfumage (m³/h), Tension Alimentation Secourue (AES) (V)) avec paliers de couleur normés (vert = nominal, ambre = vigilance, rouge = seuil critique).
- **Courbes d'Historique Télémétrique & Table d'Attributs** : Graphique temporel multi-courbes synchronisé (fenêtre glissante de 24h) et vue tabulaire des attributs client/partagés.
