import ast
from typing import Any, Callable, TypeVar, Union

__all__ = [
    "ADD_COMMENTS_REGEX_PATTERN",
    "ALL_NODE",
    "DESCRIPTION",
    "EXCLUDE_REGEX_PATTERN",
    "GLOB_PATTERN",
    "INCLUDE_REGEX_PATTERN",
    "SKIP_COMMENTS_REGEX_PATTERN",
    "VERSION",
]

VERSION = "0.2.0"
DESCRIPTION = (
    "Pyall is a linter that tries to keep "
    "the __all __ in your Python modules always up to date."
)

# TYPE
Function = TypeVar("Function", bound=Callable[..., Any])
ASTFunctionT = Union[ast.FunctionDef, ast.AsyncFunctionDef]

# TUPLE
ALL_NODE = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Name)

# REGEX
INCLUDE_REGEX_PATTERN = r"\.(py)$"
EXCLUDE_REGEX_PATTERN = r"^$"
GLOB_PATTERN = r"**/*.py"
SKIP_COMMENTS_REGEX_PATTERN = r"#.*(pyall: {0,1}not-public)"
ADD_COMMENTS_REGEX_PATTERN = r"#.*(pyall: {0,1}public)"
