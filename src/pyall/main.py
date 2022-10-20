from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from pyall import __description__, __version__, color
from pyall import constants as C
from pyall import utils
from pyall.config import Config
from pyall.session import Session

__all__ = ("main",)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="Pyall",
        description=__description__,
    )
    parser.add_argument(
        "sources",
        default=[Path(".")],
        nargs="*",
        help="Enter the directories and file paths you want to analyze.",
        action="store",
        type=Path,
    )
    parser.add_argument(
        "-r",
        "--refactor",
        action="store_true",
        help="Auto-sync __all__ list in python modules automatically.",
    )
    parser.add_argument(
        "-d",
        "--diff",
        action="store_true",
        help="Prints a diff of all the changes Pyall would make to a file.",
    )
    parser.add_argument(
        "--include",
        help="File include pattern.",
        metavar="include",
        action="store",
        default=C.INCLUDE_REGEX_PATTERN,
        type=str,
    )
    parser.add_argument(
        "--exclude",
        help="File exclude pattern.",
        metavar="exclude",
        action="store",
        default=C.EXCLUDE_REGEX_PATTERN,
        type=str,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Pyall {__version__}",
        help="Prints version of pyall",
    )
    argv = argv if argv is not None else sys.argv[1:]
    args = parser.parse_args(argv)
    config = Config(include=args.include, exclude=args.exclude)
    session = Session(config=config)
    exit_code = 0
    for path in args.sources:
        for source, py_path in session.get_source(path):
            try:
                match, expected_all = session.get_expected_all(source)
                if match:
                    continue
            except SyntaxError as e:
                color.paint(str(e) + "at " + py_path.as_posix(), color.RED)
                continue
            else:
                exit_code = 1
            if args.refactor:
                session.refactor(path=py_path, apply=True)
                print(
                    f"Refactoring '{color.paint(str(py_path), color.GREEN)}'"
                )
            if args.diff:
                new_source = session.refactor(path=py_path, apply=False)
                diff = utils.diff(
                    action=source.splitlines(),
                    expected=new_source.splitlines(),
                    fromfile=py_path,
                )
                print(color.diff(diff))
            if not args.diff and not args.refactor:
                print(
                    color.paint(py_path.as_posix(), color.YELLOW)
                    + "; "
                    + " -> "
                    + color.paint(
                        "__all__ = " + str(expected_all),
                        color.GREEN,
                    )
                )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
