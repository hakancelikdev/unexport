from __future__ import annotations

from typing import NamedTuple

from unexport import constants as C

__all__ = ("Config",)


class Config(NamedTuple):
    include: str = C.INCLUDE_REGEX_PATTERN
    exclude: str = C.EXCLUDE_REGEX_PATTERN
