import ast
import functools
import io
import re
import tokenize
from typing import Iterator, Optional, Set, cast

from pyall import constants as C

__all__ = ["Analyzer"]


def _visitor_recursive(func: C.Function) -> C.Function:
    """Decorator to make visitor work recursive."""

    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        func(obj, *args, **kwargs)
        obj.generic_visit(*args)

    return cast(C.Function, wrapper)


def _node_skip(func: C.Function) -> C.Function:
    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        assert (
            len(args) <= 1
        ), "Please don't forget to add the node value as the first parameter."
        node = args[0]
        if not node.skip:
            func(obj, *args, **kwargs)

    return cast(C.Function, wrapper)


def _node_parent_not_class_or_function(func: C.Function) -> C.Function:
    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        assert (
            len(args) <= 1
        ), "Please don't forget to add the node value as the first parameter."
        node = args[0]
        if not Analyzer.first_occurrence(
            node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            func(obj, *args, **kwargs)

    return cast(C.Function, wrapper)


class _AllItemAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.all: Set[str] = set()
        self.classes: Set[str] = set()
        self.functions: Set[str] = set()
        self.variables: Set[str] = set()

    @_node_skip
    @_node_parent_not_class_or_function
    @_visitor_recursive
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if not node.name.startswith("_"):
            self.classes.add(node.name)

    @_node_skip
    @_node_parent_not_class_or_function
    @_visitor_recursive
    def visit_FunctionDef(self, node: C.ASTFunctionT) -> None:
        if not node.name.startswith("_"):
            self.functions.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef

    @_node_skip
    @_node_parent_not_class_or_function
    @_visitor_recursive
    def visit_Name(self, node: ast.Name) -> None:
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


class Analyzer:
    skip_import_comments_regex = "#.*(pyall: {0,1}skip)"

    def __init__(self, *, source: str):
        self.source = source

        self.all: Set[str] = set()
        self.expected_all: Set[str] = set()

    def traverse(self) -> None:
        tree = ast.parse(self.source)
        self.relate(tree)
        self.set_skip_node(tree)
        all_item_analyzer = _AllItemAnalyzer()
        all_item_analyzer.visit(tree)
        self.all.update(sorted(all_item_analyzer.all))
        self.expected_all.update(sorted(all_item_analyzer.classes))
        self.expected_all.update(sorted(all_item_analyzer.functions))
        self.expected_all.update(sorted(all_item_analyzer.variables))

    def set_skip_node(self, tree: ast.AST) -> None:
        skip = set()
        readline = io.StringIO(self.source).readline
        for type_, string, start, end, line in tokenize.generate_tokens(
            readline
        ):
            if re.search(self.skip_import_comments_regex, line, re.IGNORECASE):
                lineno = start[0]
                skip.add(lineno)
        for node in ast.walk(tree):
            if (
                isinstance(
                    node,
                    (
                        ast.ClassDef,
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.Name,
                    ),
                )
                and node.lineno in skip
            ):
                node.skip = True  # type: ignore
            else:
                node.skip = False  # type: ignore

    @staticmethod
    def relate(tree: ast.AST, parent: Optional[ast.AST] = None) -> None:
        tree.parent = parent  # type: ignore
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node  # type: ignore

    @staticmethod
    def get_parents(node: ast.AST) -> Iterator[ast.AST]:
        parent = node
        while parent:
            if parent := parent.parent:  # type: ignore
                yield parent

    @classmethod
    def first_occurrence(cls, node: ast.AST, *ancestors):
        for parent in cls.get_parents(node):
            if isinstance(parent, *ancestors):
                return parent
        else:
            return False
