# 🏢 Cas d'Usage : GTB Classe A (Décret BACS / Tertiaire)

> **Identifiant technique** : `bldg_bacs_class_a` | **Catégorie** : Tertiaire & Smart Building | **Protocole par défaut** : MQTT / HTTP TLS

## 1. Contexte Métier & Objectif
Modèle conçu pour les réponses aux appels d'offres **Décret BACS** (EN ISO 52120-1 Classe A) et **Décret Tertiaire** (-40 % d'énergie en 2030). Il combine le suivi CVC/Éclairage DALI avec le calcul en temps réel de l'**IPE surfacique**, des **émissions CO2** et du **gain énergétique vs référence**.

## 2. Variables Simulées & Formules Causales

| Variable ID | Libellé | Nature | Unité | Mode / Formule |
| :--- | :--- | :---: | :---: | :--- |
| `temp_ambiante` | Température Ambiante Zone | Télémétrie | `°C` | `random_walk` `[19.2; 21.8]` |
| `puissance_cvc_kw` | Puissance Appelée CVC | Télémétrie | `kW` | `sine` `[8.0; 28.0]` |
| `puissance_eclairage_kw` | Puissance Éclairage DALI | Télémétrie | `kW` | `sine` `[1.5; 7.5]` |
| `puissance_totale_kw` | Puissance Totale Bâtiment | Télémétrie | `kW` | `derived`: `puissance_cvc_kw + puissance_eclairage_kw` |
| `ipe_surfacique_kwh_m2` | IPE Surfacique (2500 m²) | Télémétrie | `kWh/m².an` | `derived`: `(puissance_totale_kw * 8760.0) / 2500.0` |
| `emissions_co2_kg_h` | Émissions CO2 Instantanées | Télémétrie | `kgCO2/h` | `derived`: `puissance_totale_kw * 0.052` |
| `economie_bacs_pct` | Gain Énergétique BACS vs Réf. | Télémétrie | `%` | `derived`: `max(0.0, min(45.0, (1.0 - (puissance_totale_kw / 45.0)) * 100.0))` |
| `energie_cumulee_kwh` | Index Énergie Bâtiment | Télémétrie | `kWh` | `integrator` (`puissance_totale_kw`, `hour`) |
| `mode_bacs_classe_a` | Régulation Optimisée BACS | Attribut | `bool` | `constant` (`true`, pilotable `SHARED_SCOPE`) |

## 3. Règles d'Alarmes ThingsBoard Recommandées
- **`MAJOR`** : `ipe_surfacique_kwh_m2 > 140` (dérive énergétique hors cible Décret Tertiaire).
- **`WARNING`** : `temp_ambiante > 24.0` ou `temp_ambiante < 18.0` (inconfort thermique).
