# 📦 Guide : Import / Export de Cas d'Usage Métiers & Agent IA Antigravity

> **Version** : 2.2.0+  
> **Composants** : Bibliothèque d'équipements métiers (*Equipment Catalog*), Packages JSON normalisés, Plugin Antigravity `iot-preset-designer`  
> **Compatibilité** : ThingsBoard 4.3, Eclipse Mosquitto, Google Antigravity (IDE, CLI `agy`, Desktop 2.0)

---

## 1. Vue d'Ensemble

Depuis la version **v2.2.0**, l'IoT Data Simulator intègre un système complet d'**importation et d'exportation de cas d'usage métiers** (*Equipment Presets*), ainsi qu'un **Agent IA spécialisé pour Google Antigravity** permettant de générer de nouveaux modèles 100 % conformes en quelques secondes.

### 🌟 Avantages Clés
1. **Packages 100 % Autonomes & Exhaustifs** : Un export contient l'intégralité du modèle (variables, équations mathématiques, dépendances causales, intégrateurs d'énergie), le modèle complet de tableau de bord ThingsBoard 4.3 (synoptique SCADA vectoriel P&ID/SLD animé, jauges et commandes interactives), la structure CSV ThingsBoard et les paramètres d'instanciation en 1 clic.
2. **Persistance Sécurisée en Volume Docker** : Les modèles personnalisés sont stockés dans `data/custom_presets.json` (au sein du volume persistant `simulator_data`), préservés lors des mises à jour applicatives.
3. **Protection des 32 Modèles d'Usine** : Les 32 modèles natifs du simulateur restent immuables et protégés contre toute suppression ou écrasement accidentel.
4. **Génération par Agent IA** : Le plugin Antigravity `iot-preset-designer` permet à tout utilisateur de converser avec un agent expert pour concevoir des équipements sur-mesure (ex: électrolyseur hydrogène, méthaniseur, chiller ammoniac, centrale solaire hybride).

---

## 2. Utilisation dans l'Interface Graphique (IHM)

### 2.1 Exporter un Cas d'Usage
1. Ouvrez l'application web sur **[http://localhost:8000](http://localhost:8000)** (ou votre port Portainer ex: `8032`).
2. Cliquez sur le bouton **Modèles Métiers** dans l'en-tête pour ouvrir le catalogue.
3. Sur n'importe quelle carte d'équipement (natif ou personnalisé), cliquez sur l'icône verte **`download`** (Exporter ce cas d'usage).
4. Le navigateur télécharge immédiatement le fichier `preset_export_<id>.json`.

### 2.2 Exporter l'Ensemble de la Bibliothèque (Bundle)
1. Dans l'en-tête de la modale du catalogue, cliquez sur le bouton vert **`Exporter tout`**.
2. Un fichier archive `presets_catalog_full_bundle.json` est téléchargé, contenant l'ensemble des modèles de tous les secteurs.

### 2.3 Importer un ou Plusieurs Modèles
1. Dans l'en-tête de la modale du catalogue, cliquez sur le bouton bleu **`Importer`**.
2. Sélectionnez votre fichier `.json` (package unitaire, bundle ou fichier de modèle brut).
3. L'application valide immédiatement le fichier. En cas de succès :
   - Le message de confirmation s'affiche avec le nombre de modèles importés.
   - Le catalogue se rafraîchit automatiquement et bascule sur le nouvel onglet **Personnalisés**.
   - Le badge **`Custom`** apparaît sur les nouveaux modèles.

### 2.4 Instancier un Modèle Importé en 1 Clic
1. Cliquez sur le bouton **`Utiliser`** sur la carte du modèle importé.
2. La fenêtre d'instanciation s'ouvre, pré-remplie avec le protocole recommandé, le préfixe d'ID et l'intervalle d'envoi.
3. Renseignez ou générez le Token ThingsBoard (bouton JWT) puis validez.
4. L'équipement et l'ensemble de ses grandeurs physiques (y compris formules dérivées et intégrateurs) sont créés instantanément !

### 2.5 Supprimer un Modèle Personnalisé
1. Sur les modèles personnalisés, une icône rouge **`trash-2`** (Supprimer) est disponible.
2. Cliquez dessus et confirmez la suppression.
3. *Note : Cette icône n'apparaît jamais sur les 32 modèles natifs d'usine, qui sont strictement protégés.*

---

## 3. Endpoints API REST Dédiés

| Méthode | URL | Rôle RBAC | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/presets/{preset_id}/export` | `ROLE_ANY` | Télécharge le package JSON exhaustif du modèle `{preset_id}`. |
| `GET` | `/api/presets/export/all` | `ROLE_ANY` | Télécharge le bundle JSON de tous les modèles du catalogue. |
| `POST` | `/api/presets/import` | `OPERATOR`/`ADMIN` | Importe un modèle ou un bundle (reçoit JSON brut ou fichier multipart). |
| `DELETE` | `/api/presets/{preset_id}` | `OPERATOR`/`ADMIN` | Supprime un modèle personnalisé. Rejette les modèles natifs avec HTTP 400. |

### Exemples cURL :
```bash
# Export unitaire
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/presets/ind_compressor/export -o ind_compressor.json

# Import de fichier JSON
curl -X POST http://localhost:8000/api/presets/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @mon_nouveau_preset.json
```

---

## 4. L'Agent IA Antigravity : `iot-preset-designer`

Pour accélérer la création de nouveaux cas d'usage métiers sans avoir à écrire manuellement du JSON ou concevoir des SVG complexes, un plugin Antigravity officiel est disponible dans le projet :

👉 **`customizations/antigravity/plugins/iot-preset-designer/`**

### 4.1 Capacités de l'Agent IA
- **Rôle** : *IoT Preset Architect*, Automaticien SCADA & Ingénieur IoT.
- **Skill** : `iot-preset-generator` (activée à la demande lors de requêtes de création d'équipements).
- **Connaissance Métier** :
  - Maîtrise des 12 modes de simulation (`sine`, `sawtooth`, `random_walk`, etc.).
  - Écriture d'équations causales AST sécurisées (`derived`) sans `eval()`.
  - Intégrateurs continus d'énergie active (`integrator`) en kWh, MWh, m³, kg.
  - Conception de synoptiques P&ID / SLD industriels vectoriels en SVG animé.
  - Conformité ThingsBoard 4.3 (dataKeys avec `label == clean_name`, widgets `system.single_switch` sur `SHARED_SCOPE`).

### 4.2 Scripts Autonomes Inclus dans le Plugin
- **`scripts/validate_preset.py`** : Valide la conformité syntaxique, les formules AST et vérifie l'absence de références circulaires avant livraison.
  ```bash
  python3 validate_preset.py --file mon_preset.json
  ```
- **`scripts/build_full_package.py`** : Transforme un preset brut en package complet prêt à importer avec tableau de bord ThingsBoard 4.3 et template CSV.
  ```bash
  python3 build_full_package.py --input preset_brut.json --output preset_pret_a_importer.json
  ```

### 4.3 Installation & Activation dans Antigravity
Le plugin est déjà déployé dans `~/.gemini/config/plugins/iot-preset-designer/`. Pour toute nouvelle machine ou collaborateur :
```bash
# Copier le plugin dans la configuration globale Antigravity
cp -r customizations/antigravity/plugins/iot-preset-designer ~/.gemini/config/plugins/
```
Il est immédiatement actif dans **Antigravity IDE**, **Antigravity 2.0** et la CLI **`agy`** !
