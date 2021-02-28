from __future__ import annotations

import ast
import functools
from dataclasses import dataclass
from typing import Callable, ClassVar, Iterator, cast

from pyall import constants as C
from pyall.relate import first_occurrence

__all__ = ["InvalidRuleFunctionError", "Rule"]


class InvalidRuleFunctionError(BaseException):
    ...


@dataclass
class Rule:
    nodes: tuple[ast.AST, ...]
    rule: Callable[[ast.AST], bool]

    rules: ClassVar[list[Rule]] = []

    @classmethod
    def register(cls, nodes: tuple[ast.AST, ...]) -> C.Function:
        def f(rule: C.Function) -> None:
            cls.validate_rule(rule)
            cls.rules.append(cls(nodes=nodes, rule=rule))

        return cast(C.Function, f)

    @classmethod
    def filter_by_node(
        cls, node: tuple[ast.AST, ...]
    ) -> Iterator[Callable[[ast.AST], bool]]:
        for rule in cls.rules:
            if isinstance(node, rule.nodes):  # type: ignore
                yield rule.rule  # type: ignore

    @classmethod
    def apply_rules(cls, func: C.Function) -> C.Function:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> None:
            obj = args[0]
            node = args[1]

            check_rules = all(rule(node) for rule in cls.filter_by_node(node))
            if check_rules:
                func(*args, **kwargs)
            else:
                obj.generic_visit(node)

        return cast(C.Function, wrapper)

    @classmethod
    def validate_rule(cls, rule: Callable[[ast.AST], bool]) -> bool:
        if not rule.__name__.startswith("_rule_"):
            raise InvalidRuleFunctionError(
                "Rule function name must start with '_rule_'."
            )
        elif not rule.__code__.co_argcount == 1:
            raise InvalidRuleFunctionError(
                "Rule function only gets one argument."
            )
        elif not rule.__code__.co_varnames[0] == "node":
            raise InvalidRuleFunctionError(
                "The parameter name must be 'node'."
            )
        else:
            return True


@Rule.register((ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Name))
def _rule_node_skip(node) -> bool:
    return not node.skip


@Rule.register((ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
def _rule_def_name(node) -> bool:
    return not node.name.startswith("_")


@Rule.register((ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Name))
def _rule_parent_not_def(node) -> bool:
    return not first_occurrence(
        node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    )


@Rule.register((ast.Name,))
def _rule_name_name(node) -> bool:
    return (
        node.id.isupper() or node.id[0].isupper()
    ) and not node.id.startswith("_")


@Rule.register((ast.Name,))
def _rule_name_ctx(node) -> bool:
    return isinstance(node.ctx, ast.Store)


@Rule.register((ast.Assign,))
def _rule_node_is_all(node) -> bool:
    return getattr(node.targets[0], "id", None) == "__all__" and isinstance(
        node.value, (ast.List, ast.Tuple, ast.Set)
    )


@Rule.register((ast.Expr,))
def _rule_node_is_all_item(node) -> bool:
    return (
        isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "__all__"
    )
