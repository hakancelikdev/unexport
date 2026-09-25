## Add private name to `__all__`

You can add the private name to `__all__` When you write 'unexport: public' as a
comment.

```python
__all__ = ["name", "_protected_name", "__private_name", "_protected_function", "__private_function", "_ProtectedClass", "__PrivateClass"]

name = ... # unexport: public
_protected_name = ...  # unexport: public
__private_name = ...  # unexport: public

def _protected_function(): ...  # unexport: public
def __private_function(): ...  # unexport: public

class _ProtectedClass: ...  # unexport: public
class __PrivateClass: ...  # unexport: public
```

## Remove public name from `__all__`

You can remove the public name from `__all__` When you write 'unexport: not-public' as a
comment.

```python
PUBLIC_NAME = ...  # unexport: not-public

def public_function(): ...  # unexport: not-public

class PublicClass:...  # unexport: not-public
```

## Type variables

`TypeVar`, `ParamSpec` and `TypeVarTuple` definitions are module-local helpers, so they
are not added to `__all__`. Write 'unexport: public' as a comment to add one anyway.

```python
from typing import TypeVar

T = TypeVar("T")  # not added to __all__
PublicT = TypeVar("PublicT")  # unexport: public
```

## Names you list yourself

Names that are already in `__all__` stay there as long as the module still binds them,
even if unexport would not add them on its own: re-exported imports, dunders such as
`__version__`, lowercase variables or private helpers. Listed names that may exist
without a visible binding are kept as well: when the module has a star import, a module
`__getattr__` (PEP 562), or updates `globals()`, and, in a package's `__init__.py`, the
names of its submodules (`from package import *` imports those). A listed name that no
longer exists, or that is marked `# unexport: not-public` (also on an import, or on one
name of a multi-line import), is removed.

```python
from .core import Api

__all__ = ["Api", "__version__", "helper"]  # all three stay

__version__ = "1.0"

def helper(): ...
```

## How `__all__` is read

`__all__ = [...]`, `__all__: list[str] = [...]`, `__all__ += [...]`,
`__all__.append("x")` and `__all__.extend([...])` (or a tuple) at module level are all
understood. When `__all__` is built from several of these statements, unexport reports
the difference but does not rewrite the file, since changing one statement would list
names twice; update it by hand. When `__all__` has parts that can't be read statically,
such as `["a"] + sub.__all__`, the module is not checked.
