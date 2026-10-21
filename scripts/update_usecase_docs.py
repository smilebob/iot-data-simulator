#!/usr/bin/env python3
"""
Mise à jour exhaustive des 32 fiches documentaires de cas d'usage métiers
(Documentation/use_cases/*/*.md) avec les spécifications du pilotage bidirectionnel,
des widgets de contrôle ThingsBoard 4.3 et des synoptiques SCADA P&ID vectoriels.
"""

import os
import sys
import glob
import types

# Mocks minimaux pour exécution sans dépendances externes
pyd = types.ModuleType('pydantic')
class BaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items(): setattr(self, k, v)
    def model_copy(self, deep=True):
        import copy; return copy.deepcopy(self)
    def model_dump(self): return self.__dict__
def Field(default=None, default_factory=None, **kwargs):
    if default_factory: return default_factory()
    return default
pyd.BaseModel = BaseModel
pyd.Field = Field
pyd.field_validator = lambda *a, **k: (lambda f: f)
sys.modules['pydantic'] = pyd

for mod in ['paho', 'paho.mqtt', 'paho.mqtt.client', 'fastapi', 'fastapi.responses', 'aiocoap', 'httpx']:
    m = types.ModuleType(mod)
    m.Client = lambda *a, **k: None
    m.Response = lambda *a, **k: None
    sys.modules[mod] = m

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.core.equipment_catalog import get_equipment_catalog
from app.models.variable import VariableType, DataType

CAT_DIR_MAP = {
    "industry": "01_industrie",
    "building": "02_tertiaire",
    "infrastructure": "03_infrastructures",
    "smart_city": "04_villes_telecoms"
}

def clean_key(var_id: str) -> str:
    return var_id.replace('-', '_')

def generate_section_6(eq, rel_dir):
    dash_rel = f"dashboards/thingsboard/{rel_dir}/{eq.id}.json"
    dash_link = f"[`{dash_rel}`](file://{BASE_DIR}/{dash_rel})"
    
    telemetries = [v for v in eq.variables if v.var_type == VariableType.TELEMETRY]
    attributes = [v for v in eq.variables if v.var_type == VariableType.ATTRIBUTE]

    # Description jauges
    jauges_list = ", ".join([f"{v.name} ({v.unit})" if v.unit else v.name for v in telemetries[:3]])

    sec6 = f"## 6. Pilotage Interactif & Tableaux de Bord ThingsBoard 4.3\n\n"
    sec6 += f"Le tableau de bord officiel préconfiguré {dash_link} intègre l'ensemble des composants nécessaires à l'exploitation temps réel sous ThingsBoard 4.3 :\n\n"
    sec6 += f"- **Synoptique SCADA Vectoriel P&ID (Widget HTML Card)** : Schéma de principe industriel vectoriel SVG haute résolution, adapté aux écrans de contrôle (fond clair pro WCAG AA, animations CSS de flux/rotations). Les pastilles de télémétries dynamiques sont liées par clé technique exacte (`clean_key` comme `dataKey.label`) garantissant une résolution instantanée des variables `${{cle:decimales}}` sous ThingsBoard 4.3.\n"

    if attributes:
        sec6 += "- **Commandes & Pilotage Interactif Bidirectionnel** :\n"
        for a in attributes:
            ck = clean_key(a.id)
            if a.data_type == DataType.BOOLEAN:
                sec6 += f"  - **Interrupteur Circulaire (*Round Switch*) - {a.name}** : Commutateur interactif (`system.control_widgets.round_switch`) lié à l'attribut partagé `{ck}` (`SHARED_SCOPE`). Permet à l'opérateur de basculer la commande (ON/OFF) depuis ThingsBoard. Le simulateur intercepte la requête RPC (`set_{ck}` ou `setValue`), applique immédiatement la consigne avec forçage manuel (`manual_override = True`), acquitte la requête sur `v1/devices/me/rpc/response/{{id}}` et confirme le nouvel état d'attribut sur `v1/devices/me/attributes`.\n"
            else:
                sec6 += f"  - **Formulaire de Consigne (*Update Multiple Attributes*) - {a.name}** : Widget de saisie interactif (`system.input_widgets.update_multiple_attributes`) permettant de renseigner la consigne `{ck}` ({a.data_type.value}). Les modifications sont instantanément répercutées dans la simulation physique via l'abonnement aux attributs partagés.\n"
    else:
        sec6 += "- **Mode Opérationnel Autonome & Télémétrie Pure** : Cet équipement fonctionne en régulation automatique continue. Les attributs affichés dans la table récapitulative fournissent les métadonnées d'inventaire technique (modèle constructeur, révision logicielle, protocole de liaison).\n"

    sec6 += f"- **Jauges Analogiques (JustGage Widgets)** : Restitution visuelle instantanée des grandeurs critiques ({jauges_list}) avec paliers de couleur normés (vert = nominal, ambre = vigilance, rouge = seuil critique).\n"
    sec6 += f"- **Courbes d'Historique Télémétrique & Table d'Attributs** : Graphique temporel multi-courbes synchronisé (fenêtre glissante de 24h) et vue tabulaire des attributs client/partagés.\n"

    return sec6

