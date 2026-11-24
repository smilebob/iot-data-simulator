# 🤖 Guide Pas-à-Pas : Utiliser l'Agent IA « IoT Preset Architect » dans d'Autres Outils IA

> **Public** : Parcours **Débutant / Commercial (0 code)** & Parcours **Expert / Développeur & Intégrateur IA**  
> **Source du plugin** : [`customizations/antigravity/plugins/iot-preset-designer/`](../../customizations/antigravity/plugins/iot-preset-designer/)  
> **Compatibilité** : Gemini Gems, ChatGPT (Custom GPT), Claude Projects, Microsoft Copilot Studio, Claude Code, OpenAI Codex, Cursor, Windsurf, GitHub Copilot, n8n / Make / API.

---

## 🎯 Principe Général

L'agent **IoT Preset Architect** permet de transformer une simple description métier ou une **fiche technique PDF client** en un **cas d'usage industriel complet** (modèle physique 3 passes + variables dérivées + compteurs d'énergie + synoptique SCADA **ANSI/ISA-101** + tableau de bord **ThingsBoard 4.3**) directement importable dans **IoT Data Simulator**.

Parce que le plugin repose uniquement sur des fichiers standards ouverts (Markdown, JSON Schema et scripts Python), vous pouvez le déployer dans **n'importe quel outil IA** en quelques minutes.

---

# 🟢 NIVEAU 1 — PARCOURS DÉBUTANT / COMMERCIAL (0 LIGNE DE CODE)

*Objectif : créer votre assistant personnel dans **Gemini**, **ChatGPT**, **Claude** ou **Microsoft Copilot Studio** en 3 minutes, sans rien installer.*

## Étape 1 : Récupérer les 5 fichiers de référence

Ouvrez le dossier du projet :
```text
customizations/antigravity/plugins/iot-preset-designer/skills/iot-preset-generator/references/
```
Préparez ces **5 fichiers** (vous allez les déposer dans la « Base de connaissances / Fichiers » de votre outil IA) :
1. `preset_schema.json` *(format JSON officiel du simulateur)*
2. `simulation_modes.md` *(les 12 modes de simulation physique)*
3. `svg_catalog_index.json` *(catalogue des 70 composants SVG ANSI/ISA-101)*
4. `thingsboard_scada_guide.md` *(règles ThingsBoard 4.3 & ISA-101)*
5. `templates/single_preset_template.json` *(exemple complet prêt à l'emploi)*

---

## Étape 2 : Créer l'assistant dans votre outil IA préféré

Choisissez votre plateforme :
- **Google Gemini** : Menu gauche → **Gems** → **Nouveau Gem**
- **ChatGPT (Plus / Team / Enterprise)** : **Explorer les GPT** → **+ Créer** → Onglet **Configurer**
- **Claude (Pro / Team)** : **Projets** → **+ Nouveau projet**
- **Microsoft Copilot Studio** : **Agents** → **+ Nouvel agent**

Remplissez ensuite les 2 champs suivants :
1. **Nom** : `IoT Preset Architect (ThingsBoard & ISA-101)`
2. **Connaissances / Fichiers joints** : uploadez les **5 fichiers** listés à l'Étape 1.
3. **Instructions système (System Prompt)** : copiez-collez intégralement le bloc ci-dessous :

```markdown
Tu es "IoT Preset Architect", expert en automatisme industriel, efficacité énergétique et supervision SCADA ThingsBoard 4.3 conforme à la norme stricte ANSI/ISA-101.01.

Ta mission : concevoir des cas d'usage métiers (Equipment Presets) 100 % valides et importables dans IoT Data Simulator.

MÉTHODOLOGIE OBLIGATOIRE :
1. Si l'utilisateur fournit un PDF / fiche technique, extrais directement les grandeurs, plages [min, max], unités, seuils et commandes. Sinon, pose 3 questions courtes maximum (secteur, grandeurs clés, commandes pilotables).
2. Modélise les variables en 3 passes :
   - Passe 1 : Grandeurs primaires (`sine`, `random_walk`, `sawtooth`, `square`, `constant`) + attributs pilotables (`var_type: "attribute"`, `boolean` ou `float`).
   - Passe 2 : Variables dérivées (`sim_mode: "derived"`) avec formules mathématiques pures sans `eval()` (ex: `puissance_kw * 0.18`).
   - Passe 3 : Compteurs cumulés (`sim_mode: "integrator"`) dès qu'un flux (kW, m³/h) existe.
3. Respecte STRICTEMENT le schéma `preset_schema.json` et l'exemple `single_preset_template.json`.
   - Catégories autorisées : `industry`, `building`, `infrastructure`, `smart_city`.
   - Préfixes d'ID recommandés : `ind_`, `bldg_`, `infra_`, `city_`.
   - N'inclus JAMAIS le préfixe de l'équipement dans les `id` des variables (ex: `temperature_eau`, pas `mon_eq_temperature_eau`).
4. Pour le synoptique SCADA, choisis 3 à 4 composants dans `svg_catalog_index.json` (70 composants ANSI/ISA-101). Fond gris mat `#E5E7EB`, zéro couleur néon au nominal, et `label == name` sur chaque `dataKey` ThingsBoard 4.3.
5. Livraison finale : fournis TOUJOURS un bloc de code JSON complet, propre et sans commentaires (`//`), prêt à être enregistré en `.json` et importé dans IoT Data Simulator.
```

---

## Étape 3 : Générer votre premier cas d'usage (Exemples de Prompts)

### Exemple A — Création libre
> *« Crée un cas d'usage pour une station d'injection biométhane (secteur infrastructure) : débit gaz 120 à 250 Nm³/h, taux de méthane CH4 97 à 99 %, pression injection 40 bar, puissance compresseur dérivée du débit, volume cumulé Nm³ (intégrateur) et une vanne d'isolement pilotable (On/Off). »*

### Exemple B — À partir d'une fiche technique PDF client
1. Glissez-déposez le **PDF de la fiche technique** d'une machine client dans le chat.
2. Écrivez simplement :
   > *« Génère le preset JSON complet pour IoT Data Simulator + synoptique ISA-101 à partir de cette fiche technique. »*

---

## Étape 4 : Importer le JSON dans IoT Data Simulator (2 clics)

1. Copiez le bloc JSON généré par l'IA et enregistrez-le dans un fichier (ex. `biomethane.json`).
2. Ouvrez **IoT Data Simulator** → cliquez sur **Catalogue** → bouton **Importer**.
3. Sélectionnez `biomethane.json`.
4. Le simulateur valide automatiquement le schéma, ajoute votre cas d'usage dans l'onglet **Personnalisés**, et vous pouvez l'instancier + pousser son dashboard dans ThingsBoard en 1 clic !

### 🩺 Dépannage Débutant (3 erreurs fréquentes)
| Symptôme à l'import | Cause probable | Solution en 1 phrase à dire à l'IA |
| :--- | :--- | :--- |
| *« JSON invalide »* | Le JSON a été coupé à la fin ou contient des commentaires `//`. | *« Regénère le JSON complet sans aucun commentaire `//` ni `...`. »* |
| *« Variable introuvable dans formule »* | Une formule `derived` cite un nom différent de l'`id` de la variable. | *« Vérifie que chaque formule `derived` utilise exactement les `id` des variables déclarées. »* |
| *« Catégorie invalide »* | L'IA a inventé une catégorie hors liste. | *« Utilise uniquement une catégorie parmi : `industry`, `building`, `infrastructure`, `smart_city`. »* |

---

# 🔵 NIVEAU 2 — PARCOURS EXPERT (IDE IA, CLI & PIPELINES AUTOMATISÉS)

*Objectif : intégrer nativement l'agent, sa skill et ses scripts de validation dans des agents de code (**Claude Code**, **OpenAI Codex**, **Cursor**, **Windsurf**, **GitHub Copilot**) ou dans un workflow automatisé (**n8n**, **CI/CD**, **LangChain**).*

## 1. Intégration Native dans les Agents de Code (IDE & CLI)

Tous les fichiers du plugin sont versionnés dans le dépôt sous :
```text
customizations/antigravity/plugins/iot-preset-designer/
├── AGENTS.md
├── plugin.json
└── skills/iot-preset-generator/
    ├── SKILL.md
    ├── references/
    │   ├── preset_schema.json
    │   ├── simulation_modes.md
    │   ├── svg_catalog_index.json
    │   ├── thingsboard_scada_guide.md
    │   └── templates/single_preset_template.json
    └── scripts/
        ├── compose_synoptic.py
        ├── validate_preset.py
        ├── build_full_package.py
        ├── sizing_estimator.py
        └── deploy_preset.py
```

### Tableau de correspondance par outil

| Outil IA | Emplacement des instructions agent | Emplacement de la skill |
| :--- | :--- | :--- |
| **Claude Code** | Copier `AGENTS.md` vers `CLAUDE.md` (racine projet) | Copier `skills/iot-preset-generator/` vers `.claude/skills/iot-preset-generator/` |
| **OpenAI Codex CLI** | `AGENTS.md` lu nativement à la racine | Copier `skills/iot-preset-generator/` vers `.codex/skills/iot-preset-generator/` |
| **Cursor** | Copier `AGENTS.md` vers `.cursor/rules/iot-preset-architect.mdc` | Référencer `SKILL.md` et `references/` via `@` dans le composer |
| **Windsurf** | Copier `AGENTS.md` vers `.windsurfrules` | Copier `skills/iot-preset-generator/` dans `.windsurf/skills/` |
| **GitHub Copilot** | Copier `AGENTS.md` vers `.github/copilot-instructions.md` | Référencer `references/preset_schema.json` dans le prompt |

### Exemple de déploiement rapide en 1 commande (Claude Code)
```bash
mkdir -p .claude/skills
cp -r customizations/antigravity/plugins/iot-preset-designer/skills/iot-preset-generator .claude/skills/
cp customizations/antigravity/plugins/iot-preset-designer/AGENTS.md ./CLAUDE.md
```

---

## 2. Chaîne Outillée Python (Validation, Synoptique, Packaging & Déploiement)

Les 5 scripts dans `skills/iot-preset-generator/scripts/` sont exécutables en autonomie par n'importe quel agent disposant d'un shell ou par une pipeline CI/CD :

```bash
PLUGIN_SCRIPTS="customizations/antigravity/plugins/iot-preset-designer/skills/iot-preset-generator/scripts"

# 1. Composer un synoptique vectoriel ANSI/ISA-101 à partir des 70 SVG
python3 "$PLUGIN_SCRIPTS/compose_synoptic.py" --help

# 2. Valider strictement le preset généré (JSON Schema + Pydantic + AST sans cycle + TB 4.3)
python3 "$PLUGIN_SCRIPTS/validate_preset.py" --file mon_preset_raw.json

# 3. Assembler le package complet v2.1.0 (Preset + Dashboard TB 4.3 + CSV + Spec)
python3 "$PLUGIN_SCRIPTS/build_full_package.py" \
  --input mon_preset_raw.json \
  --output mon_preset_package.json

# 4. Estimer la volumétrie réseau / stockage ThingsBoard (dp/s)
python3 "$PLUGIN_SCRIPTS/sizing_estimator.py" --file mon_preset_package.json

# 5. Déployer automatiquement sur l'instance IoT Data Simulator (POST /api/presets/import)
python3 "$PLUGIN_SCRIPTS/deploy_preset.py" \
  --file mon_preset_package.json \
  --url http://127.0.0.1:8032
```

---

## 3. Intégration dans une Pipeline Automatisée (n8n, Make, LangChain, API)

Pour industrialiser la création de cas d'usage depuis un portail avant-vente interne :

1. **Entrée** : upload d'une fiche technique PDF client (extraction texte / OCR).
2. **Appel LLM en *Structured Output*** :
   - *System Prompt* : contenu de `AGENTS.md` + `SKILL.md`
   - *Response JSON Schema* : `references/preset_schema.json`
   - *Context* : `references/svg_catalog_index.json` + texte extrait du PDF
3. **Post-traitement déterministe** :
   - Exécuter `validate_preset.py` (si code retour ≠ 0, renvoyer le message d'erreur au LLM en boucle de rétroaction automatique *self-healing* max 2 essais).
   - Exécuter `build_full_package.py`.
4. **Injection API REST** :
   ```bash
   curl -X POST http://votre-simulateur:8032/api/presets/import \
     -H "Authorization: Bearer <JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d @mon_preset_package.json
   ```

---

## 4. Synchronisation & Maintenance du Plugin

- La source de vérité versionnée dans Git est **`customizations/antigravity/plugins/iot-preset-designer/`**.
- En cas d'ajout de nouveaux composants SVG dans [`app/core/svg_components.py`](../../app/core/svg_components.py), pensez à régénérer `references/svg_catalog_index.json` afin que tous les agents (Antigravity, Gemini Gems, ChatGPT, Claude Code, Codex) connaissent immédiatement les nouveaux composants ISA-101.
