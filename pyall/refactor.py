import ast
from typing import List, NamedTuple

__all__ = ["refactor_source"]


class _Location(NamedTuple):
    start: int = 0
    end: int = 0
    all_exists: bool = False


def _find_location(source: str) -> _Location:
    location = _Location()
    tree = ast.parse(source)
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and getattr(node.targets[0], "id", None) == "__all__"
        ):
            return location._replace(
                start=node.lineno - 1, end=node.end_lineno, all_exists=True
            )
        elif (
            isinstance(node, (ast.Import, ast.ImportFrom))
            and node.lineno > location.start
        ):
            location = location._replace(start=node.end_lineno)
    return location


def refactor_source(source: str, expected_all: List[str]) -> str:
    if not expected_all:
        return source
    location = _find_location(source)
    lines = ast._splitlines_no_ff(source)  # type: ignore

    if location.all_exists:
        if location.start != location.end:
            del lines[location.start : location.end]
        else:
            del lines[location.start]
        lines.insert(location.start, f"__all__ = {str(expected_all)}\n")
    else:
        lines.insert(location.start, f"__all__ = {str(expected_all)}\n")
    next_line = lines[location.start + 1]
    previous_line = lines[location.start - 1]
    if next_line != "\n":
        lines.insert(location.start + 1, "\n")
    if location.start != 0 and previous_line != "\n":
        lines.insert(location.start, "\n")
    return "".join(lines)
