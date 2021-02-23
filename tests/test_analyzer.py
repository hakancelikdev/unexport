import ast
import textwrap
import unittest

from pyall.analyzer import Analyzer

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
        self.assertSetEqual(analyzer.all, set())
        self.assertSetEqual(analyzer.expected_all, {"TEST_VAR"})

    def test_primitive_variable_has_all(self):
        source = textwrap.dedent(
            """\
                __all__ = ['TEST_VAR']
                TEST_VAR = 1
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertSetEqual(analyzer.all, {"TEST_VAR"})
        self.assertSetEqual(analyzer.expected_all, {"TEST_VAR"})


class AnalyzerFunctionTestCase(unittest.TestCase):
    def test_primitive_function(self):
        source = textwrap.dedent(
            """\
                def function():...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertSetEqual(analyzer.all, set())
        self.assertSetEqual(analyzer.expected_all, {"function"})

    def test_primitive_function_has_all(self):
        source = textwrap.dedent(
            """\
                __all__ = ['function']
                def function():...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertSetEqual(analyzer.all, {"function"})
        self.assertSetEqual(analyzer.expected_all, {"function"})


class AnalyzerClassesTestCase(unittest.TestCase):
    def test_primitive_class(self):
        source = textwrap.dedent(
            """\
                class Klass():...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertSetEqual(analyzer.all, set())
        self.assertSetEqual(analyzer.expected_all, {"Klass"})

    def test_primitive_class_has_all(self):
        source = textwrap.dedent(
            """\
                __all__ = ['Klass']
                class Klass():...
            """
        )
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        self.assertSetEqual(analyzer.all, {"Klass"})
        self.assertSetEqual(analyzer.expected_all, {"Klass"})


class AnalyzerTestCase(unittest.TestCase):
    def test_emty(self):
        analyzer = Analyzer(source="")
        analyzer.traverse()
        self.assertSetEqual(analyzer.all, set())
        self.assertSetEqual(analyzer.expected_all, set())

    def test_tree_analyzer(self):
        source = textwrap.dedent(
            """\
                TEST_SKIP_VAR = 0 # pyall: skip

                TEST_VAR = 1
            """
        )
        analyzer = Analyzer(source=source)
        tree = ast.parse(analyzer.source)
        analyzer.set_skip_node(tree)
        nodes = list(ast.walk(tree))
        self.assertFalse(nodes[0].skip)
        self.assertFalse(nodes[1].skip)
        self.assertFalse(nodes[2].skip)
        self.assertTrue(nodes[3].skip)
        self.assertFalse(nodes[4].skip)
        self.assertFalse(nodes[5].skip)
        self.assertFalse(nodes[6].skip)
        self.assertFalse(nodes[7].skip)
        self.assertFalse(nodes[8].skip)
