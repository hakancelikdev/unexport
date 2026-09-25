from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from unexport import utils
from unexport.analyzer import Analyzer
from unexport.config import Config
from unexport.refactor import refactor_source

__all__ = ("Session",)


@dataclass
class Session:
    config: Config

    def get_source(self, path: Path) -> Iterator[tuple[str | None, Path, str | None]]:
        """Yield (source, path, error) for each file; source is None when the file can't be read."""
        for py_path in utils.list_paths(path, include=self.config.include, exclude=self.config.exclude):
            try:
                source, _, _ = utils.read(py_path)
            except utils.READ_ERRORS as exc:
                yield None, py_path, str(exc)
            else:
                yield source, py_path, None

    @staticmethod
    def get_expected_all(source: str) -> tuple[bool, list[str]]:
        analyzer = Analyzer(source=source)
        analyzer.traverse()
        # A dynamic __all__ (e.g. ``["a"] + sub.__all__``) can't be compared statically; leave it alone.
        match = analyzer.is_dynamic_all or analyzer.actual_all == analyzer.expected_all
        return match, analyzer.expected_all

    @classmethod
    def refactor(cls, path: Path, apply: bool = False) -> str:
        source, encoding, newline = utils.read(path)
        _, expected_all = cls.get_expected_all(source)
        new_source = refactor_source(source, expected_all)
        if apply and new_source != source:
            with path.open("w", encoding=encoding, newline=newline) as file:
                file.write(new_source)
        return new_source
