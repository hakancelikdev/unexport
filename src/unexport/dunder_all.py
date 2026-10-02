"""Find the module-level statements that define or change ``__all__``."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from typing import NamedTuple

__all__ = ("AllStatement", "find_all_statements")

_NESTED_BLOCKS = (ast.If, ast.Try, ast.With, ast.For, ast.While) + tuple(
    getattr(ast, name) for name in ("TryStar", "Match") if hasattr(ast, name)
)


class AllStatement(NamedTuple):
    node: ast.stmt
    names: list[str]  # the string literals it adds
    is_literal: bool  # False when part of it can't be read statically (e.g. ``+ sub.__all__``)


def _is_all(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and node.id == "__all__"


def _literal_names(value: ast.expr | None) -> tuple[list[str], bool]:
    """String items of a list/tuple/set, or of a ``+`` chain of them."""
    if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
        left, left_literal = _literal_names(value.left)
        right, right_literal = _literal_names(value.right)
        return left + right, left_literal and right_literal
    if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        names = [item.value for item in value.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)]
        return names, len(names) == len(value.elts)
    return [], False


def _binds_all(target: ast.expr) -> bool:
    """``__all__`` inside an unpacking target, e.g. ``__all__, X = [...], 1``."""
    return any(_is_all(node) for node in ast.walk(target))


def _read(node: ast.stmt) -> AllStatement | None:
    if isinstance(node, ast.Assign) and any(_is_all(target) for target in node.targets):
        return AllStatement(node, *_literal_names(node.value))
    if isinstance(node, (ast.Import, ast.ImportFrom)) and any(
        (alias.asname or alias.name) == "__all__" for alias in node.names
    ):
        return AllStatement(node, [], False)  # ``from io import __all__``: its names can't be read here
    if isinstance(node, (ast.Assign, ast.For, ast.AsyncFor)) and any(
        _binds_all(target) for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
    ):
        return AllStatement(node, [], False)
    if isinstance(node, ast.AnnAssign) and _is_all(node.target) and node.value is not None:
        return AllStatement(node, *_literal_names(node.value))
    if isinstance(node, ast.AugAssign) and _is_all(node.target):
        names, is_literal = _literal_names(node.value)
        return AllStatement(node, names, is_literal and isinstance(node.op, ast.Add))
    if (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and _is_all(node.value.func.value)
    ):
        method, args = node.value.func.attr, node.value.args
        if method == "append" and len(args) == 1:
            if isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                return AllStatement(node, [args[0].value], True)
        elif method == "extend" and len(args) == 1:
            return AllStatement(node, *_literal_names(args[0]))
        return AllStatement(node, [], False)  # remove(), insert(), clear(), ... or a non-literal argument
    return None


def _module_level(statements: list[ast.stmt]) -> Iterator[ast.stmt]:
    """Statements at module level, including inside if/try/with/for/while/match blocks, not in functions or classes."""
    for node in statements:
        yield node
        if isinstance(node, _NESTED_BLOCKS):
            for field in ("body", "orelse", "finalbody"):
                yield from _module_level(getattr(node, field, []))
            for block in [*getattr(node, "handlers", []), *getattr(node, "cases", [])]:
                yield from _module_level(block.body)


def find_all_statements(tree: ast.Module) -> list[AllStatement]:
    statements = [statement for node in _module_level(tree.body) if (statement := _read(node)) is not None]
    return sorted(statements, key=lambda statement: (statement.node.lineno, statement.node.col_offset))
