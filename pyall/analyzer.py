import ast
import functools
from typing import Set, cast

from pyall import constants as C
from pyall import relate

__all__ = ["Analyzer"]


def _visitor_recursive(func: C.Function) -> C.Function:
    """Decorator to make visitor work recursive."""

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        self.generic_visit(*args)

    return cast(C.Function, wrapper)


class _AllItemNameAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.all: Set[str] = set()
        self.classes: Set[str] = set()
        self.functions: Set[str] = set()
        self.variables: Set[str] = set()

    @_visitor_recursive
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if not relate.first_occurrence(
            node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            if not node.name.startswith("_"):
                self.classes.add(node.name)

    @_visitor_recursive
    def visit_FunctionDef(self, node: C.ASTFunctionT) -> None:
        if not relate.first_occurrence(
            node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            if not node.name.startswith("_"):
                self.functions.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef

    @_visitor_recursive
    def visit_Name(self, node: ast.Name) -> None:
        if not relate.first_occurrence(
            node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            if (
                isinstance(node.ctx, ast.Store)
                and (node.id.isupper() or node.id[0].isupper())
                and not node.id.startswith("_")
            ):
                self.variables.add(node.id)

    @_visitor_recursive
    def visit_Assign(self, node: ast.Assign) -> None:
        if getattr(node.targets[0], "id", None) == "__all__" and isinstance(
            node.value, (ast.List, ast.Tuple, ast.Set)
        ):
            for item in node.value.elts:
                if isinstance(item, ast.Constant):
                    self.all.add(str(item.value))
                elif isinstance(item, ast.Str):
                    self.all.add(item.s)

    @_visitor_recursive
    def visit_Expr(self, node: ast.Expr) -> None:
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "__all__"
        ):
            if node.value.func.attr == "append":
                for arg in node.value.args:
                    if isinstance(arg, ast.Constant):
                        self.all.add(str(arg.value))
                    elif isinstance(arg, ast.Str):
                        self.all.add(arg.s)
            elif node.value.func.attr == "extend":
                for arg in node.value.args:
                    if isinstance(arg, ast.List):
                        for item in arg.elts:
                            if isinstance(item, ast.Constant):
                                self.all.add(str(item.value))
                            elif isinstance(item, ast.Str):
                                self.all.add(item.s)


class Analyzer(ast.NodeVisitor):
    def __init__(self, *, source: str):
        self.source = source

        self.all: Set[str] = set()
        self.expected_all: Set[str] = set()

    def traverse(self) -> None:
        tree = ast.parse(self.source)
        relate.relate(tree)
        all_item_analyzer = _AllItemNameAnalyzer()
        all_item_analyzer.visit(tree)
        self.all.update(sorted(all_item_analyzer.all))
        self.expected_all.update(sorted(all_item_analyzer.classes))
        self.expected_all.update(sorted(all_item_analyzer.functions))
        self.expected_all.update(sorted(all_item_analyzer.variables))
