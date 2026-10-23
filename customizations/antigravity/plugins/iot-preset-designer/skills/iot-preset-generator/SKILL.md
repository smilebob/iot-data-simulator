---
name: iot-preset-generator
description: >-
  Conçoit, valide et génère des cas d'usage métiers industriels (Equipment Presets) 100% conformes et importables dans IoT Data Simulator et ThingsBoard 4.3.
  Utilisez cette skill lorsque l'utilisateur veut créer un nouveau modèle d'équipement (ex: électrolyseur, four, chiller, compresseur, centrale solaire, station de pompage),
  définir des signaux physiques mathématiques, des variables dérivées (formules AST), des compteurs d'énergie intégrateurs, ou préparer des tableaux de bord SCADA ThingsBoard.
---

# Skill : Générateur de Cas d'Usage Métier pour IoT Data Simulator

Cette skill guide l'agent pour structurer, modéliser, valider et livrer un cas d'usage métier (*Equipment Preset*) prêt pour l'application **IoT Data Simulator** (v2.2.0+) et **ThingsBoard 4.3**.

---

## 🛠️ Ressources & Documentation Embarquées

Pour respecter le principe de *Progressive Disclosure*, lisez les fichiers de référence associés selon les besoins de la modélisation :

| Document | Rôle & Contenu |
| :--- | :--- |
| [`references/preset_schema.json`](references/preset_schema.json) | Schéma JSON Schema v2.1.0 formel du format de package d'export/import. |
| [`references/simulation_modes.md`](references/simulation_modes.md) | Spécification complète des 12 modes de simulation (ondes, causalités AST, intégrateurs continus). |
| [`references/thingsboard_scada_guide.md`](references/thingsboard_scada_guide.md) | Directives d'intégration SCADA ThingsBoard 4.3, SVG P&ID animé et dataKeys `${cle}`. |
| [`references/templates/single_preset_template.json`](references/templates/single_preset_template.json) | Modèle de référence complet d'un package JSON prêt à l'emploi. |

---

## 📋 Méthodologie en 5 Étapes

### Étape 1 : Cadrage Métier & Classification Sectorielle
Déterminer la catégorie de l'équipement :
- `industry` : *Industrie & Automatismes* (machines-outils, fours, compresseurs, groupes froids, chaudières, robots)
- `building` : *Tertiaire & Smart Building* (CTA, GTB, CVC, PAC, TGBT, éclairage DALI, SSI incendie, QAI)
- `infrastructure` : *Infrastructures & Énergie* (postes HTA, onduleurs PV, éoliennes, bornes IRVE, stations d'épuration, pompage)
- `smart_city` : *Villes & Télécoms* (éclairage public intelligent, stations météo, mobilités, gestion des déchets, SHM)

Choisir un identifiant technique unique en minuscules avec préfixe sectoriel (ex: `ind_electrolyzer`, `bldg_chiller_nh3`, `infra_bess_grid`).

---

### Étape 2 : Définition des Variables (Télémétries & Attributs)
Chaque grandeur doit être caractérisée par :
1. `id` : Identifiant technique de la métrique sans le préfixe équipement (ex: `pression_h2`, `debit_eau`, `temperature_stack`, `puissance_active`).
2. `name` : Nom lisible en français avec unités entre parenthèses si applicable.
3. `var_type` :
   - `"telemetry"` : Grandeurs physiques continues horodatées.
   - `"attribute"` : États de marche, consignes, modes de fonctionnement pilotables par ThingsBoard.
4. `data_type` : `"float"`, `"integer"`, `"boolean"` ou `"string"`.
5. `unit` : Symbole officiel de l'unité (`bar`, `°C`, `kW`, `kWh`, `m³/h`, `A`, `V`, `Hz`, `%`, `ppm`).
6. `publish_interval` : Fréquence d'émission en secondes (ex: `1.0` ou `2.0` pour le process, `10.0` pour les températures d'inertie, `30.0` pour les attributs).

---

### Étape 3 : Modélisation Mathématique & Causalité Physique
Associer le mode de calcul approprié :
1. **Grandeurs Principales (Sources primaires)** :
   - Process oscillant régulier : `sine` ou `cosine` (avec `min_val`, `max_val`, `period`).
   - Cycles de remplissage / montée progressive : `sawtooth` ou `ramp`.
   - Marche aléatoire avec inertie thermique/pression : `random_walk` (avec `step`, `noise_percent`).
   - Signal numérique bistable : `square` ou `constant`.
2. **Grandeurs Dérivées (`derived`)** :
   - Lier les grandeurs physiques par des formules causales via `derived_config`.
   - Formule Python standard sans `eval()` (opérateurs arithmétiques `+`, `-`, `*`, `/`, `**`, `abs()`, `min()`, `max()`).
   - Exemple pour un compresseur : `puissance_active = (pression_cuve * 4.2) + (debit_air * 1.5)`.
3. **Compteurs Cumulés (`integrator`)** :
   - Dès qu'une grandeur de flux (puissance instantanée en kW, débit en m³/h ou kg/s) existe, ajouter une variable intégratrice continue avec `integrator_config` :
     ```json
     "integrator_config": {
       "source_variable": "puissance_active",
       "time_unit": "hours",
       "initial_val": 1250.0
     }
     ```

---

### Étape 4 : Validation du Package
Toujours exécuter le script de validation intégré pour tester le modèle avant de le soumettre à l'utilisateur :
```bash
python3 scripts/validate_preset.py --file mon_nouveau_preset.json
```
Le script vérifie :
- La validité du JSON et du schéma Pydantic.
- L'analyse syntaxique AST des formules de calcul.
- L'existence de toutes les variables référencées dans les formules dérivées et les intégrateurs.
- L'absence de cycles ou dépendances circulaires.

---

### Étape 5 : Assemblage Automatique du Package Complet (ThingsBoard SCADA & CSV)
Si l'utilisateur a rédigé uniquement la définition du modèle `preset`, utilisez l'outil :
```bash
python3 scripts/build_full_package.py --input mon_preset_brut.json --output preset_export_pret_a_importer.json
```
Ce script adjoint automatiquement :
1. Le gabarit ThingsBoard 4.3 complet (avec synoptique vectoriel SVG dynamique relié aux dataKeys, jauges JustGage, graphiques temporels et widgets de contrôle).
2. L'en-tête et modèle de ligne CSV ThingsBoard (`name,type,label,access_token`).
3. Les paramètres d'instanciation en 1 clic.

---

## 🚀 Restitution à l'Utilisateur
Une fois le package validé, délivrez :
1. Le code JSON formaté ou le chemin du fichier sauvegardé.
2. Un bref tableau récapitulatif des variables physiques et de leurs formules causales.
3. Le rappel de la commande ou du bouton d'importation :
   - *Dans l'IHM* : Ouvrir **Modèles Métiers** ➔ Cliquer sur **Importer** ➔ Sélectionner le fichier JSON.
   - *Par API REST* : `curl -X POST http://localhost:8000/api/presets/import -H "Content-Type: application/json" -d @mon_preset.json`
