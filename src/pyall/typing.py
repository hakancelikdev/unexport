import ast
from typing import Any, Callable, TypeVar, Union

__all__ = [
    "Function",
    "ASTFunctionT",
]

Function = TypeVar("Function", bound=Callable[..., Any])
ASTFunctionT = Union[ast.FunctionDef, ast.AsyncFunctionDef]
