import os
import re
import tempfile

from pylint.lint.expand_modules import _is_ignored_file

with tempfile.TemporaryDirectory() as root:
    os.makedirs(os.path.join(root, "gen"))
    element = os.path.join(root, "decoy", "..", "gen", "about.py")
    ignored_path = os.path.join(root, "gen") + os.sep
    result = _is_ignored_file(
        element,
        [],
        [],
        [re.compile("^" + re.escape(ignored_path) + r".*$")],
    )

print(f"RESULT={result!r}")
