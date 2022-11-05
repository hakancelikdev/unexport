import ast
import textwrap
import unittest

from unexport.analyzer import Analyzer

__all__ = [
    "AnalyzerClassesTestCase",
    "AnalyzerFunctionTestCase",
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
