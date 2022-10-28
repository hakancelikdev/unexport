import unittest
from pathlib import Path

from pyall import constants as C
from pyall import utils

__all__ = ["UtilsTestCase"]


class UtilsTestCase(unittest.TestCase):
    def test_list_paths(self):
        self.assertEqual(len(list(utils.list_paths(Path("tests/test_utils.py")))), 1)
        test_file_count = len(list(Path("tests").glob(C.GLOB_PATTERN)))
        self.assertEqual(len(list(utils.list_paths(Path("tests")))), test_file_count)
