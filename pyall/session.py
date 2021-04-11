from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Tuple

from pyall import utils
from pyall.analyzer import Analyzer
from pyall.config import Config
from pyall.refactor import refactor_source

__all__ = ["Session"]


@dataclass
class Session:
    config: Config

    def get_source(self, path: Path) -> Iterator[Tuple[str, Path]]:
        for py_path in utils.list_paths(
            path, include=self.config.include, exclude=self.config.exclude
        ):
            source, _ = utils.read(py_path)
            yield source, py_path

    @staticmethod
    def get_expected_all(source: str) -> Tuple[bool, List[str]]:
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        match = analyzer.actual_all == analyzer.expected_all
        return match, analyzer.expected_all

    @classmethod
    def refactor(cls, path: Path, apply: bool = False) -> str:
        source, encoding = utils.read(path)
        _, expected_all = cls.get_expected_all(source)
        new_source = refactor_source(source, expected_all)
        if apply and new_source != source:
            path.write_text(new_source, encoding=encoding)
        return new_source