def enhance_section_4_2(eq):
    attributes = [v for v in eq.variables if v.var_type == VariableType.ATTRIBUTE]
    
    sec4_2 = "### 4.2 Attributs d'État Partagés, Client & RPC ThingsBoard\n\n"
    if attributes:
        sec4_2 += "#### Topic d'Attributs Partagés (`v1/devices/me/attributes`)\n"
        sec4_2 += "Le simulateur publie et synchronise ses attributs d'état opérationnels :\n"
        sec4_2 += "```json\n{\n"
        lines = []
        for a in attributes:
            ck = clean_key(a.id)
            if a.data_type == DataType.BOOLEAN:
                val = "true"
            elif a.data_type in (DataType.FLOAT, DataType.INTEGER):
                val = "100"
            else:
                val = '"VALEUR"'
            lines.append(f'  "{ck}": {val}')
        sec4_2 += ",\n".join(lines) + "\n}\n```\n\n"
        
        sec4_2 += "#### Pilotage par RPC Bidirectionnel (`v1/devices/me/rpc/request/{id}`)\n"
        sec4_2 += "L'opérateur peut envoyer une consigne ou basculer un état depuis un widget de tableau de bord ThingsBoard 4.3 :\n"
        first_attr = attributes[0]
        ck = clean_key(first_attr.id)
        example_param = "true" if first_attr.data_type == DataType.BOOLEAN else (50 if first_attr.data_type == DataType.INTEGER else '"AUTO"')
        sec4_2 += "```json\n"
        sec4_2 += f'// Requête descendante ThingsBoard -> Simulateur\n'
        sec4_2 += f'{{\n  "method": "set_{ck}",\n  "params": {example_param}\n}}\n\n'
        sec4_2 += f'// Réponse immédiate Simulateur -> ThingsBoard (sur v1/devices/me/rpc/response/{{id}})\n'
        sec4_2 += f'{{\n  "status": "SUCCESS",\n  "value": {example_param}\n}}\n'
        sec4_2 += "```\n"
    else:
        sec4_2 += "```json\n{\n"
        sec4_2 += f'  "modele": "{eq.name}",\n'
        sec4_2 += f'  "firmware_version": "v2.4.1",\n'
        sec4_2 += f'  "statut_equipement": "OPERATIONNEL"\n'
        sec4_2 += "}\n```\n"
    
    return sec4_2

def update_doc_file(doc_path, eq, rel_dir):
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update Section 4.2
    # Find ### 4.2 up to ## 5.
    idx_4_2 = content.find('### 4.2')
    idx_5 = content.find('## 5.')
    if idx_4_2 != -1 and idx_5 != -1:
        new_4_2 = enhance_section_4_2(eq)
        content = content[:idx_4_2] + new_4_2 + "\n---\n\n" + content[idx_5:]

    # 2. Update Section 6
    # Find ## 6.
    idx_6 = content.find('## 6.')
    if idx_6 != -1:
        new_6 = generate_section_6(eq, rel_dir)
        content = content[:idx_6] + new_6
    else:
        new_6 = generate_section_6(eq, rel_dir)
        content = content.rstrip() + "\n\n---\n\n" + new_6

    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    catalog = {eq.id: eq for eq in get_equipment_catalog()}
    docs = sorted(glob.glob(os.path.join(BASE_DIR, 'Documentation/use_cases/*/*.md')))
    updated_count = 0

    for d in docs:
        rel_dir = os.path.basename(os.path.dirname(d))
        base = os.path.basename(d).replace('.md', '')
        eq_id = '_'.join(base.split('_')[1:])
        if eq_id in catalog:
            eq = catalog[eq_id]
            update_doc_file(d, eq, rel_dir)
            updated_count += 1
            print(f"[{updated_count}/32] Updated: {os.path.relpath(d, BASE_DIR)}")
        else:
            print(f"SKIPPED (not in catalog): {d}")

    print(f"\nSuccessfully updated {updated_count} use case documentation files.")

if __name__ == '__main__':
    main()
