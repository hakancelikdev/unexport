from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from unexport import __description__, __version__, color
from unexport import constants as C
from unexport import utils
from unexport.config import Config
from unexport.session import Session

__all__ = ("main",)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="unexport",
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
        help="Prints a diff of all the changes Unexport would make to a file.",
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
        version=f"Unexport {__version__}",
        help="Prints version of unexport",
    )
    argv = argv if argv is not None else sys.argv[1:]
    args = parser.parse_args(argv)
    config = Config(include=args.include, exclude=args.exclude)
    session = Session(config=config)
    exit_code = 0
    for path in args.sources:
        for source, py_path, error in session.get_source(path):
            if source is not None:
                try:
                    match, expected_all = session.get_expected_all(source, py_path)
                except SyntaxError as exc:
                    error = str(exc)
            if error is not None:
                print(color.paint(f"{error} at {py_path.as_posix()}", color.RED))
                exit_code = 1
                continue
            if match:
                continue
            exit_code = 1
            if args.refactor or args.diff:
                new_source = session.refactor(path=py_path, apply=args.refactor)
                if new_source == source:
                    print(
                        color.paint(py_path.as_posix(), color.YELLOW)
                        + ": __all__ is built from several statements and can't be updated automatically; expected "
                        + color.paint("__all__ = " + str(expected_all), color.GREEN)
                    )
                    continue
            if args.refactor:
                print(f"Refactoring '{color.paint(str(py_path), color.GREEN)}'")
            if args.diff:
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
