# Bibliothèque des Tableaux de Bord ThingsBoard (JSON Export)

> **Version ThingsBoard supportée** : ThingsBoard Community Edition (CE) et Professional Edition (PE) v3.x à v3.8+
> **Nombre de tableaux de bord préconfigurés** : 32 modèles métiers

Ce dossier contient les fichiers de configuration JSON prêts à être importés dans votre serveur ThingsBoard.

---

## 🚀 Procédure d'Importation en 3 Étapes dans ThingsBoard

1. **Ouvrir ThingsBoard** : Rendez-vous dans le menu latéral gauche **Tableaux de bord (Dashboards)**.
2. **Importer le fichier JSON** : Cliquez sur le bouton **`+`** en haut à droite, puis sélectionnez **`Importer le tableau de bord` (Import Dashboard)** et chargez le fichier `.json` correspondant à votre cas d'usage.
3. **Mapper l'alias de l'équipement** :
   - Une fenêtre pop-up intitulée *« Résolution des alias d'entités »* s'affiche automatiquement.
   - Pour l'alias portant le nom de votre modèle, sélectionnez dans le menu déroulant l'équipement virtuel réel que vous avez créé sur ThingsBoard.
   - Cliquez sur **`Ajouter`** ou **`Terminer`**.

Toutes les jauges, graphiques temps réel et indicateurs s'animent instantanément avec les flux émis par le simulateur !

---

## 💡 Téléchargement Direct depuis l'Application & Sécurité des Données

Vous pouvez télécharger le tableau de bord préconfiguré pour n'importe quel équipement instancié :
- Dans l'application web du simulateur, localisez votre équipement créé dans la liste.
- Cliquez sur le bouton **`Dashboard TB`** présent dans la barre d'outils de l'équipement.
- Le fichier JSON généré intègre le synoptique SCADA dédié, l'ensemble des grandeurs et la configuration d'alias.
- **Sécurité & Protection des Secrets (CIS / OWASP)** : Par mesure de sécurité, l'Access Token ThingsBoard n'est jamais affiché ni gravé en clair dans le tableau de bord, évitant ainsi toute fuite de secret lors de l'export ou du partage d'écrans. Le rattachement s'effectue automatiquement via l'alias d'entité lors de l'importation.

---

## 📋 Répertoire des Tableaux de Bord par Secteur

### Industrie & Automatismes (`01_industrie/`)

| Modèle | Fichier JSON | Grandeurs Incluses |
|---|---|---|
| **Centrale d'Air Comprimé** | [`ind_compressor.json`](01_industrie/ind_compressor.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Broche d'Usinage & Moteur** | [`ind_spindle.json`](01_industrie/ind_spindle.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Groupe Froid Industriel** | [`ind_chiller.json`](01_industrie/ind_chiller.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Ligne de Convoyage & Robotique** | [`ind_conveyor.json`](01_industrie/ind_conveyor.json) | 3 grandeurs (Jauges + Télémétries + Attributs) |
| **Chambre Froide Négative** | [`ind_cold_room.json`](01_industrie/ind_cold_room.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Chaudière Industrielle Vapeur** | [`ind_steam_boiler.json`](01_industrie/ind_steam_boiler.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Salle Blanche & CTA Stérile (ISO)** | [`ind_cleanroom_cta.json`](01_industrie/ind_cleanroom_cta.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Four de Traitement Thermique** | [`ind_thermal_furnace.json`](01_industrie/ind_thermal_furnace.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |

### Bâtiments Intelligents & Tertiaire (`02_tertiaire/`)

| Modèle | Fichier JSON | Grandeurs Incluses |
|---|---|---|
| **Centrale Traitement d'Air (CTA)** | [`bldg_cta.json`](02_tertiaire/bldg_cta.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **TGBT & Compteur Multi-Fluides** | [`bldg_tgbt.json`](02_tertiaire/bldg_tgbt.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Station Qualité d'Air (QAI)** | [`bldg_qai.json`](02_tertiaire/bldg_qai.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Pompe à Chaleur Réversible (PAC)** | [`bldg_heatpump.json`](02_tertiaire/bldg_heatpump.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Centrale Sécurité Incendie (SSI)** | [`bldg_fire_ssi.json`](02_tertiaire/bldg_fire_ssi.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Gestion d'Éclairage DALI & Présence** | [`bldg_dali_lighting.json`](02_tertiaire/bldg_dali_lighting.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Compteur d'Énergie Thermique (Calories)** | [`bldg_thermal_meter.json`](02_tertiaire/bldg_thermal_meter.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Contrôle d'Accès & Flux Bâtiment** | [`bldg_access_flow.json`](02_tertiaire/bldg_access_flow.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |

### Infrastructures Énergétiques & Réseaux (`03_infrastructures/`)

| Modèle | Fichier JSON | Grandeurs Incluses |
|---|---|---|
| **Transformateur HTA/BT** | [`infra_transfo_hta.json`](03_infrastructures/infra_transfo_hta.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Onduleur Solaire Photovoltaïque** | [`infra_solar_pv.json`](03_infrastructures/infra_solar_pv.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Borne de Recharge IRVE** | [`infra_irve_charger.json`](03_infrastructures/infra_irve_charger.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Poste de Relevage Assainissement** | [`infra_water_pump.json`](03_infrastructures/infra_water_pump.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Aérogénérateur / Éolienne MW** | [`infra_wind_turbine.json`](03_infrastructures/infra_wind_turbine.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Système Stockage Batteries (BESS)** | [`infra_bess_storage.json`](03_infrastructures/infra_bess_storage.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Aiguillage & Signalisation Ferroviaire** | [`infra_rail_switch.json`](03_infrastructures/infra_rail_switch.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Bassin d'Aération & Traitement STEP** | [`infra_water_treatment.json`](03_infrastructures/infra_water_treatment.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |

### Villes Intelligentes & Télécoms (`04_villes_telecoms/`)

| Modèle | Fichier JSON | Grandeurs Incluses |
|---|---|---|
| **Armoire d'Éclairage Public** | [`city_lighting.json`](04_villes_telecoms/city_lighting.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Station Météo & Climat Urbain** | [`city_weather.json`](04_villes_telecoms/city_weather.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Shelter Télécoms / Nœud Fibre** | [`telecom_shelter.json`](04_villes_telecoms/telecom_shelter.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Comptage Trafic & Mobilités** | [`city_traffic.json`](04_villes_telecoms/city_traffic.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Conteneur Déchets & PAV Connecté** | [`city_waste_bin.json`](04_villes_telecoms/city_waste_bin.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Arrosage Intelligent Espaces Verts** | [`city_smart_irrigation.json`](04_villes_telecoms/city_smart_irrigation.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |
| **Sonde Acoustique & Nuisances Sonores** | [`city_acoustic_sensor.json`](04_villes_telecoms/city_acoustic_sensor.json) | 4 grandeurs (Jauges + Télémétries + Attributs) |
| **Surveillance Ouvrage d'Art (SHM)** | [`city_structure_shm.json`](04_villes_telecoms/city_structure_shm.json) | 5 grandeurs (Jauges + Télémétries + Attributs) |

