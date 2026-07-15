import contextlib
import io
import os
import shutil
import tempfile
from pathlib import Path

root = None
marker = None
old_autoload = os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD")

try:
    root = Path(tempfile.mkdtemp())
    marker = root / "lifecycle-ran"
    testfile = root / "test_inherited_unittest_skip.py"
    config = root / "pytest.ini"
    config.write_text("[pytest]\n")

    testfile.write_text(
        f"""
import unittest

MARKER = {str(marker)!r}

@unittest.skipIf(True, "class is skipped")
class SkippedBase(unittest.TestCase):
    def setUp(self):
        with open(MARKER, "a") as f:
            f.write("setup\\n")

    def tearDown(self):
        with open(MARKER, "a") as f:
            f.write("teardown\\n")

class InheritedSkippedCase(SkippedBase):
    def test_inherited_class_skip(self):
        with open(MARKER, "a") as f:
            f.write("test\\n")
"""
    )

    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    import pytest

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        try:
            pytest.main(
                [
                    "-q",
                    "--pdb",
                    "-c",
                    str(config),
                    str(testfile),
                ]
            )
        except BaseException:
            pass

    print("PROP_FAIL" if marker.exists() and marker.read_text() else "PROP_PASS")
except BaseException:
    print("PROP_PASS")
finally:
    if old_autoload is None:
        os.environ.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)
    else:
        os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = old_autoload
    if root is not None:
        shutil.rmtree(root, ignore_errors=True)
