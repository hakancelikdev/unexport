import ast
from typing import List

__all__ = ["refactor_source"]


def _find_location(source: str) -> int:
    location = 0
    tree = ast.parse(source)
    for node in tree.body:
        if (
            isinstance(node, (ast.Import, ast.ImportFrom))
            and node.lineno > location
        ):
            location = node.lineno
    return location


def _splitlines_no_ff(source):
    # https://github.com/python/cpython/blob/693aeacf8851d1e9995073e27e50644a505dc49c/Lib/ast.py#L296
    """Split a string into lines ignoring form feed and other chars.

    This mimics how the Python parser splits source code.
    """
    idx = 0
    lines = []
    next_line = ""
    while idx < len(source):
        c = source[idx]
        next_line += c
        idx += 1
        # Keep \r\n together
        if c == "\r" and idx < len(source) and source[idx] == "\n":
            next_line += "\n"
            idx += 1
        if c in "\r\n":
            lines.append(next_line)
            next_line = ""

    if next_line:
        lines.append(next_line)
    return lines


def refactor_source(source: str, expected_all: List[str]) -> str:
    if not expected_all:
        return source
    location = _find_location(source)
    lines = _splitlines_no_ff(source)
    lines.insert(location, f"__all__ = {str(expected_all)}\n")
    next_line = lines[location + 1]
    previous_line = lines[location - 1]
    if location == 0 and next_line != "\n":
        lines.insert(location + 1, "\n")
    if next_line == "\n" and previous_line != "\n":
        lines.insert(location, "\n")
    return "".join(lines)
