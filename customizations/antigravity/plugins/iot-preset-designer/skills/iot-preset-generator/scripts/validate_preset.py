#!/usr/bin/env python3
"""
Script de validation formelle de conformité pour les modèles d'équipements IoT (Presets).
Vérifie la syntaxe, la complétude, la validité des formules causales AST et l'absence de cycles.
Exécutable de manière autonome avec Python 3 standard (zéro dépendance externe).
"""

import ast
import json
import os
import re
import sys
import argparse
from typing import Dict, List, Set, Any, Tuple

VALID_CATEGORIES = {"industry", "building", "infrastructure", "smart_city"}
VALID_VAR_TYPES = {"telemetry", "attribute"}
VALID_DATA_TYPES = {"float", "integer", "boolean", "string"}
VALID_SIM_MODES = {
    "sine", "cosine", "triangle", "square", "sawtooth", "ramp",
    "random_walk", "gaussian", "constant", "points_table", "derived", "integrator"
}
ALLOWED_AST_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd, ast.Call, ast.Load
)
ALLOWED_FUNCTIONS = {"abs", "min", "max", "round", "sqrt", "sin", "cos"}

class ValidationError(Exception):
    pass

def validate_formula_ast(formula: str, available_vars: Set[str]) -> List[str]:
    """Valide qu'une formule mathématique est saine et ne référence que des variables existantes."""
    try:
        tree = ast.parse(formula, mode='eval')
    except SyntaxError as e:
        raise ValidationError(f"Erreur de syntaxe dans la formule '{formula}': {e}")

    referenced_vars: List[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST_NODES):
            raise ValidationError(
                f"Opération interdite '{type(node).__name__}' dans la formule '{formula}'. "
                f"Seules les opérations arithmétiques pures et les fonctions {ALLOWED_FUNCTIONS} sont autorisées."
            )
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCTIONS:
                func_name = getattr(node.func, "id", "inconnue")
                raise ValidationError(
                    f"Fonction non autorisée '{func_name}()' dans la formule '{formula}'. "
                    f"Fonctions autorisées : {sorted(ALLOWED_FUNCTIONS)}."
                )
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name not in ALLOWED_FUNCTIONS:
                if var_name not in available_vars:
                    raise ValidationError(
                        f"La variable '{var_name}' référencée dans la formule '{formula}' "
                        f"n'existe pas dans le modèle. Variables disponibles : {sorted(available_vars)}"
                    )
                referenced_vars.append(var_name)

    return referenced_vars

def check_cycles(dep_graph: Dict[str, List[str]]):
    """Détecte les éventuelles dépendances circulaires entre variables dérivées."""
    visited: Set[str] = set()
    stack: Set[str] = set()

    def visit(node: str, path: List[str]):
        visited.add(node)
        stack.add(node)
        for neighbor in dep_graph.get(node, []):
            if neighbor in stack:
                cycle_str = " -> ".join(path + [neighbor])
                raise ValidationError(f"Dépendance circulaire détectée : {cycle_str}")
            if neighbor not in visited:
                visit(neighbor, path + [neighbor])
        stack.remove(node)

    for n in dep_graph:
        if n not in visited:
            visit(n, [n])

