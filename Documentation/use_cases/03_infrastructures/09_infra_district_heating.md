# 🔥 Cas d'Usage : Sous-Station Réseau de Chaleur (RCU)

> **Identifiant technique** : `infra_district_heating` | **Catégorie** : Infrastructures & Énergie | **Protocole par défaut** : MQTT / HTTP TLS

## 1. Contexte Métier & Objectif
Modélisation d'une sous-station d'échange thermique raccordée à un **Réseau de Chaleur Urbain (RCU)** : surveillance des températures primaire aller/retour, optimisation du **Delta T primaire**, calcul de la puissance thermique livrée, comptage en **MWh** et quantification du **CO2 évité vs chaudière gaz**.

## 2. Variables Simulées & Formules Causales

| Variable ID | Libellé | Nature | Unité | Mode / Formule |
| :--- | :--- | :---: | :---: | :--- |
| `temp_primaire_aller` | Température Primaire Aller | Télémétrie | `°C` | `random_walk` `[82.0; 94.0]` |
| `temp_primaire_retour` | Température Primaire Retour | Télémétrie | `°C` | `random_walk` `[54.0; 64.0]` |
| `delta_t_primaire` | Delta T Primaire | Télémétrie | `°C` | `derived`: `max(0.0, temp_primaire_aller - temp_primaire_retour)` |
| `debit_primaire_m3h` | Débit Primaire RCU | Télémétrie | `m³/h` | `sine` `[6.0; 18.0]` |
| `puissance_thermique_kw` | Puissance Thermique Livrée | Télémétrie | `kW` | `derived`: `debit_primaire_m3h * 1.163 * delta_t_primaire` |
| `energie_thermique_mwh` | Compteur Chaleur Cumulée | Télémétrie | `MWh` | `integrator` (`puissance_thermique_kw`, `multiplier=0.001`) |
| `emissions_co2_evitees_kg_h` | CO2 Évité vs Gaz | Télémétrie | `kgCO2/h` | `derived`: `puissance_thermique_kw * 0.145` |
| `vanne_regulation_active` | Vanne Régulation 2 Voies | Attribut | `bool` | `constant` (`true`, pilotable `SHARED_SCOPE`) |

## 3. Règles d'Alarmes ThingsBoard Recommandées
- **`MAJOR`** : `delta_t_primaire < 15.0` (mauvais refroidissement du retour primaire RCU).
- **`CRITICAL`** : `temp_primaire_aller < 70.0` (défaut d'alimentation réseau primaire).
