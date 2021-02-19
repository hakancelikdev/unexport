import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from pyall import color
from pyall import constants as C
from pyall import utils
from pyall.analyzer import Analyzer

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
    exact = False
    for source_path in args.sources:
        for py_path in utils.list_paths(source_path):
            source, encoding = utils.read(py_path)
            analyzer = Analyzer(source=source)
            try:
                analyzer.traverse()
            except SyntaxError as e:
                print(e, "at ", py_path)
                return 1
            else:
                exact = sorted(analyzer.all) == sorted(analyzer.expected_all)
                if not exact:
                    print(
                        color.paint(py_path.as_posix(), color.YELLOW)
                        + "; "
                        + " -> "
                        + color.paint(
                            "__all__ = " + str(list(analyzer.expected_all)),
                            color.GREEN,
                        )
                    )
                    return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