def validate_preset_dict(preset: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valide l'objet EquipmentPreset."""
    warnings: List[str] = []

    # 1. Champs obligatoires
    for req in ("id", "name", "category", "category_label", "variables"):
        if req not in preset or preset[req] is None:
            raise ValidationError(f"Champ obligatoire manquant dans le preset : '{req}'")

    # 2. Format de l'ID
    if not re.match(r"^[a-z0-9_]+$", preset["id"]):
        raise ValidationError(f"L'ID du preset '{preset['id']}' doit être en minuscules avec chiffres et tirets bas uniquement.")

    # 3. Catégorie
    if preset["category"] not in VALID_CATEGORIES:
        raise ValidationError(
            f"Catégorie invalide '{preset['category']}'. "
            f"Valeurs autorisées : {sorted(VALID_CATEGORIES)}"
        )

    # 4. Variables
    variables = preset.get("variables", [])
    if not isinstance(variables, list) or len(variables) == 0:
        raise ValidationError("Le modèle doit contenir au moins une variable dans 'variables'.")

    var_ids: Set[str] = set()
    dep_graph: Dict[str, List[str]] = {}

    for i, v in enumerate(variables):
        if not isinstance(v, dict):
            raise ValidationError(f"La variable à l'indice {i} n'est pas un objet JSON.")
        
        # Champs obligatoires
        for v_req in ("id", "name", "var_type", "data_type", "sim_mode"):
            if v_req not in v or v[v_req] is None:
                raise ValidationError(f"Variable #{i} ({v.get('id', 'sans_id')}) : champ obligatoire manquant '{v_req}'")

        v_id = v["id"]
        if v_id in var_ids:
            raise ValidationError(f"Identifiant de variable dupliqué : '{v_id}'")
        var_ids.add(v_id)

        if v["var_type"] not in VALID_VAR_TYPES:
            raise ValidationError(f"Variable '{v_id}' : var_type '{v['var_type']}' invalide. Attendu : {sorted(VALID_VAR_TYPES)}")

        if v["data_type"] not in VALID_DATA_TYPES:
            raise ValidationError(f"Variable '{v_id}' : data_type '{v['data_type']}' invalide. Attendu : {sorted(VALID_DATA_TYPES)}")

        sim_mode = v["sim_mode"]
        if sim_mode not in VALID_SIM_MODES:
            raise ValidationError(f"Variable '{v_id}' : sim_mode '{sim_mode}' invalide. Attendu : {sorted(VALID_SIM_MODES)}")

    # 5. Validation des dépendances et formules
    for v in variables:
        v_id = v["id"]
        sim_mode = v["sim_mode"]

        if sim_mode == "derived":
            cfg = v.get("derived_config") or {}
            formula = cfg.get("formula", "").strip()
            if not formula:
                raise ValidationError(f"Variable dérivée '{v_id}' : 'derived_config.formula' est obligatoire.")
            
            # Formule ne doit pas se référencer elle-même
            other_vars = var_ids - {v_id}
            deps = validate_formula_ast(formula, other_vars)
            dep_graph[v_id] = deps

        elif sim_mode == "integrator":
            cfg = v.get("integrator_config") or {}
            src = cfg.get("source_variable", "").strip()
            if not src:
                raise ValidationError(f"Variable intégratrice '{v_id}' : 'integrator_config.source_variable' est obligatoire.")
            if src not in var_ids:
                raise ValidationError(f"Variable intégratrice '{v_id}' : la variable source '{src}' n'existe pas dans le preset.")
            if src == v_id:
                raise ValidationError(f"Variable intégratrice '{v_id}' ne peut pas s'intégrer elle-même.")
            dep_graph[v_id] = [src]

    # Vérification des cycles
    check_cycles(dep_graph)

    return True, warnings

def validate_file(file_path: str) -> bool:
    """Valide un fichier JSON complet (package unitaire, bundle ou preset brut)."""
    if not os.path.exists(file_path):
        print(f"❌ Erreur : Fichier introuvable '{file_path}'", file=sys.stderr)
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Erreur de syntaxe JSON dans '{file_path}' : {e}", file=sys.stderr)
        return False

    presets_to_test = []
    if isinstance(data, dict):
        if data.get("export_type") == "presets_bundle" and "presets_packages" in data:
            for pkg in data["presets_packages"]:
                presets_to_test.append(pkg.get("preset", pkg))
        elif "preset" in data and isinstance(data["preset"], dict):
            presets_to_test.append(data["preset"])
        else:
            presets_to_test.append(data)
    elif isinstance(data, list):
        for item in data:
            presets_to_test.append(item.get("preset", item) if isinstance(item, dict) else item)

    if not presets_to_test:
        print("❌ Erreur : Aucun modèle d'équipement trouvé dans le fichier.", file=sys.stderr)
        return False

    success_count = 0
    for idx, p in enumerate(presets_to_test):
        try:
            validate_preset_dict(p)
            var_count = len(p.get("variables", []))
            print(f"✅ Modèle #{idx + 1} valide : '{p.get('name')}' (id: '{p.get('id')}', {var_count} grandeurs, secteur: {p.get('category')})")
            success_count += 1
        except ValidationError as ve:
            print(f"❌ Erreur de conformité sur le modèle #{idx + 1} ('{p.get('id', 'inconnu')}') : {ve}", file=sys.stderr)
        except Exception as ex:
            print(f"❌ Exception inattendue sur le modèle #{idx + 1} : {ex}", file=sys.stderr)

    if success_count == len(presets_to_test):
        print(f"\n🎉 Succès total : {success_count}/{len(presets_to_test)} modèle(s) 100% conforme(s) et prêt(s) pour l'importateur IoT Simulator !")
        return True
    else:
        print(f"\n⚠️ Échec : {len(presets_to_test) - success_count} modèle(s) non conforme(s).", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Validateur de modèles de cas d'usage IoT Data Simulator")
    parser.add_argument("--file", "-f", required=True, help="Chemin du fichier JSON à valider")
    args = parser.parse_args()

    ok = validate_file(args.file)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
