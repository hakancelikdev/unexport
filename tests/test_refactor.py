import os
import tempfile
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from unexport.session import Session

__all__ = ["reopenable_temp_file", "test_refactor"]


@contextmanager
def reopenable_temp_file(content: str) -> Iterator[Path]:
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", encoding="utf-8", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(content)
        yield tmp_path
    finally:
        os.unlink(tmp_path)


def _is_equal_source_to_refactor(action: str, expected: str) -> bool:
    source = textwrap.dedent(action)
    with reopenable_temp_file(source) as tmp:
        expected_source = Session.refactor(path=tmp, apply=False)
        return textwrap.dedent(expected) == expected_source


cases = [
    (
        """\
        """,
        """\
        """,
    ),
    (
        """\
                key = "value"
                _key = "_value"
                Key = "Value"
                KEY = "VALUE"
        """,
        """\
                __all__ = ["KEY", "Key"]

                key = "value"
                _key = "_value"
                Key = "Value"
                KEY = "VALUE"
        """,
    ),
    (
        """\
                import x

                def func():...
        """,
        """\
                import x

                __all__ = ["func"]

                def func():...
        """,
    ),
    (
        """\
                __all__ = ("var",)
                
                var = 1
        """,
        """\
                __all__ = ("var",)
                
                var = 1
        """,
    ),
    (
        """\
            from x import xx

            import y

            def t():
                import tt
        """,
        """\
            from x import xx

            import y

            __all__ = ["t"]

            def t():
                import tt
        """,
    ),
    (  # import & start != 0
        """\
            import x

            __all__ = ["test"]

            def test():...

            def f():...
        """,
        """\
            import x

            __all__ = ["f", "test"]

            def test():...

            def f():...
        """,
    ),
    (  # start == 0
        """\
            __all__ = ["test"]

            def test():...

            def f():...
        """,
        """\
            __all__ = ["f", "test"]

            def test():...

            def f():...
        """,
    ),
    (
        """\
            __all__ = [
                "x",
                "y",
                "z",
                "s",
            ]

            def x():...

        """,
        """\
            __all__ = [
                "x",
            ]

            def x():...

        """,
    ),
    (
        """\
            __all__ = ["x"]

            x = 1  # unexport: public
        """,
        """\
            __all__ = ["x"]

            x = 1  # unexport: public
        """,
    ),
    (
        """\
            __all__ = []

            XXX = 1  # unexport: not-public
        """,
        """\
            __all__ = []

            XXX = 1  # unexport: not-public
        """,
    ),
    (  # issue 7: keep the trailing comment
        """\
            __all__ = []  # comments

            def a():...
        """,
        """\
            __all__ = ["a"]  # comments

            def a():...
        """,
    ),
    (  # keep the comment after a multi-line __all__
        """\
            __all__ = [
                "a",
            ]  # public api

            def a():...

            def b():...
        """,
        """\
            __all__ = [
                "a",
                "b",
            ]  # public api

            def a():...

            def b():...
        """,
    ),
    (  # only the value is replaced, other code on the same line is kept
        """\
            NAME = "ş"; __all__ = []; OTHER = 1
        """,
        """\
            NAME = "ş"; __all__ = ["NAME", "OTHER"]; OTHER = 1
        """,
    ),
    (  # the target and the spacing around "=" are kept
        """\
            import x

            __all__=("a",)

            def a():...

            def b():...
        """,
        """\
            import x

            __all__=("a", "b")

            def a():...

            def b():...
        """,
    ),
    (  # issue 22: keep a tuple
        """\
            __all__ = ("a", "b")

            def c():...
        """,
        """\
            __all__ = ("c",)

            def c():...
        """,
    ),
    (  # issue 22: keep a set
        """\
            __all__ = {"a"}

            def b():...

            def c():...
        """,
        """\
            __all__ = {"b", "c"}

            def b():...

            def c():...
        """,
    ),
    (  # issue 22: split a long __all__ into one name per line
        """\
            __all__ = []

            def first_public_function_name():...
            def second_public_function_name():...
            def third_public_function_name():...
        """,
        """\
            __all__ = [
                "first_public_function_name",
                "second_public_function_name",
                "third_public_function_name",
            ]

            def first_public_function_name():...
            def second_public_function_name():...
            def third_public_function_name():...
        """,
    ),
    (  # issue 22: split a long new __all__ into one name per line
        """\
            import x

            def first_public_function_name():...
            def second_public_function_name():...
            def third_public_function_name():...
        """,
        """\
            import x

            __all__ = [
                "first_public_function_name",
                "second_public_function_name",
                "third_public_function_name",
            ]

            def first_public_function_name():...
            def second_public_function_name():...
            def third_public_function_name():...
        """,
    ),
    (  # issue 39: re-exported imports stay in __all__
        """\
            from .core import Api

            __all__ = ["Api"]

            def helper(): ...
        """,
        """\
            from .core import Api

            __all__ = ["Api", "helper"]

            def helper(): ...
        """,
    ),
    (  # issue 45: a stale __all__ becomes empty
        """\
            __all__ = ["gone"]

            _private = 1
        """,
        """\
            __all__ = []

            _private = 1
        """,
    ),
    (  # issue 45: keep the tuple form, even when it was multi-line
        """\
            __all__ = (
                "gone",
            )
        """,
        """\
            __all__ = ()
        """,
    ),
    (  # no __all__ and nothing public: unchanged
        """\
            _private = 1
        """,
        """\
            _private = 1
        """,
    ),
    (  # issue 42: after the module docstring
        """\
            \"\"\"Module docstring.\"\"\"


            def func(): ...
        """,
        """\
            \"\"\"Module docstring.\"\"\"

            __all__ = ["func"]


            def func(): ...
        """,
    ),
    (  # issue 42: after a multi-line docstring
        """\
            \"\"\"Module docstring.

            More text.
            \"\"\"
            def func(): ...
        """,
        """\
            \"\"\"Module docstring.

            More text.
            \"\"\"

            __all__ = ["func"]

            def func(): ...
        """,
    ),
    (  # issue 42: docstring and __future__ import, after the import
        """\
            \"\"\"Doc.\"\"\"
            from __future__ import annotations

            def func(): ...
        """,
        """\
            \"\"\"Doc.\"\"\"
            from __future__ import annotations

            __all__ = ["func"]

            def func(): ...
        """,
    ),
    (  # issue 42: shebang and encoding lines stay first
        """\
            #!/usr/bin/env python
            # -*- coding: utf-8 -*-
            def func(): ...
        """,
        """\
            #!/usr/bin/env python
            # -*- coding: utf-8 -*-

            __all__ = ["func"]

            def func(): ...
        """,
    ),
    (  # issue 41: an annotated __all__ is updated in place
        """\
            __all__: list[str] = ["func"]

            def func(): ...

            def other(): ...
        """,
        """\
            __all__: list[str] = ["func", "other"]

            def func(): ...

            def other(): ...
        """,
    ),
    (  # issue 41: __all__ built from several statements is not rewritten
        """\
            __all__ = ["a"]
            __all__ += ["b"]

            def a(): ...
            def b(): ...
            def c(): ...
        """,
        """\
            __all__ = ["a"]
            __all__ += ["b"]

            def a(): ...
            def b(): ...
            def c(): ...
        """,
    ),
    (  # issue 41: a dynamic __all__ is left alone
        """\
            from . import sub

            __all__ = ["func"] + sub.__all__

            def func(): ...
            def other(): ...
        """,
        """\
            from . import sub

            __all__ = ["func"] + sub.__all__

            def func(): ...
            def other(): ...
        """,
    ),
    (  # an empty set __all__ stays a set
        """\
            __all__ = {"removed"}

            def _private(): ...
        """,
        """\
            __all__ = set()

            def _private(): ...
        """,
    ),
    (  # the last top-level statement is an import
        "X = 1\nimport os\n",
        'X = 1\nimport os\n\n__all__ = ["X"]\n',
    ),
    (  # ... without a trailing newline
        "X = 1\nimport os",
        'X = 1\nimport os\n\n__all__ = ["X"]\n',
    ),
    (  # an imported __all__ is left alone, not overridden by a new one
        """\
            from io import *
            from io import __all__

            class Extra: ...
        """,
        """\
            from io import *
            from io import __all__

            class Extra: ...
        """,
    ),
]


@pytest.mark.parametrize("action,expected", cases)
def test_refactor(action: str, expected: str):
    assert _is_equal_source_to_refactor(action, expected) is True, "Action source is not equal to after refactoring"
