"""
Secure Physical Evaluation Engine for Derived Variables and Time Integrators.

Provides sandboxed, deterministic evaluation of mathematical formulas using Python's
Abstract Syntax Tree (AST) parser without calling eval() or exec(), strictly preventing
arbitrary code execution while supporting algebraic and trigonometric dependencies.
"""

import ast
import logging
import math
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger("iot_sim.physics")


def _safe_round(val: Any, n: Any = 0) -> float:
    """Rounds a numeric value safely to n decimal places.

    Args:
        val: Input numeric value.
        n: Decimal precision count (default: 0).

    Returns:
        float: Rounded numeric result.
    """
    try:
        return float(round(float(val), int(n)))
    except Exception:
        return float(round(float(val)))


def _safe_pow(a: Any, b: Any) -> float:
    """Computes bounded exponentiation to prevent CPU exhaustion and overflow.

    Args:
        a: Base numeric value.
        b: Exponent power (clamped within [-10, 10]).

    Returns:
        float: Computed power or 0.0 if exponent exceeds bounds.
    """
    exp = float(b)
    if abs(exp) > 10:
        return 0.0
    return float(pow(float(a), exp))


# Whitelist of allowed pure mathematical functions in AST expressions
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
    """Sandboxed Abstract Syntax Tree (AST) mathematical expression evaluator.

    Permits only pure arithmetic operators, comparisons, ternary conditionals,
    and whitelisted functions from SAFE_FUNCTIONS. Rejects all attributes, imports,
    dunder lookups, assignments, and external function calls.
    """

    @classmethod
    def evaluate(cls, expression: str, context: Dict[str, Any]) -> float:
        """Evaluates an algebraic formula against a dictionary of variable values.

        Args:
            expression: Mathematical expression string
                (e.g., '(flow_rate * delta_temp * 1.163)').
            context: Dictionary mapping variable identifiers to numeric metric values.

        Returns:
            float: Evaluated numeric result, or 0.0 upon syntax/zero-division errors.

        Example:
            >>> SafeExpressionEvaluator.evaluate('p * 2', {'p': 12.5})
            25.0
        """
        if not expression or not expression.strip():
            return 0.0

        try:
            tree = ast.parse(expression.strip(), mode="eval")
            return float(cls._eval_node(tree.body, context))
        except ZeroDivisionError:
            return 0.0
        except Exception as e:
            logger.debug(f"Formula evaluation error in expression '{expression}': {e}")
            return 0.0

    @classmethod
    def _eval_node(cls, node: ast.AST, context: Dict[str, Any]) -> Any:
        """Recursively walks and evaluates validated AST nodes.

        Args:
            node: Current AST node to evaluate.
            context: Variable identifier lookup dictionary.

        Returns:
            Any: Computed intermediate value of the node.

        Raises:
            ValueError: If an untrusted, unsupported, or unsafe AST construct is encountered.
        """
        # Literal constants (integers, floats, booleans)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return node.value
            elif isinstance(node.value, (int, float)):
                return node.value
            return 0.0

        # Variable identifier lookup
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name in context:
                val = context[var_name]
                if isinstance(val, (int, float, bool)):
                    return float(val)
                return 0.0
            
            # Fallback suffix lookup (e.g., 'pressure' resolves to 'dev1_pressure')
            for k, val in context.items():
                if k.endswith(f"_{var_name}") or k == var_name:
                    if isinstance(val, (int, float, bool)):
                        return float(val)
            return 0.0

        # Unary operations (-x, +x, not x)
        elif isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand, context)
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.Not):
                return not operand
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

        # Binary arithmetic operations (+, -, *, /, //, %, **)
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
                # Clamp power to avoid overflow
                if abs(right) > 10:
                    return 0.0
                return left ** right
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")

        # Comparison operations (==, !=, <, <=, >, >=)
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

        # Ternary conditional expressions (A if Condition else B)
        elif isinstance(node, ast.IfExp):
            test = cls._eval_node(node.test, context)
            return cls._eval_node(node.body, context) if test else cls._eval_node(node.orelse, context)

        # Authorized mathematical function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
                func = SAFE_FUNCTIONS[node.func.id]
                args = [cls._eval_node(arg, context) for arg in node.args]
                return func(*args)
            raise ValueError(f"Unauthorized function call in formula: {ast.dump(node.func)}")

        raise ValueError(f"Unsupported syntax tree structure: {type(node).__name__}")

    @classmethod
    def extract_dependencies(cls, expression: str) -> Set[str]:
        """Parses an expression and extracts all referenced variable identifiers.

        Useful for building directed acyclic dependency graphs (DAG) to order evaluation.

        Args:
            expression: Mathematical expression string.

        Returns:
            Set[str]: Unique set of variable names found in the formula.

        Example:
            >>> SafeExpressionEvaluator.extract_dependencies('temp_in - temp_out')
            {'temp_in', 'temp_out'}
        """
        if not expression or not expression.strip():
            return set()
        try:
            tree = ast.parse(expression.strip(), mode="eval")
            return {
                node.id for node in ast.walk(tree)
                if isinstance(node, ast.Name) and node.id not in SAFE_FUNCTIONS
            }
        except Exception:
            return set()
