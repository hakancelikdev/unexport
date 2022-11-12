import os
import tempfile
import textwrap
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

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
            __all__ = ["x"]

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
    (
        """\
            from typing import TypeVar

            T = TypeVar("T")
        """,
        """\
            from typing import TypeVar

            T = TypeVar("T")
        """,
    ),
    (
        """\
            from typing import TypeVar

            T = TypeVar("T")

            def func():
                pass
        """,
        """\
            from typing import TypeVar

            __all__ = ["func"]

            T = TypeVar("T")

            def func():
                pass
        """,
    ),
    (
        """\
            import typing

            T = typing.TypeVar("T")
        """,
        """\
            import typing

            T = typing.TypeVar("T")
        """,
    ),
    (
        """\
            class TypeVar:
                def __init__(self, name):...
                
            T = TypeVar("T")
        """,
        """\
            __all__ = ["T", "TypeVar"]
            
            class TypeVar:
                def __init__(self, name):...
                
            T = TypeVar("T")
        """,
    )
]


@pytest.mark.parametrize("action,expected", cases)
def test_refactor(action: str, expected: str):
    assert _is_equal_source_to_refactor(action, expected) is True, "Action source is not equal to after refactoring"
