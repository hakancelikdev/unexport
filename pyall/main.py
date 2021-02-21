import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from pyall import color
from pyall import constants as C
from pyall.session import Session

__all__ = ["main"]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="Pyall",
        description=C.DESCRIPTION,
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
        "-v",
        "--version",
        action="version",
        version=f"Pyall {C.VERSION}",
        help="Prints version of pyall",
    )
    argv = argv if argv is not None else sys.argv[1:]
    args = parser.parse_args(argv)
    for path in args.sources:
        for source, py_path in Session.get_source(path):
            try:
                match, expected_all = Session.get_expected_all(source)
            except SyntaxError as e:
                color.paint(str(e) + "at " + py_path.as_posix(), color.RED)
                return 1
            else:
                if not match:
                    print(
                        color.paint(py_path.as_posix(), color.YELLOW)
                        + "; "
                        + " -> "
                        + color.paint(
                            "__all__ = " + str(expected_all),
                            color.GREEN,
                        )
                    )
                    return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
