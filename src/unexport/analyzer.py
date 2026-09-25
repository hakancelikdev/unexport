from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass, field

from unexport import constants as C
from unexport import typing as T
from unexport.dunder_all import AllStatement, find_all_statements
from unexport.relate import is_bare_annotation, is_runtime_missing, relate
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


@dataclass
class _ModuleBindings:
    """Names bound at module level, of any kind: imports, classes, functions and variables."""

    names: set[str] = field(default_factory=set)
    not_public: set[str] = field(default_factory=set)  # marked with ``# unexport: not-public``
    deleted: set[str] = field(default_factory=set)  # removed with ``del`` after their last binding
    has_star_import: bool = False
    _last_bound: dict[str, int] = field(default_factory=dict, repr=False)
    _last_deleted: dict[str, int] = field(default_factory=dict, repr=False)

    def collect(self, tree: ast.Module) -> None:
        nodes: list[ast.AST] = list(tree.body)
        while nodes:
            node = nodes.pop()
            if is_runtime_missing(node):  # if TYPE_CHECKING: / if __name__ == "__main__":
                continue
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Del):
                self._last_deleted[node.id] = max(node.lineno, self._last_deleted.get(node.id, 0))
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
                for alias in node.names:
                    self._bind((alias.asname or alias.name).split(".")[0], alias)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        self.has_star_import = True
                    else:
                        self._bind(alias.asname or alias.name, alias)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and not is_bare_annotation(node):
                self._bind(node.id, node)
            nodes.extend(ast.iter_child_nodes(node))

        # `del NAME` after the last binding: the name doesn't exist once the module is imported.
        self.deleted = {name for name, line in self._last_deleted.items() if line > self._last_bound.get(name, 0)}
        self.names -= self.deleted

    def _bind(self, name: str, node: ast.AST) -> None:
        self.names.add(name)
        self._last_bound[name] = max(getattr(node, "lineno", 0), self._last_bound.get(name, 0))
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
    all_statements: list[AllStatement] = field(init=False, default_factory=list)

    def traverse(self) -> None:
        try:
            tree = ast.parse(self.source)
        except ValueError as exc:  # null bytes, before Python 3.12 raised them as SyntaxError
            raise SyntaxError(str(exc)) from exc
        relate(tree)
        self.set_extra_attr(tree)
        self.all_item_analyzer.visit(tree)
        self.module_bindings.collect(tree)
        self.all_statements = find_all_statements(tree)
        self.all_item_analyzer.actual_all = {name for statement in self.all_statements for name in statement.names}

    @property
    def is_dynamic_all(self) -> bool:
        """__all__ has parts that can't be read statically (e.g. ``+ sub.__all__``), so it can't be checked."""
        return any(not statement.is_literal for statement in self.all_statements)

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
            elif not isinstance(node, ast.alias):  # set with their import statement below
                node.skip = False  # type: ignore
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:  # the comment can be on the statement or on the imported name's line
                    alias.skip = alias.lineno in skip or node.lineno in skip  # type: ignore

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
        public = (set(self.classes) | set(self.functions) | set(self.variables)) - self.module_bindings.deleted
        # Names that are already listed and still exist are deliberate (re-exports, dunders, ...), keep them.
        listed = {name for name in self.all_item_analyzer.actual_all if self.module_bindings.keeps(name)}
        return sorted(public | listed)
