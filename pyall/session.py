from pathlib import Path
from typing import Iterator, List, Tuple

from pyall import utils
from pyall.analyzer import Analyzer
from pyall.refactor import refactor_source

__all__ = ["Session"]


class Session:
    @staticmethod
    def get_source(path: Path) -> Iterator[Tuple[str, Path]]:
        for py_path in utils.list_paths(path):
            source = utils.read(py_path)
            yield source, py_path

    @staticmethod
    def get_expected_all(source: str) -> Tuple[bool, List[str]]:
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        action_all = sorted(analyzer.all)
        expected_all = sorted(analyzer.expected_all)
        match = action_all == expected_all
        return match, list(expected_all)

    @classmethod
    def refactor(cls, source: str) -> str:
        match, expected_all = cls.get_expected_all(source)
        if match:
            return source
        else:
            return refactor_source(source, expected_all)
