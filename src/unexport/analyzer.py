from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass, field

from unexport import constants as C
from unexport import typing as T
from unexport.relate import relate
from unexport.rule import Rule

__all__ = ("Analyzer",)


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
        assert isinstance(node.value, (ast.List, ast.Tuple, ast.Set))
        for item in node.value.elts:
            if isinstance(item, ast.Constant):
                self.actual_all.add(str(item.value))

    @Rule.apply
    def visit_Expr(self, node: ast.Expr) -> None:
        assert isinstance(node.value, ast.Call)
        assert isinstance(node.value.func, ast.Attribute)
        if node.value.func.attr == "append":
            for arg in node.value.args:
                if isinstance(arg, ast.Constant):
                    self.actual_all.add(str(arg.value))
        elif node.value.func.attr == "extend":
            for arg in node.value.args:
                if isinstance(arg, ast.List):
                    for item in arg.elts:
                        if isinstance(item, ast.Constant):
                            self.actual_all.add(str(item.value))


@dataclass
class _ModuleBindings:
    """Names bound at module level, of any kind: imports, classes, functions and variables."""

    names: set[str] = field(default_factory=set)
    not_public: set[str] = field(default_factory=set)  # marked with ``# unexport: not-public``
    has_star_import: bool = False

    def collect(self, tree: ast.Module) -> None:
        nodes: list[ast.AST] = list(tree.body)
        while nodes:
            node = nodes.pop()
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self._bind(node.name, node)
                nodes.extend(node.decorator_list)  # the body is a nested scope
                continue
            if isinstance(node, ast.Lambda):
                continue
            if isinstance(node, ast.comprehension):
                nodes.extend([node.iter, *node.ifs])  # the target is local to the comprehension
                continue
            if isinstance(node, ast.Import):
                self.names.update((alias.asname or alias.name).split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        self.has_star_import = True
                    else:
                        self.names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                self._bind(node.id, node)
            nodes.extend(ast.iter_child_nodes(node))

    def _bind(self, name: str, node: ast.AST) -> None:
        self.names.add(name)
        if getattr(node, "skip", False):
            self.not_public.add(name)

    def keeps(self, name: str) -> bool:
        """Whether a name that is already listed in __all__ stays there.

        It does when the module binds it (a re-exported import, a dunder
        or a lowercase variable that unexport would not add on its own),
        or when a star import might provide it.
        """
        if name in self.not_public:
            return False
        return name in self.names or self.has_star_import


@dataclass
class Analyzer:
    source: str
    all_item_analyzer: _AllItemAnalyzer = field(init=False, default_factory=_AllItemAnalyzer)
    module_bindings: _ModuleBindings = field(init=False, default_factory=_ModuleBindings)

    def traverse(self) -> None:
        tree = ast.parse(self.source)
        relate(tree)
        self.set_extra_attr(tree)
        self.all_item_analyzer.visit(tree)
        self.module_bindings.collect(tree)

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
        # A name can be both a class/function and a variable (e.g. ``Point = Point``); list it once.
        public = set(self.classes) | set(self.functions) | set(self.variables)
        # Names that are already listed and still exist are deliberate (re-exports, dunders, ...), keep them.
        listed = {name for name in self.all_item_analyzer.actual_all if self.module_bindings.keeps(name)}
        return sorted(public | listed)
