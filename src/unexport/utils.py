from __future__ import annotations

import difflib
import re
import tokenize
from pathlib import Path
from typing import Iterable, Iterator

from unexport import constants as C

__all__ = ("diff", "list_paths", "read")


def read(path: Path) -> tuple[str, str]:
    try:
        with tokenize.open(path) as stream:
            source = stream.read()
            encoding = stream.encoding
    except (OSError, SyntaxError):
        return "", "utf-8"
    return source, encoding


def list_paths(
    start: Path,
    include: str = C.INCLUDE_REGEX_PATTERN,
    exclude: str = C.EXCLUDE_REGEX_PATTERN,
) -> Iterator[Path]:
    include_regex, exclude_regex = re.compile(include), re.compile(exclude)
    file_names: Iterable[Path]
    if start.is_dir():
        file_names = start.glob(C.GLOB_PATTERN)
    else:
        file_names = [start]
    yield from filter(
        lambda filename: include_regex.search(filename.as_posix()) and not exclude_regex.search(filename.as_posix()),
        file_names,
    )


def diff(*, action: list[str], expected: list[str], fromfile: Path = None) -> tuple[str, ...]:
    return tuple(
        difflib.unified_diff(
            action,
            expected,
            fromfile=fromfile.as_posix() if fromfile else "",
        )
    )
