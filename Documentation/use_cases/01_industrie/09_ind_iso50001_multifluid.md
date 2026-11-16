# ⚡ Cas d'Usage : Comptage Multi-Fluides ISO 50001

> **Identifiant technique** : `ind_iso50001_multifluid` | **Catégorie** : Industrie & Automatismes | **Protocole par défaut** : MQTT / HTTP TLS

## 1. Contexte Métier & Objectif
Plan de comptage énergétique multi-fluides conforme à la norme **ISO 50001** (Électricité, Gaz Naturel, Eau Process) permettant de calculer en direct le **coût énergétique horaire (`€/h`)**, l'**IPE industriel (`kWh/tonne produite`)** et les index cumulés.

## 2. Variables Simulées & Formules Causales

| Variable ID | Libellé | Nature | Unité | Mode / Formule |
| :--- | :--- | :---: | :---: | :--- |
| `puissance_elec_kw` | Puissance Électrique Usine | Télémétrie | `kW` | `sine` `[80.0; 240.0]` |
| `debit_gaz_nm3h` | Débit Gaz Naturel | Télémétrie | `Nm³/h` | `random_walk` `[12.0; 38.0]` |
| `debit_eau_m3h` | Débit Eau Process | Télémétrie | `m³/h` | `random_walk` `[2.0; 9.5]` |
| `cout_horaire_eur` | Coût Énergétique Instantané | Télémétrie | `€/h` | `derived`: `(puissance_elec_kw * 0.18) + (debit_gaz_nm3h * 0.85) + (debit_eau_m3h * 3.2)` |
| `ipe_industriel_kwh_t` | IPE Production (kWh/tonne) | Télémétrie | `kWh/t` | `derived`: `(puissance_elec_kw + (debit_gaz_nm3h * 10.5)) / 12.0` |
| `index_elec_kwh` | Compteur Électrique Cumulé | Télémétrie | `kWh` | `integrator` (`puissance_elec_kw`, `hour`) |
| `index_eau_m3` | Compteur Eau Cumulé | Télémétrie | `m³` | `integrator` (`debit_eau_m3h`, `hour`) |
| `surveillance_talon_active` | Surveillance Talon Nocturne | Attribut | `bool` | `constant` (`true`, pilotable `SHARED_SCOPE`) |

## 3. Règles d'Alarmes ThingsBoard Recommandées
- **`MAJOR`** : `cout_horaire_eur > 85.0` (dépassement budgétaire horaire).
- **`WARNING`** : `ipe_industriel_kwh_t > 45.0` (dérive d'efficacité énergétique par tonne produite).
