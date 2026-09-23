from __future__ import annotations

import ast

__all__ = ("refactor_source",)


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


def _replace_node(lines: list[str], node: ast.expr, text: str) -> None:
    # AST column offsets are UTF-8 byte offsets.
    start, end = node.lineno - 1, (node.end_lineno or node.lineno) - 1
    prefix = lines[start].encode()[: node.col_offset].decode()
    suffix = lines[end].encode()[node.end_col_offset :].decode()
    lines[start : end + 1] = [prefix + text + suffix]


def _format_all(expected_all: list[str]) -> str:
    return str(expected_all).replace("'", '"')


def refactor_source(source: str, expected_all: list[str]) -> str:
    if not expected_all:
        return source
    tree = ast.parse(source)
    lines = ast._splitlines_no_ff(source)  # type: ignore

    if all_node := _find_all_node(tree):
        _replace_node(lines, all_node.value, _format_all(expected_all))
        return "".join(lines)

    start = _find_insert_line(tree)
    lines.insert(start, f"__all__ = {_format_all(expected_all)}\n")

    next_line = lines[start + 1]
    previous_line = lines[start - 1]
    if next_line != "\n":
        lines.insert(start + 1, "\n")
    if start != 0 and previous_line != "\n":
        lines.insert(start, "\n")
    return "".join(lines)
