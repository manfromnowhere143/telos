import contextlib
import io
import pathlib
import tempfile

import pytest

with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    marker = root / "marker.txt"
    test_file = root / "test_inherited_skip.py"
    test_file.write_text(
        f"""
import unittest
from pathlib import Path

MARKER = Path({str(marker)!r})

@unittest.skip("inherited class skip")
class SkippedBase(unittest.TestCase):
    def tearDown(self):
        MARKER.write_text("tearDown")

class TestInheritedSkip(SkippedBase):
    def test_case(self):
        pass
""",
        encoding="utf-8",
    )

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        pytest.main(["-q", "--pdb", str(test_file)])

    result = marker.read_text(encoding="utf-8") if marker.exists() else ""
    print(f"RESULT={result!r}")
