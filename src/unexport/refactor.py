from __future__ import annotations

import ast

__all__ = ("refactor_source",)

_MAX_LINE_LENGTH = 88
_INDENT = " " * 4
_BRACKETS = {ast.List: ("[", "]"), ast.Tuple: ("(", ")"), ast.Set: ("{", "}")}


def _find_all_node(tree: ast.Module) -> ast.Assign | None:
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "__all__":
            return node
    return None


def _find_insert_line(tree: ast.Module) -> int:
    start = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node.lineno > start:
            start = node.end_lineno or 0
    return start


def _format_all(
    expected_all: list[str],
    brackets: tuple[str, str] = ("[", "]"),
    multiline: bool = False,
    indent: str = "",
) -> str:
    items = [f'"{name}"' for name in expected_all]
    opening, closing = brackets
    if multiline:
        body = "".join(f"{indent}{_INDENT}{item},\n" for item in items)
        return f"{opening}\n{body}{indent}{closing}"
    trailing_comma = "," if opening == "(" and len(items) == 1 else ""
    return f"{opening}{', '.join(items)}{trailing_comma}{closing}"


def _replace_value(lines: list[str], node: ast.expr, expected_all: list[str]) -> None:
    # AST column offsets are UTF-8 byte offsets.
    start, end = node.lineno - 1, (node.end_lineno or node.lineno) - 1
    prefix = lines[start].encode()[: node.col_offset].decode()
    suffix = lines[end].encode()[node.end_col_offset :].decode()
    brackets = _BRACKETS.get(type(node), ("[", "]"))
    text = _format_all(expected_all, brackets)
    if start != end or len(prefix + text + suffix.rstrip("\r\n")) > _MAX_LINE_LENGTH:
        indent = prefix[: len(prefix) - len(prefix.lstrip())]
        text = _format_all(expected_all, brackets, multiline=True, indent=indent)
    lines[start : end + 1] = [prefix + text + suffix]


def refactor_source(source: str, expected_all: list[str]) -> str:
    if not expected_all:
        return source
    tree = ast.parse(source)
    lines = ast._splitlines_no_ff(source)  # type: ignore

    if all_node := _find_all_node(tree):
        _replace_value(lines, all_node.value, expected_all)
        return "".join(lines)

    start = _find_insert_line(tree)
    refactored_all = f"__all__ = {_format_all(expected_all)}"
    if len(refactored_all) > _MAX_LINE_LENGTH:
        refactored_all = f"__all__ = {_format_all(expected_all, multiline=True)}"
    lines.insert(start, refactored_all + "\n")

    next_line = lines[start + 1]
    previous_line = lines[start - 1]
    if next_line != "\n":
        lines.insert(start + 1, "\n")
    if start != 0 and previous_line != "\n":
        lines.insert(start, "\n")
    return "".join(lines)
