from pathlib import Path

import pytest

from unexport import utils
from unexport.main import main

__all__ = ["test_errors_are_reported", "test_read_errors"]


def test_errors_are_reported(tmp_path: Path, capsys):
    (tmp_path / "bad_bytes.py").write_bytes(b'X = 1\ny = "\xff"\n')
    (tmp_path / "bad_encoding.py").write_bytes(b"# -*- coding: not-a-real-encoding -*-\nX = 1\n")
    (tmp_path / "syntax.py").write_text("def broken(:\n")
    (tmp_path / "good.py").write_text("__all__ = ['func']\n\n\ndef func(): ...\n")

    exit_code = main([tmp_path.as_posix()])
    output = capsys.readouterr().out

    assert "can't decode" in output and "bad_bytes.py" in output
    assert "unknown encoding" in output and "bad_encoding.py" in output
    assert "invalid syntax" in output and "syntax.py" in output
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
