import textwrap

import pytest

from pyall.session import Session

__all__ = ["test_refactor"]


def _is_equal_source_to_refactor(action: str, expected: str) -> bool:
    expected_source = Session.refactor(source=textwrap.dedent(action))
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
                __all__ = ['KEY', 'Key']

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

                __all__ = ['func']

                def func():...
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

            __all__ = ['t']

            def t():
                import tt
        """,
    ),
]


@pytest.mark.parametrize("action,expected", cases)
def test_refactor(action: str, expected: str):
    assert (
        _is_equal_source_to_refactor(action, expected) is True
    ), "Action source is not equal to after refactoring"
