import ast
import sys
import textwrap
import unittest

from unexport.analyzer import Analyzer

__all__ = [
    "AnalyzerClassesTestCase",
    "AnalyzerFunctionTestCase",
    "AnalyzerAllFormsTestCase",
    "AnalyzerListedNamesTestCase",
    "AnalyzerRuntimeNamesTestCase",
    "AnalyzerPEP695TestCase",
    "AnalyzerPEP696TestCase",
    "AnalyzerPython314TestCase",
    "AnalyzerTestCase",
    "AnalyzerVariableTestCase",
]


class AnalyzerVariableTestCase(unittest.TestCase):
    def test_primitive_variable(self):
        source = textwrap.dedent(
            """\
                TEST_VAR = 1
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertFalse(analyzer.actual_all)
        self.assertListEqual(analyzer.expected_all, ["TEST_VAR"])

    def test_primitive_variable_has_all(self):
        source = textwrap.dedent(
            """\
                __all__ = ['TEST_VAR']
                TEST_VAR = 1
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.actual_all, ["TEST_VAR"])
        self.assertListEqual(analyzer.expected_all, ["TEST_VAR"])

    def test_not_public_comment(self):
        source = textwrap.dedent(
            """\
                TEST_VAR = 1 # unexport: not-public
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertFalse(analyzer.actual_all)
        self.assertFalse(analyzer.expected_all)

    def test_type_var_is_not_public(self):
        source = textwrap.dedent(
            """\
                import typing
                from typing import ParamSpec, TypeVar, TypeVarTuple

                T = TypeVar("T")
                P = ParamSpec("P")
                Ts = TypeVarTuple("Ts")
                K = typing.TypeVar("K", bound=str)
                V: typing.TypeVar = typing.TypeVar("V")
                A, (B, [C]) = TypeVar("A"), (TypeVar("B"), [TypeVar("C")])
                Pair, Name = TypeVar("Pair"), "a string"

                def func():
                    pass
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertFalse(analyzer.actual_all)
        self.assertListEqual(analyzer.expected_all, ["Name", "func"])

    def test_type_var_public_comment(self):
        source = textwrap.dedent(
            """\
                from typing import TypeVar

                T = TypeVar("T")  # unexport: public
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.expected_all, ["T"])

    def test_other_call_is_public(self):
        source = textwrap.dedent(
            """\
                from typing import NewType

                UserId = NewType("UserId", int)
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.expected_all, ["UserId"])


class AnalyzerFunctionTestCase(unittest.TestCase):
    def test_primitive_function(self):
        source = textwrap.dedent(
            """\
                def function():...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertFalse(analyzer.actual_all)
        self.assertListEqual(analyzer.expected_all, ["function"])

    def test_primitive_function_has_all(self):
        source = textwrap.dedent(
            """\
                __all__ = ['function']
                def function():...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.actual_all, ["function"])
        self.assertListEqual(analyzer.expected_all, ["function"])


class AnalyzerClassesTestCase(unittest.TestCase):
    def test_primitive_class(self):
        source = textwrap.dedent(
            """\
                class Klass():...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertFalse(analyzer.actual_all)
        self.assertListEqual(analyzer.expected_all, ["Klass"])

    def test_primitive_class_has_all(self):
        source = textwrap.dedent(
            """\
                __all__ = ['Klass']
                class Klass():...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.actual_all, ["Klass"])
        self.assertListEqual(analyzer.expected_all, ["Klass"])


class AnalyzerTestCase(unittest.TestCase):
    def test_name_defined_twice_is_listed_once(self):
        source = textwrap.dedent(
            """\
                class Point: ...

                Point = Point

                def Factory(): ...

                Factory = Factory
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.expected_all, ["Factory", "Point"])

    def test_emty(self):
        analyzer = Analyzer(source="")
        analyzer.traverse()
        self.assertFalse(analyzer.actual_all)
        self.assertFalse(analyzer.expected_all)

    def test_set_extra_attr(self):
        source = textwrap.dedent(
            """\
                TEST_SKIP_VAR = 0 # unexport: not-public

                TEST_VAR = 1 # unexport: public
            """
        )
        analyzer = Analyzer(source=source)
        tree = ast.parse(analyzer.source)
        analyzer.set_extra_attr(tree)
        nodes = list(ast.walk(tree))
        self.assertFalse(nodes[0].skip)
        self.assertFalse(nodes[1].skip)
        self.assertFalse(nodes[2].skip)

        self.assertTrue(nodes[3].skip)
        self.assertIsInstance(nodes[3], ast.Name)
        self.assertEqual(nodes[3].id, "TEST_SKIP_VAR")

        self.assertFalse(nodes[4].skip)
        self.assertFalse(nodes[5].skip)
        self.assertFalse(nodes[6].skip)
        self.assertFalse(nodes[7].skip)
        self.assertFalse(nodes[8].skip)


class AnalyzerAllFormsTestCase(unittest.TestCase):
    """How __all__ is read (issue 41)."""

    def analyze(self, source: str) -> Analyzer:
        analyzer = Analyzer(source=textwrap.dedent(source))
        analyzer.traverse()
        return analyzer

    def test_imported_or_unpacked_all_is_dynamic(self):
        for source in (
            "from io import __all__\nclass Extra: ...\n",
            "from io import (__all__, SEEK_SET)\nclass Extra: ...\n",
            "import names as __all__\nclass Extra: ...\n",
            "__all__, VERSION = ['Extra'], 1\nclass Extra: ...\nclass Other: ...\n",
        ):
            with self.subTest(source=source):
                self.assertTrue(self.analyze(source).is_dynamic_all)

    def test_augmented_annotated_and_extend_tuple(self):
        analyzer = self.analyze(
            """\
                __all__: list[str] = ["a"]
                __all__ += ["b"]
                __all__.extend(("c",))
                __all__.append("d")

                def a(): ...
                def b(): ...
                def c(): ...
                def d(): ...
            """
        )
        self.assertListEqual(analyzer.actual_all, ["a", "b", "c", "d"])
        self.assertListEqual(analyzer.actual_all, analyzer.expected_all)
        self.assertFalse(analyzer.is_dynamic_all)

    def test_dynamic_parts(self):
        for source in (
            '__all__ = ["a"] + sub.__all__\n',
            '__all__ = ["a"]\n__all__.extend(sub.__all__)\n',
            '__all__ = ["a", "b"]\n__all__.remove("b")\n',
        ):
            with self.subTest(source=source):
                self.assertTrue(self.analyze(source).is_dynamic_all)

    def test_all_inside_a_function_is_ignored(self):
        analyzer = self.analyze(
            """\
                def setup():
                    __all__ = ["nothing"]
            """
        )
        self.assertListEqual(analyzer.actual_all, [])


class AnalyzerListedNamesTestCase(unittest.TestCase):
    """Names already listed in __all__ stay when the module still binds them (issue 39)."""

    def expected_all(self, source: str) -> list[str]:
        analyzer = Analyzer(source=textwrap.dedent(source))
        analyzer.traverse()
        return analyzer.expected_all

    def test_reexported_imports_are_kept(self):
        source = """\
            import os.path
            from .core import Api
            from .models import User as Account

            __all__ = ["Account", "Api", "helper", "os"]

            def helper(): ...
        """
        self.assertListEqual(self.expected_all(source), ["Account", "Api", "helper", "os"])

    def test_imports_are_not_added(self):
        source = """\
            from .core import Api

            def helper(): ...
        """
        self.assertListEqual(self.expected_all(source), ["helper"])

    def test_listed_lowercase_and_dunder_names_are_kept(self):
        source = """\
            __all__ = ["__version__", "logger", "_helper"]

            __version__ = "1.0"
            logger = object()

            def _helper(): ...
        """
        self.assertListEqual(self.expected_all(source), ["__version__", "_helper", "logger"])

    def test_listed_but_not_public_is_removed(self):
        source = """\
            __all__ = ["Hidden"]

            Hidden = 1  # unexport: not-public
        """
        self.assertListEqual(self.expected_all(source), [])

    def test_listed_but_not_public_import_is_removed(self):
        source = """\
            import os  # unexport: not-public
            from .core import Api, Hidden  # unexport: not-public
            from .models import (
                User,
                Group,  # unexport: not-public
            )

            __all__ = ["Api", "Group", "Hidden", "User", "os"]
        """
        self.assertListEqual(self.expected_all(source), ["User"])

    def test_listed_but_undefined_is_removed(self):
        source = """\
            __all__ = ["gone", "func"]

            def func(): ...
        """
        self.assertListEqual(self.expected_all(source), ["func"])

    def test_star_import_keeps_unresolved_names(self):
        source = """\
            from .models import *

            __all__ = ["User"]
        """
        self.assertListEqual(self.expected_all(source), ["User"])

    def test_names_local_to_functions_or_comprehensions_are_not_bindings(self):
        source = """\
            __all__ = ["inner", "item"]

            def func():
                inner = 1

            VALUES = [item for item in range(3)]
        """
        self.assertListEqual(self.expected_all(source), ["VALUES", "func"])


class AnalyzerRuntimeNamesTestCase(unittest.TestCase):
    """Names that don't exist when the module is imported are not exported (issue 40)."""

    def expected_all(self, source: str) -> list[str]:
        analyzer = Analyzer(source=textwrap.dedent(source))
        analyzer.traverse()
        return analyzer.expected_all

    def test_deleted_name(self):
        source = """\
            TEMP = 1
            del TEMP
            KEPT = 1
        """
        self.assertListEqual(self.expected_all(source), ["KEPT"])

    def test_bare_annotation(self):
        source = """\
            __all__ = ["Declared", "Assigned"]

            Declared: int
            Assigned: int = 1
            Later: str
            Later = "set later"
        """
        self.assertListEqual(self.expected_all(source), ["Assigned", "Later"])

    def test_deleted_on_the_same_line(self):
        source = """\
            TEMP = 1; del TEMP
            KEPT = 1; del KEPT; KEPT = 2
        """
        self.assertListEqual(self.expected_all(source), ["KEPT"])

    def test_constant_false_branches(self):
        source = """\
            from typing import TYPE_CHECKING

            if False:
                class Never: ...
            if 0:
                Zero = 1
            if True:
                Always = 1
            else:
                Otherwise = 1
            if not TYPE_CHECKING:
                Runtime = 1
            else:
                Checking = 1
        """
        self.assertListEqual(self.expected_all(source), ["Always", "Runtime"])

    def test_walrus_in_lambda(self):
        source = """\
            handler = lambda: (Value := 1)
            Real = 1
        """
        self.assertListEqual(self.expected_all(source), ["Real"])

    def test_rebound_after_del(self):
        source = """\
            VALUE = 1
            del VALUE
            VALUE = 2
        """
        self.assertListEqual(self.expected_all(source), ["VALUE"])

    def test_type_checking_block(self):
        source = """\
            import typing
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                Alias = int
                class Stub: ...
            else:
                Runtime = int

            if typing.TYPE_CHECKING:
                Other = int
        """
        self.assertListEqual(self.expected_all(source), ["Runtime"])

    def test_main_guard(self):
        source = """\
            def main(): ...

            if __name__ == "__main__":
                RESULT = main()

            if "__main__" == __name__:
                OTHER = main()
        """
        self.assertListEqual(self.expected_all(source), ["main"])

    def test_comprehension_targets(self):
        source = """\
            VALUES = [Item for Item in range(3)]
            PAIRS = {Key: Value for Key, Value in []}
            FIRST = [(Last := x) for x in range(3)]
        """
        # a walrus inside a comprehension binds at module level
        self.assertListEqual(self.expected_all(source), ["FIRST", "Last", "PAIRS", "VALUES"])

    def test_public_comment_still_forces(self):
        source = """\
            if TYPE_CHECKING:
                Alias = int  # unexport: public
        """
        self.assertListEqual(self.expected_all(source), ["Alias"])

    def test_listed_names_that_do_not_exist_are_removed(self):
        source = """\
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from x import Y

            import os
            del os

            __all__ = ["Y", "os", "func"]

            def func(): ...
        """
        self.assertListEqual(self.expected_all(source), ["func"])


@unittest.skipIf(sys.version_info < (3, 12), "PEP 695 syntax requires Python 3.12+")
class AnalyzerPEP695TestCase(unittest.TestCase):
    def test_type_alias(self):
        source = textwrap.dedent(
            """\
                type Point = tuple[float, float]
                type _Private = int
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertFalse(analyzer.actual_all)
        self.assertListEqual(analyzer.expected_all, ["Point"])

    def test_type_alias_not_public_comment(self):
        source = textwrap.dedent(
            """\
                type Point = tuple[float, float]  # unexport: not-public
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertFalse(analyzer.expected_all)

    def test_generic_type_alias(self):
        source = textwrap.dedent(
            """\
                type Pair[T] = tuple[T, T]
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.expected_all, ["Pair"])

    def test_generic_function_and_class(self):
        source = textwrap.dedent(
            """\
                def first[T](items: list[T]) -> T:
                    return items[0]

                class Box[T]:
                    VALUE: T

                    def get[K](self) -> K: ...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.expected_all, ["Box", "first"])


@unittest.skipIf(sys.version_info < (3, 13), "PEP 696 syntax requires Python 3.13+")
class AnalyzerPEP696TestCase(unittest.TestCase):
    def test_type_parameter_defaults(self):
        source = textwrap.dedent(
            """\
                type Alias[T = int] = list[T]

                def first[T = str](items: list[T]) -> T:
                    return items[0]

                class Box[*Ts = *tuple[int]]: ...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.expected_all, ["Alias", "Box", "first"])


@unittest.skipIf(sys.version_info < (3, 14), "Python 3.14+ syntax")
class AnalyzerPython314TestCase(unittest.TestCase):
    def test_template_string(self):
        source = textwrap.dedent(
            """\
                NAME = "world"
                GREETING = t"Hello {NAME}"
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.expected_all, ["GREETING", "NAME"])

    def test_except_without_parentheses(self):
        source = textwrap.dedent(
            """\
                try:
                    VALUE = int("x")
                except ValueError, TypeError:
                    VALUE = 0
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.expected_all, ["VALUE"])

    def test_deferred_annotations(self):
        source = textwrap.dedent(
            """\
                def build() -> Later: ...

                class Later: ...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertListEqual(analyzer.expected_all, ["Later", "build"])
