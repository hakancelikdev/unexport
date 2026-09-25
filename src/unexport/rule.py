from __future__ import annotations

import ast
import dataclasses
import functools
from collections.abc import Callable, Iterator
from typing import ClassVar, NamedTuple, cast

from unexport import constants as C
from unexport import typing as T
from unexport.relate import first_occurrence, is_comprehension_target, is_runtime_missing

__all__ = ("Rule",)


class InvalidRuleFunctionError(BaseException):  # unexport: not-public
    ...


class _DefineRule(NamedTuple):
    nodes: tuple[ast.AST, ...]
    function: Callable[[ast.AST], bool]


@dataclasses.dataclass
class Rule:
    rules: ClassVar[list[_DefineRule]] = []

    @classmethod
    def register(cls, nodes: tuple[ast.AST, ...]) -> T.Function:  # type: ignore
        def f(function: T.Function) -> None:
            cls.validate_rule(function)
            cls.rules.append(_DefineRule(nodes=nodes, function=function))

        return cast(T.Function, f)

    @classmethod
    def filter_by_node(cls, node: tuple[ast.AST, ...]) -> Iterator[Callable[[ast.AST], bool]]:
        for rule in cls.rules:
            if isinstance(node, rule.nodes):  # type: ignore
                yield rule.function  # type: ignore

    @classmethod
    def apply(cls, func: T.Function) -> T.Function:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> None:
            obj, node = args[0], args[1]
            if all(rule(node) for rule in cls.filter_by_node(node)):
                func(*args, **kwargs)
            obj.generic_visit(node)

        return cast(T.Function, wrapper)

    @classmethod
    def validate_rule(cls, function: Callable[[ast.AST], bool]) -> bool:
        if not function.__name__.startswith("_rule_"):
            raise InvalidRuleFunctionError("Rule function name must start with '_rule_'.")
        elif not function.__code__.co_argcount == 1:
            raise InvalidRuleFunctionError("Rule function only gets one argument.")
        elif not function.__code__.co_varnames[0] == "node":
            raise InvalidRuleFunctionError("The parameter name must be 'node'.")
        else:
            return True


@Rule.register(  # type: ignore
    (  # type: ignore
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Name,
    )
)
def _rule_node_skip(node) -> bool:
    return node.skip is False


@Rule.register(  # type: ignore
    (  # type: ignore
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Name,
    )
)
def _rule_node_add(node) -> bool:
    return node.add is True if hasattr(node, "add") else True


@Rule.register(  # type: ignore
    (  # type: ignore
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Name,
    )
)
def _rule_parent_not_def(node) -> bool:
    return not first_occurrence(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))


@Rule.register(  # type: ignore
    (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)  # type: ignore
)
def _rule_def_name(node) -> bool:
    return not node.name.startswith("_")


@Rule.register((ast.Name,))  # type: ignore
def _rule_name_name(node) -> bool:
    if hasattr(node, "add"):
        return node.add is True
    return (node.id.isupper() or node.id[0].isupper()) and not node.id.startswith("_")


@Rule.register((ast.Name,))  # type: ignore
def _rule_name_ctx(node) -> bool:
    return isinstance(node.ctx, ast.Store)


def _assigned_value(node: ast.AST) -> ast.AST | None:
    """The value a target name gets, following tuple unpacking (``T, U = TypeVar("T"), TypeVar("U")``)."""
    path: list[int] = []
    while isinstance(node.parent, (ast.Tuple, ast.List)):  # type: ignore[attr-defined]
        path.append(node.parent.elts.index(node))  # type: ignore[attr-defined, arg-type]
        node = node.parent  # type: ignore[attr-defined]
    parent = node.parent  # type: ignore[attr-defined]
    if not isinstance(parent, (ast.Assign, ast.AnnAssign)):
        return None
    value = parent.value
    for index in reversed(path):
        if not isinstance(value, (ast.Tuple, ast.List)) or len(value.elts) <= index:
            return None
        value = value.elts[index]
    return value


@Rule.register((ast.Name,))  # type: ignore
def _rule_name_not_type_var(node) -> bool:
    if hasattr(node, "add"):
        return node.add is True
    value = _assigned_value(node)
    if not isinstance(value, ast.Call):
        return True
    func = value.func
    if isinstance(func, ast.Name):
        return func.id not in C.TYPE_VAR_FACTORIES
    if isinstance(func, ast.Attribute):
        return func.attr not in C.TYPE_VAR_FACTORIES
    return True


@Rule.register(  # type: ignore
    (  # type: ignore
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Name,
    )
)
def _rule_exists_at_runtime(node) -> bool:
    if hasattr(node, "add"):
        return node.add is True
    return not is_runtime_missing(node)


@Rule.register((ast.Name,))  # type: ignore
def _rule_name_not_comprehension_target(node) -> bool:
    if hasattr(node, "add"):
        return node.add is True
    return not is_comprehension_target(node)
