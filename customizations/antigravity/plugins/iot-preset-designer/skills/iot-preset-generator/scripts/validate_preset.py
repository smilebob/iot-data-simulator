#!/usr/bin/env python3
"""
Formal Compliance Validator for IoT Equipment Presets
=====================================================
Validates schema syntax, physical completeness, mathematical AST expressions,
integrator chains, and cycle detection in derived causal topologies.
Runs standalone with zero external dependencies (Python 3 standard library only).
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
    """Custom exception raised when preset validation fails."""
    pass


def validate_formula_ast(formula: str, available_vars: Set[str]) -> List[str]:
    """Validates that a mathematical formula is structurally safe and references valid variables.

    Args:
        formula: Mathematical formula string.
        available_vars: Set of valid variable identifiers defined in the preset.

    Returns:
        List of referenced variable identifiers.

    Raises:
        ValidationError: If syntax is invalid or references unauthorized nodes/functions.
    """
    try:
        tree = ast.parse(formula, mode='eval')
    except SyntaxError as e:
        raise ValidationError(f"Syntax error in formula '{formula}': {e}")

    referenced_vars: List[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST_NODES):
            raise ValidationError(
                f"Unauthorized AST node '{type(node).__name__}' in formula '{formula}'. "
                f"Only pure arithmetic operations and mathematical functions {ALLOWED_FUNCTIONS} are permitted."
            )
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCTIONS:
                func_name = getattr(node.func, "id", "unknown")
                raise ValidationError(
                    f"Unauthorized function '{func_name}()' in formula '{formula}'. "
                    f"Permitted functions: {sorted(ALLOWED_FUNCTIONS)}."
                )
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name not in ALLOWED_FUNCTIONS:
                if var_name not in available_vars:
                    raise ValidationError(
                        f"Variable '{var_name}' referenced in formula '{formula}' "
                        f"does not exist in preset. Available variables: {sorted(available_vars)}"
                    )
                referenced_vars.append(var_name)

    return referenced_vars


def check_cycles(dep_graph: Dict[str, List[str]]):
    """Detects cyclic dependencies in derived variable topological dependency graphs.

    Args:
        dep_graph: Directed graph mapping variable IDs to their dependency lists.

    Raises:
        ValidationError: If a circular causal loop is detected.
    """
    visited: Set[str] = set()
    stack: Set[str] = set()

    def visit(node: str, path: List[str]):
        visited.add(node)
        stack.add(node)
        for neighbor in dep_graph.get(node, []):
            if neighbor in stack:
                cycle_str = " -> ".join(path + [neighbor])
                raise ValidationError(f"Circular dependency detected: {cycle_str}")
            if neighbor not in visited:
                visit(neighbor, path + [neighbor])
        stack.remove(node)

    for n in dep_graph:
        if n not in visited:
            visit(n, [n])


def validate_preset_dict(preset: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validates an EquipmentPreset dictionary against schema and physical constraints.

    Args:
        preset: Preset dictionary to validate.

    Returns:
        Tuple of (is_valid, warnings_list).

    Raises:
        ValidationError: If any mandatory schema or semantic validation fails.
    """
    warnings: List[str] = []

    # 1. Mandatory fields
    for req in ("id", "name", "category", "category_label", "variables"):
        if req not in preset or preset[req] is None:
            raise ValidationError(f"Missing mandatory field in preset: '{req}'")

    # 2. Identifier format
    if not re.match(r"^[a-z0-9_]+$", preset["id"]):
        raise ValidationError(f"Preset ID '{preset['id']}' must contain only lowercase letters, digits, and underscores.")

    # 3. Category
    if preset["category"] not in VALID_CATEGORIES:
        raise ValidationError(
            f"Invalid category '{preset['category']}'. "
            f"Allowed values: {sorted(VALID_CATEGORIES)}"
        )

    # 4. Variables list
    variables = preset.get("variables", [])
    if not isinstance(variables, list) or len(variables) == 0:
        raise ValidationError("Preset must contain at least one variable in 'variables'.")

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
