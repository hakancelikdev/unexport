from pathlib import Path

import pytest

from unexport import utils
from unexport.main import main

__all__ = [
    "test_errors_are_reported",
    "test_read_errors",
    "test_refactor_keeps_crlf_newlines",
    "test_several_statements_are_not_refactored",
]


def test_errors_are_reported(tmp_path: Path, capsys):
    (tmp_path / "bad_bytes.py").write_bytes(b'X = 1\ny = "\xff"\n')
    (tmp_path / "bad_encoding.py").write_bytes(b"# -*- coding: not-a-real-encoding -*-\nX = 1\n")
    (tmp_path / "syntax.py").write_text("def broken(:\n")
    (tmp_path / "null_bytes.py").write_bytes(b"X = 1\x00\n")
    (tmp_path / "good.py").write_text("__all__ = ['func']\n\n\ndef func(): ...\n")

    exit_code = main([tmp_path.as_posix()])
    output = capsys.readouterr().out

    assert "can't decode" in output and "bad_bytes.py" in output
    assert "unknown encoding" in output and "bad_encoding.py" in output
    assert "invalid syntax" in output and "syntax.py" in output
    assert "null bytes" in output and "null_bytes.py" in output
    assert "good.py" not in output  # checked, and its __all__ is up to date
    assert exit_code == 1


@pytest.mark.parametrize(
    "content, error",
    [
        (b"# -*- coding: not-a-real-encoding -*-\n", SyntaxError),
        (b'x = 1\ny = 2\nz = "\xff"\n', UnicodeDecodeError),  # after the lines used to detect the encoding
    ],
)
def test_read_errors(tmp_path: Path, content: bytes, error: type):
    path = tmp_path / "bad.py"
    path.write_bytes(content)

    with pytest.raises(error):
        utils.read(path)
    assert issubclass(error, utils.READ_ERRORS)


def test_several_statements_are_not_refactored(tmp_path: Path, capsys):
    path = tmp_path / "module.py"
    source = '__all__ = ["a"]\n__all__ += ["b"]\n\n\ndef a(): ...\n\n\ndef b(): ...\n\n\ndef c(): ...\n'
    path.write_text(source)

    exit_code = main(["--refactor", path.as_posix()])
    output = capsys.readouterr().out

    assert "can't be updated automatically" in output and "'c'" in output
    assert "Refactoring" not in output
    assert path.read_text() == source
    assert exit_code == 1


def test_refactor_keeps_crlf_newlines(tmp_path: Path):
    path = tmp_path / "crlf.py"
    path.write_bytes(b"import os\r\n\r\nclass Public: ...\r\n")

    main(["--refactor", path.as_posix()])

    assert path.read_bytes() == b'import os\r\n\r\n__all__ = ["Public"]\r\n\r\nclass Public: ...\r\n'
