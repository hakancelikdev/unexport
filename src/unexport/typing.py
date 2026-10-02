import ast
from collections.abc import Callable
from typing import Any, TypeVar, Union

__all__ = (
    "Function",
    "ASTFunctionT",
)

Function = TypeVar("Function", bound=Callable[..., Any])  # unexport: public
ASTFunctionT = Union[ast.FunctionDef, ast.AsyncFunctionDef]
