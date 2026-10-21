# 📚 Catalogue Exhaustif des Cas d'Usages Métiers IoT

Ce dossier rassemble la documentation technique intégrale des **32 modèles d'équipements virtuels pré-configurés** intégrés dans l'application **IoT Data Simulator** (version 1.6.0).

Chaque fiche détaille le contexte physique, l'architecture de communication, le dictionnaire de grandeurs, les schémas de payload JSON ThingsBoard, les scénarios d'anomalies et les recommandations de tableaux de bord.

---

## 🏭 1. Industrie & Automatismes (8 Cas d'Usage)

| ID Modèle | Équipement | Protocole | Fiche Technique | Résumé du Cas d'Usage |
|---|---|:---:|---|---|
| `ind_compressor` | **Centrale d'Air Comprimé** | `MQTT` | [01_ind_compressor.md](./01_industrie/01_ind_compressor.md) | Fourniture continue d'air comprimé pour les outillages pneumatiques, vérins et m... |
| `ind_spindle` | **Broche d'Usinage & Moteur Vibrant** | `MQTT` | [02_ind_spindle.md](./01_industrie/02_ind_spindle.md) | Usinage grande vitesse (UGV) et machines-outils CNC. Analyse vibratoire et therm... |
| `ind_chiller` | **Groupe Froid Industriel (Chiller)** | `HTTP` | [03_ind_chiller.md](./01_industrie/03_ind_chiller.md) | Production d'eau glacée pour process industriels, thermoformage ou climatisation... |
| `ind_conveyor` | **Ligne de Convoyage & Robotique** | `MQTT` | [04_ind_conveyor.md](./01_industrie/04_ind_conveyor.md) | Ligne d'assemblage automatisée ou centre logistique colis. Suivi des cadences de... |
| `ind_cold_room` | **Chambre Froide Négative & Chaîne du Froid** | `MQTT` | [05_ind_cold_room.md](./01_industrie/05_ind_cold_room.md) | Stockage agroalimentaire grand froid (-20°C) soumis aux réglementations strictes... |
| `ind_steam_boiler` | **Chaudière Industrielle Vapeur & Cogénération** | `HTTP` | [06_ind_steam_boiler.md](./01_industrie/06_ind_steam_boiler.md) | Centrale thermo-énergétique industrielle générant de la vapeur saturée pour les ... |
| `ind_cleanroom_cta` | **Salle Blanche & CTA Stérile (ISO 5 à 8)** | `COAP` | [07_ind_cleanroom_cta.md](./01_industrie/07_ind_cleanroom_cta.md) | Environnements à contamination contrôlée (laboratoires pharmaceutiques P3/P4, sa... |
| `ind_thermal_furnace` | **Four de Traitement Thermique Métallurgique** | `MQTT` | [08_ind_thermal_furnace.md](./01_industrie/08_ind_thermal_furnace.md) | Fours continus ou sous vide pour recuit, cémentation et stabilisation métallurgi... |

---

## 🏢 2. Tertiaire & Smart Building (8 Cas d'Usage)

| ID Modèle | Équipement | Protocole | Fiche Technique | Résumé du Cas d'Usage |
|---|---|:---:|---|---|
| `bldg_cta` | **Centrale de Traitement d'Air (CTA)** | `HTTP` | [01_bldg_cta.md](./02_tertiaire/01_bldg_cta.md) | Conditionnement climatique et renouvellement d'air neuf pour bureaux, centres co... |
| `bldg_tgbt` | **TGBT & Compteur Multi-Fluides** | `MQTT` | [02_bldg_tgbt.md](./02_tertiaire/02_bldg_tgbt.md) | Supervision énergétique globale du Tableau Général Basse Tension. Analyse des pu... |
| `bldg_qai` | **Station Qualité d'Air Intérieur (QAI)** | `COAP` | [03_bldg_qai.md](./02_tertiaire/03_bldg_qai.md) | Conformité décret tertiaire et santé des occupants (écoles, bureaux, crèches). M... |
| `bldg_heatpump` | **Pompe à Chaleur Réversible (PAC)** | `HTTP` | [04_bldg_heatpump.md](./02_tertiaire/04_bldg_heatpump.md) | Système thermodynamique air/eau ou eau/eau pour chauffage hivernal et rafraîchis... |
| `bldg_fire_ssi` | **Centrale Sécurité Incendie (SSI) & Désenfumage** | `MQTT` | [05_bldg_fire_ssi.md](./02_tertiaire/05_bldg_fire_ssi.md) | Équipement d'Alarme et Système de Mise en Sécurité Incendie (SMSI) conforme NF S... |
| `bldg_dali_lighting` | **Gestion d'Éclairage DALI & Détection Présence** | `HTTP` | [06_bldg_dali_lighting.md](./02_tertiaire/06_bldg_dali_lighting.md) | Télégestion et régulation de l'éclairage de bureaux selon la norme DALI-2 et EN ... |
| `bldg_thermal_meter` | **Compteur d'Énergie Thermique (Calories)** | `COAP` | [07_bldg_thermal_meter.md](./02_tertiaire/07_bldg_thermal_meter.md) | Sous-comptage calorifique MID pour audits énergétiques (bâtiments tertiaires, cl... |
| `bldg_access_flow` | **Contrôle d'Accès & Flux Bâtiment** | `HTTP` | [08_bldg_access_flow.md](./02_tertiaire/08_bldg_access_flow.md) | Hypervision des accès, badges RFID et jauges de sécurité pour sièges sociaux et ... |

---

## ⚡ 3. Infrastructures d'Énergie & Mobilité (8 Cas d'Usage)

| ID Modèle | Équipement | Protocole | Fiche Technique | Résumé du Cas d'Usage |
|---|---|:---:|---|---|
| `infra_transfo_hta` | **Transformateur HTA/BT** | `MQTT` | [01_infra_transfo_hta.md](./03_infrastructures/01_infra_transfo_hta.md) | Poste de transformation moyenne tension vers basse tension (20 kV / 400 V). Surv... |
| `infra_solar_pv` | **Onduleur Solaire Photovoltaïque** | `HTTP` | [02_infra_solar_pv.md](./03_infrastructures/02_infra_solar_pv.md) | Centrale solaire en toiture ou au sol. Conversion de la puissance continue (DC) ... |
| `infra_irve_charger` | **Borne de Recharge IRVE (Véhicules Électriques)** | `HTTP` | [03_infra_irve_charger.md](./03_infrastructures/03_infra_irve_charger.md) | Borne de recharge publique ou d'entreprise (22 kW AC à 150 kW DC). Pilotage dyna... |
| `infra_water_pump` | **Poste de Relevage Assainissement** | `COAP` | [04_infra_water_pump.md](./03_infrastructures/04_infra_water_pump.md) | Évacuation des eaux usées et pluviales dans les réseaux d'assainissement collect... |
| `infra_wind_turbine` | **Aérogénérateur / Éolienne Mégawatt** | `MQTT` | [05_infra_wind_turbine.md](./03_infrastructures/05_infra_wind_turbine.md) | Parc éolien terrestre ou offshore (turbines 2 à 5 MW). Contrôle d'orientation na... |
| `infra_bess_storage` | **Système de Stockage d'Énergie par Batteries (BESS)** | `MQTT` | [06_infra_bess_storage.md](./03_infrastructures/06_infra_bess_storage.md) | Conteneur de batteries lithium stationnaire (1 à 10 MWh) pour régulation de fréq... |
| `infra_rail_switch` | **Aiguillage & Signalisation Ferroviaire** | `HTTP` | [07_infra_rail_switch.md](./03_infrastructures/07_infra_rail_switch.md) | Appareils de voie (ADV) pour réseaux ferrés, métros et tramways. Détection prédi... |
| `infra_water_treatment` | **Bassin d'Aération & Traitement STEP** | `COAP` | [08_infra_water_treatment.md](./03_infrastructures/08_infra_water_treatment.md) | Station d'épuration municipale et industrielle (boues activées). Contrôle de la ... |

---

## 🏙️ 4. Villes Durables & Réseaux Télécoms (8 Cas d'Usage)

| ID Modèle | Équipement | Protocole | Fiche Technique | Résumé du Cas d'Usage |
|---|---|:---:|---|---|
| `city_lighting` | **Armoire d'Éclairage Public Connecté** | `COAP` | [01_city_lighting.md](./04_villes_telecoms/01_city_lighting.md) | Télégestion centralisée d'armoires urbaines d'éclairage. Pilotage de l'horloge a... |
| `city_weather` | **Station Météo & Climat Urbain** | `HTTP` | [02_city_weather.md](./04_villes_telecoms/02_city_weather.md) | Réseau de micro-capteurs météorologiques pour l'adaptation au changement climati... |
| `telecom_shelter` | **Shelter Télécoms / Nœud Fibre Optique** | `MQTT` | [03_telecom_shelter.md](./04_villes_telecoms/03_telecom_shelter.md) | Point de Raccordement Mutuel (PRM), shelter NRO ou data center de bordure (Edge)... |
| `city_traffic` | **Comptage Trafic & Mobilités Douces** | `HTTP` | [04_city_traffic.md](./04_villes_telecoms/04_city_traffic.md) | Caméras ou radars edge-AI de comptage multimodal (voitures, bus, vélos, trottine... |
| `city_waste_bin` | **Conteneur Déchets & Point d'Apport Volontaire (PAV)** | `COAP` | [05_city_waste_bin.md](./04_villes_telecoms/05_city_waste_bin.md) | Conteneurs enterrés ou semi-enterrés de tri sélectif (verre, carton, ordures mén... |
| `city_smart_irrigation` | **Arrosage Intelligent Espaces Verts & Parcs** | `HTTP` | [06_city_smart_irrigation.md](./04_villes_telecoms/06_city_smart_irrigation.md) | Préservation de la ressource en eau pour parcs municipaux, terrains de sport et ... |
| `city_acoustic_sensor` | **Sonde Acoustique & Nuisances Sonores Urbaines** | `HTTP` | [07_city_acoustic_sensor.md](./04_villes_telecoms/07_city_acoustic_sensor.md) | Observatoire du bruit urbain et surveillance des chantiers BTP ou zones de fret ... |
| `city_structure_shm` | **Surveillance Ouvrage d'Art (SHM - Ponts & Viaducs)** | `MQTT` | [08_city_structure_shm.md](./04_villes_telecoms/08_city_structure_shm.md) | Structural Health Monitoring (SHM) sur infrastructures critiques (ponts métalliq... |

---

## 🚀 Utilisation dans le Simulateur

Chacun de ces modèles peut être instancié en un clic depuis l'IHM Web (Bouton **« Modèles Métiers »**) ou par l'API REST :
```bash
curl -X POST http://localhost:8000/api/presets/instantiate \
  -H "Content-Type: application/json" \
  -d '{"preset_id": "ind_compressor", "name": "Compresseur Usine 1", "token": "VOTRE_TOKEN_THINGSBOARD"}'
```
