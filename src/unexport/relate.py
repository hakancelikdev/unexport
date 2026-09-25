from __future__ import annotations

import ast
from collections.abc import Iterator

__all__ = (
    "first_occurrence",
    "get_parents",
    "is_bare_annotation",
    "is_comprehension_target",
    "is_runtime_missing",
    "relate",
)


def relate(tree: ast.AST, parent: ast.AST | None = None) -> None:
    tree.parent = parent  # type: ignore
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node  # type: ignore


def get_parents(node: ast.AST) -> Iterator[ast.AST]:
    parent = node
    while parent:
        if parent := parent.parent:  # type: ignore
            yield parent


def first_occurrence(node: ast.AST, *ancestors):
    for parent in get_parents(node):
        if isinstance(parent, *ancestors):
            return parent
    else:
        return False


def _is_type_checking(test: ast.expr) -> bool:
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
    )


def _is_main_guard(test: ast.expr) -> bool:
    """``if __name__ == "__main__":`` (either operand order)."""
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
        return False
    operands = [test.left, *test.comparators]
    return any(isinstance(item, ast.Name) and item.id == "__name__" for item in operands) and any(
        isinstance(item, ast.Constant) and item.value == "__main__" for item in operands
    )


def is_runtime_missing(node: ast.AST) -> bool:
    """Whether node is in the body of ``if TYPE_CHECKING:`` or ``if __name__ == "__main__":``.

    Names defined there don't exist when the module is imported, so
    exporting them breaks ``from module import *``. The ``else`` branch
    does run.
    """
    child = node
    for parent in get_parents(node):
        if (
            isinstance(parent, ast.If)
            and child in parent.body
            and (_is_type_checking(parent.test) or _is_main_guard(parent.test))
        ):
            return True
        child = parent
    return False


def is_comprehension_target(node: ast.AST) -> bool:
    """Whether node is (part of) the target of a comprehension, which is local to the comprehension."""
    child = node
    for parent in get_parents(node):
        if isinstance(parent, ast.comprehension):
            return child is parent.target
        if isinstance(parent, ast.stmt):
            return False
        child = parent
    return False


def is_bare_annotation(node: ast.AST) -> bool:
    """Whether node is the target of an annotation without a value (``X: int``), which binds nothing at runtime."""
    parent = getattr(node, "parent", None)
    return isinstance(parent, ast.AnnAssign) and parent.target is node and parent.value is None
