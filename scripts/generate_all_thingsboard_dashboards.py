#!/usr/bin/env python3
"""
ThingsBoard Dashboard Automated Batch Generator
===============================================
Generates standalone, compliant ThingsBoard 4.3 JSON dashboard descriptors
for all 32 industrial equipment catalog presets.

Organizes exports into sector directories:
- `01_industrie/` (Industrial Automation & Machinery)
- `02_tertiaire/` (Smart Buildings & HVAC)
- `03_infrastructures/` (Energy Grids & Pumping Networks)
- `04_villes_telecoms/` (Smart Cities, Logistics & Telecoms)
"""

import os
import sys
import json
import types

# Lightweight mock stubs to allow execution outside container runtime without external pip packages
pyd = types.ModuleType('pydantic')
class BaseModel:
    """Mock Pydantic BaseModel for standalone CLI execution."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def model_copy(self, deep=True):
        import copy
        return copy.deepcopy(self)
    def model_dump(self):
        return self.__dict__

def Field(default=None, default_factory=None, description=None, **kwargs):
    """Mock Pydantic Field."""
    if default_factory:
        return default_factory()
    return default

pyd.BaseModel = BaseModel
pyd.Field = Field
pyd.field_validator = lambda *a, **k: (lambda f: f)
sys.modules['pydantic'] = pyd

# Mock transport and networking dependencies
for mod in ['paho', 'paho.mqtt', 'paho.mqtt.client', 'fastapi', 'fastapi.responses', 'aiocoap', 'httpx']:
    m = types.ModuleType(mod)
    m.Client = lambda *a, **k: None
    m.Response = lambda *a, **k: None
    sys.modules[mod] = m

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.core.equipment_catalog import get_equipment_catalog
from app.core.dashboard_generator import generate_thingsboard_dashboard
from app.models.device import DeviceConfig

CATEGORY_DIR_MAP = {
    "industry": ("01_industrie", "Industrie & Automatismes"),
    "building": ("02_tertiaire", "Bâtiments Intelligents & Tertiaire"),
    "infrastructure": ("03_infrastructures", "Infrastructures Énergétiques & Réseaux"),
    "smart_city": ("04_villes_telecoms", "Villes Intelligentes & Télécoms"),
}

def main():
    """Generates all ThingsBoard dashboards and creates directory index README.md."""
    target_base = os.path.join(BASE_DIR, "dashboards", "thingsboard")
    os.makedirs(target_base, exist_ok=True)

    catalog = get_equipment_catalog()
    generated_count = 0
    catalog_summary = {}

    for preset in catalog:
        subfolder, cat_name = CATEGORY_DIR_MAP.get(preset.category, ("00_divers", "Cas d'usage"))
        cat_dir = os.path.join(target_base, subfolder)
        os.makedirs(cat_dir, exist_ok=True)

        # Create model device configuration with sample token
        device = DeviceConfig(
            id=preset.id,
            name=preset.name,
            platform=preset.default_platform,
            protocol=preset.default_protocol,
            token=f"TOKEN_{preset.id.upper()}",
            publish_interval=None,
            enabled=True
        )

        # Deep clone variables with target device ID binding
        vars_copy = []
        for orig in preset.variables:
            v = orig.model_copy(deep=True)
            v.device_id = device.id
            vars_copy.append(v)

        dashboard_json = generate_thingsboard_dashboard(device, vars_copy)

        filename = f"{preset.id}.json"
        filepath = os.path.join(cat_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(dashboard_json, f, indent=2, ensure_ascii=False)

        generated_count += 1
        catalog_summary.setdefault(subfolder, []).append((preset.id, preset.name, len(preset.variables), filename))
        print(f"[{subfolder}] Generated: {filename} ({preset.name})")

    # Generate index README inside dashboards/thingsboard/
    readme_path = os.path.join(target_base, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# Bibliothèque des Tableaux de Bord ThingsBoard (JSON Export)\n\n")
        f.write("> **Version ThingsBoard supportée** : ThingsBoard Community Edition (CE) et Professional Edition (PE) v3.x à v3.8+\n")
        f.write("> **Nombre de tableaux de bord préconfigurés** : 32 modèles métiers\n\n")
        f.write("Ce dossier contient les fichiers de configuration JSON prêts à être importés dans votre serveur ThingsBoard.\n\n")
        f.write("---\n\n")
        f.write("## 🚀 Procédure d'Importation en 3 Étapes dans ThingsBoard\n\n")
        f.write("1. **Ouvrir ThingsBoard** : Rendez-vous dans le menu latéral gauche **Tableaux de bord (Dashboards)**.\n")
        f.write("2. **Importer le fichier JSON** : Cliquez sur le bouton **`+`** en haut à droite, puis sélectionnez **`Importer le tableau de bord` (Import Dashboard)** et chargez le fichier `.json` correspondant à votre cas d'usage.\n")
        f.write("3. **Mapper l'alias de l'équipement** :\n")
        f.write("   - Une fenêtre pop-up intitulée *« Résolution des alias d'entités »* s'affiche automatiquement.\n")
        f.write("   - Pour l'alias portant le nom de votre modèle, sélectionnez dans le menu déroulant l'équipement virtuel réel que vous avez créé sur ThingsBoard.\n")
        f.write("   - Cliquez sur **`Ajouter`** ou **`Terminer`**.\n\n")
        f.write("Toutes les jauges, graphiques temps réel et indicateurs s'animent instantanément avec les flux émis par le simulateur !\n\n")
        f.write("---\n\n")
        f.write("## 💡 Astuce : Téléchargement Direct depuis l'Application\n\n")
        f.write("Vous pouvez également télécharger un tableau de bord contenant **directement votre vrai Access Token ThingsBoard** :\n")
        f.write("- Dans l'application web du simulateur, localisez votre équipement créé dans la liste.\n")
        f.write("- Cliquez sur le bouton **`Dashboard TB`** présent dans la barre d'outils de l'équipement.\n")
        f.write("- Le fichier JSON téléchargé intègrera automatiquement votre Token d'authentification et votre nom d'équipement exact !\n\n")
        f.write("---\n\n")
        f.write("## 📋 Répertoire des Tableaux de Bord par Secteur\n\n")

        for subfolder in sorted(catalog_summary.keys()):
            cat_name = dict(CATEGORY_DIR_MAP.values()).get(subfolder, subfolder)
            for k, (sfolder, name) in CATEGORY_DIR_MAP.items():
                if sfolder == subfolder:
                    cat_name = name
                    break

            f.write(f"### {cat_name} (`{subfolder}/`)\n\n")
            f.write("| Modèle | Fichier JSON | Grandeurs Incluses |\n")
            f.write("|---|---|---|\n")
            for pid, pname, var_count, fname in catalog_summary[subfolder]:
                f.write(f"| **{pname}** | [`{fname}`]({subfolder}/{fname}) | {var_count} grandeurs (Jauges + Télémétries + Attributs) |\n")
            f.write("\n")

    print(f"\n✅ Total: {generated_count} ThingsBoard dashboards successfully generated in '{target_base}'!")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
