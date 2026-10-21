"""
Moteur d'évaluation physique sécurisé pour les variables dérivées et intégrateurs temporels.
Fournit une évaluation sûre d'expressions mathématiques sans recours à eval().
"""

import ast
import logging
import math
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger("iot_sim.physics")

def _safe_round(val: Any, n: Any = 0) -> float:
    try:
        return float(round(float(val), int(n)))
    except Exception:
        return float(round(float(val)))

def _safe_pow(a: Any, b: Any) -> float:
    exp = float(b)
    if abs(exp) > 10:
        return 0.0
    return float(pow(float(a), exp))

# Fonctions mathématiques autorisées dans les expressions
SAFE_FUNCTIONS: Dict[str, Callable] = {
    "abs": lambda x: float(abs(float(x))),
    "round": _safe_round,
    "min": lambda *args: float(min(*(float(a) for a in args))),
    "max": lambda *args: float(max(*(float(a) for a in args))),
    "pow": _safe_pow,
    "sqrt": lambda x: math.sqrt(max(0.0, float(x))),
    "sin": lambda x: math.sin(float(x)),
    "cos": lambda x: math.cos(float(x)),
    "tan": lambda x: math.tan(float(x)),
    "exp": lambda x: math.exp(min(20.0, float(x))),
    "log": lambda x: math.log(max(1e-9, float(x))),
    "floor": lambda x: float(math.floor(float(x))),
    "ceil": lambda x: float(math.ceil(float(x))),
}

class SafeExpressionEvaluator:
    """
    Évaluateur AST sécurisé limitant l'exécution aux seules opérations arithmétiques pures
    et fonctions mathématiques élémentaires.
    """

    @classmethod
    def evaluate(cls, expression: str, context: Dict[str, Any]) -> float:
        """
        Évalue une formule mathématique avec le dictionnaire de variables fourni.
        Ex: evaluate('debit * delta_t * 1.163', {'debit': 2.5, 'delta_t': 12.0})
        """
        if not expression or not expression.strip():
            return 0.0

        try:
            tree = ast.parse(expression.strip(), mode="eval")
            return float(cls._eval_node(tree.body, context))
        except ZeroDivisionError:
            return 0.0
        except Exception as e:
            logger.debug(f"Erreur évaluation expression '{expression}': {e}")
            return 0.0

    @classmethod
    def _eval_node(cls, node: ast.AST, context: Dict[str, Any]) -> Any:
        # Constante numérique ou booléenne
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return node.value
            elif isinstance(node.value, (int, float)):
                return node.value
            return 0.0

        # Identifiant / Nom de variable
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name in context:
                val = context[var_name]
                if isinstance(val, (int, float, bool)):
                    return float(val)
                return 0.0
            
            # Recherche avec suffixe (ex: 'debit' pour 'dev1_debit')
            for k, val in context.items():
                if k.endswith(f"_{var_name}") or k == var_name:
                    if isinstance(val, (int, float, bool)):
                        return float(val)
            return 0.0

        # Opérations unaires (-x, +x, not x)
        elif isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand, context)
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.Not):
                return not operand
            raise ValueError(f"Opérateur unaire non supporté: {node.op}")

        # Opérations binaires (+, -, *, /, //, %, **)
        elif isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left, context)
            right = cls._eval_node(node.right, context)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right if right != 0 else 0.0
            elif isinstance(node.op, ast.FloorDiv):
                return left // right if right != 0 else 0.0
            elif isinstance(node.op, ast.Mod):
                return left % right if right != 0 else 0.0
            elif isinstance(node.op, ast.Pow):
                # Limite raisonnable pour éviter les débordements
                if abs(right) > 10:
                    return 0.0
                return left ** right
            raise ValueError(f"Opérateur binaire non supporté: {node.op}")

        # Comparaisons (==, !=, <, <=, >, >=)
        elif isinstance(node, ast.Compare):
            left = cls._eval_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right = cls._eval_node(comparator, context)
                if isinstance(op, ast.Eq) and not (left == right):
                    return False
                elif isinstance(op, ast.NotEq) and not (left != right):
                    return False
                elif isinstance(op, ast.Lt) and not (left < right):
                    return False
                elif isinstance(op, ast.LtE) and not (left <= right):
                    return False
                elif isinstance(op, ast.Gt) and not (left > right):
                    return False
                elif isinstance(op, ast.GtE) and not (left >= right):
                    return False
            return True

        # Expression ternaire (A if Cond else B)
        elif isinstance(node, ast.IfExp):
            test = cls._eval_node(node.test, context)
            return cls._eval_node(node.body, context) if test else cls._eval_node(node.orelse, context)

        # Appel de fonction mathématique autorisée
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
                func = SAFE_FUNCTIONS[node.func.id]
                args = [cls._eval_node(arg, context) for arg in node.args]
                return func(*args)
            raise ValueError(f"Fonction non autorisée: {ast.dump(node.func)}")

        raise ValueError(f"Syntaxe d'expression non supportée: {type(node).__name__}")

    @classmethod
    def extract_dependencies(cls, expression: str) -> Set[str]:
        """Extrait l'ensemble des noms de variables référencées dans une expression."""
        if not expression or not expression.strip():
            return set()
        try:
            tree = ast.parse(expression.strip(), mode="eval")
            return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id not in SAFE_FUNCTIONS}
        except Exception:
            return set()
