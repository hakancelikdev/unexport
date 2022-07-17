from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass, field

from pyall import constants as C
from pyall import typing as T
from pyall.relate import relate
from pyall.rule import Rule

__all__ = ["Analyzer"]


@dataclass
class _AllItemAnalyzer(ast.NodeVisitor):
    actual_all: set[str] = field(default_factory=set)
    classes: set[str] = field(default_factory=set)
    functions: set[str] = field(default_factory=set)
    variables: set[str] = field(default_factory=set)

    @Rule.apply
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.add(node.name)

    @Rule.apply
    def visit_FunctionDef(self, node: T.ASTFunctionT) -> None:
        self.functions.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef

    @Rule.apply
    def visit_Name(self, node: ast.Name) -> None:
        self.variables.add(node.id)

    @Rule.apply
    def visit_Assign(self, node: ast.Assign) -> None:
        assert isinstance(node.value, ast.List)
        for item in node.value.elts:
            if isinstance(item, ast.Constant):
                self.actual_all.add(str(item.value))
            elif isinstance(item, ast.Str):
                self.actual_all.add(item.s)

    @Rule.apply
    def visit_Expr(self, node: ast.Expr) -> None:
        assert isinstance(node.value, ast.Call)
        assert isinstance(node.value.func, ast.Attribute)
        if node.value.func.attr == "append":
            for arg in node.value.args:
                if isinstance(arg, ast.Constant):
                    self.actual_all.add(str(arg.value))
                elif isinstance(arg, ast.Str):
                    self.actual_all.add(arg.s)
        elif node.value.func.attr == "extend":
            for arg in node.value.args:
                if isinstance(arg, ast.List):
                    for item in arg.elts:
                        if isinstance(item, ast.Constant):
                            self.actual_all.add(str(item.value))
                        elif isinstance(item, ast.Str):
                            self.actual_all.add(item.s)


@dataclass
class Analyzer:
    source: str
    all_item_analyzer: _AllItemAnalyzer = field(
        init=False, default_factory=_AllItemAnalyzer
    )

    def traverse(self) -> None:
        tree = ast.parse(self.source)
        relate(tree)
        self.set_extra_attr(tree)
        self.all_item_analyzer.visit(tree)

    def set_extra_attr(self, tree: ast.AST) -> None:
        skip, add = set(), set()
        readline = io.StringIO(self.source).readline
        for _, _, start, _, line in tokenize.generate_tokens(readline):
            if re.search(C.SKIP_COMMENTS_REGEX_PATTERN, line, re.IGNORECASE):
                lineno = start[0]
                skip.add(lineno)
            if re.search(C.ADD_COMMENTS_REGEX_PATTERN, line, re.IGNORECASE):
                lineno = start[0]
                add.add(lineno)
        for node in ast.walk(tree):
            if isinstance(node, C.ALL_NODE) and node.lineno in skip:
                node.skip = True  # type: ignore
            else:
                node.skip = False  # type: ignore

            if isinstance(node, C.ALL_NODE) and node.lineno in add:
                node.add = True  # type: ignore

    @property
    def actual_all(self):
        return sorted(self.all_item_analyzer.actual_all)

    @property
    def classes(self):
        return sorted(self.all_item_analyzer.classes)

    @property
    def functions(self):
        return sorted(self.all_item_analyzer.functions)

    @property
    def variables(self):
        return sorted(self.all_item_analyzer.variables)

    @property
    def expected_all(self):
        return sorted(self.classes + self.functions + self.variables)
