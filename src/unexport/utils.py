from __future__ import annotations

import difflib
import re
import tokenize
from collections.abc import Iterable, Iterator
from pathlib import Path

from unexport import constants as C

__all__ = ("READ_ERRORS", "diff", "list_paths", "read")


# Raised by read(): the file can't be opened, has an invalid encoding declaration or can't be decoded.
READ_ERRORS = (OSError, SyntaxError, UnicodeDecodeError)


def read(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        source = stream.read()
        encoding = stream.encoding
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
