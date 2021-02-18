import ast
from typing import Any, Callable, TypeVar, Union

__all__ = [
    "ASTFunctionT",
    "DESCRIPTION",
    "EXCLUDE_REGEX_PATTERN",
    "Function",
    "GLOB_PATTERN",
    "INCLUDE_REGEX_PATTERN",
    "VERSION",
]

VERSION = "0.1.0"
DESCRIPTION = "Pyall is a linter that tries to keep the __all __ in your Python modules always up to date."

# TYPE
Function = TypeVar("Function", bound=Callable[..., Any])
ASTFunctionT = Union[ast.FunctionDef, ast.AsyncFunctionDef]


INCLUDE_REGEX_PATTERN = r"\.(py)$"
EXCLUDE_REGEX_PATTERN = r"^$"
GLOB_PATTERN = r"**/*.py"
