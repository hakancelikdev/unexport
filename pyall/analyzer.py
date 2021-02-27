import ast
import io
import re
import tokenize
from typing import Set

from pyall import constants as C
from pyall.relate import relate
from pyall.rules import Rule

__all__ = ["Analyzer"]


class _AllItemAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.all: Set[str] = set()
        self.classes: Set[str] = set()
        self.functions: Set[str] = set()
        self.variables: Set[str] = set()

    @Rule.apply_rules
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.add(node.name)
        self.generic_visit(node)

    @Rule.apply_rules
    def visit_FunctionDef(self, node: C.ASTFunctionT) -> None:
        self.functions.add(node.name)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    @Rule.apply_rules
    def visit_Name(self, node: ast.Name) -> None:
        self.variables.add(node.id)
        self.generic_visit(node)

    @Rule.apply_rules
    def visit_Assign(self, node: ast.Assign) -> None:
        for item in node.value.elts:
            if isinstance(item, ast.Constant):
                self.all.add(str(item.value))
            elif isinstance(item, ast.Str):
                self.all.add(item.s)
        self.generic_visit(node)

    @Rule.apply_rules
    def visit_Expr(self, node: ast.Expr) -> None:
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
        self.generic_visit(node)


class Analyzer:
    def __init__(self, *, source: str):
        self.source = source

        self.all: Set[str] = set()
        self.expected_all: Set[str] = set()

    def traverse(self) -> None:
        tree = ast.parse(self.source)
        relate(tree)
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
            if re.search(
                C.SKIP_IMPORT_COMMENTS_REGEX_PATTERN, line, re.IGNORECASE
            ):
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
