import os
import tempfile

from _pytest.pathlib import visit

with tempfile.TemporaryDirectory() as root:
    os.mkdir(os.path.join(root, "target"))
    with open(os.path.join(root, "target", "leaf.txt"), "w", encoding="utf-8"):
        pass
    os.symlink("target", os.path.join(root, "link"), target_is_directory=True)

    result = [
        os.path.relpath(entry.path, root).replace(os.sep, "/")
        for entry in visit(root, lambda entry: True)
    ]

print("RESULT=" + repr(result))
