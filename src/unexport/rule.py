from __future__ import annotations

import ast
import dataclasses
import functools
from typing import Callable, ClassVar, Iterator, NamedTuple, cast

from unexport import typing as T
from unexport.relate import first_occurrence

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


@Rule.register((ast.Assign,))  # type: ignore
def _rule_node_is_all(node) -> bool:
    return getattr(node.targets[0], "id", None) == "__all__" and isinstance(node.value, (ast.List, ast.Tuple, ast.Set))


@Rule.register((ast.Expr,))  # type: ignore
def _rule_node_is_all_item(node) -> bool:
    return (
        isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "__all__"
    )


@Rule.register((ast.Name,))  # type: ignore
def _rule_node_is_typevar(node) -> bool:
    modules: list[str] = []
    if isinstance(node.parent.value, ast.Call):
        if 'TypeVar' == getattr(node.parent.value.func, 'id', None):
            modules.extend(body.module for body in node.parent.parent.body if isinstance(body, ast.ImportFrom))
        elif 'typing' == getattr(node.parent.value.func.value, 'id', None) and 'TypeVar' == getattr(node.parent.value.func, 'attr', None):
            for body in node.parent.parent.body:
                if isinstance(body, ast.Import):
                    modules.extend([import_alias.name for import_alias in body.names])
        if 'typing' in modules:
            return False
    return True
