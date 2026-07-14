import os
import sys

import pylint

original_cwd = os.getcwd()
original_path = sys.path[:]
original_pythonpath = os.environ.get("PYTHONPATH")

try:
    os.chdir(os.path.abspath(os.sep))
    cwd = os.getcwd()
    sys.path[:] = [cwd, "__sentinel__"]
    os.environ["PYTHONPATH"] = "__sentinel_pythonpath__"

    pylint.modify_sys_path()
    result = sys.path[:]
finally:
    sys.path[:] = original_path
    os.chdir(original_cwd)
    if original_pythonpath is None:
        os.environ.pop("PYTHONPATH", None)
    else:
        os.environ["PYTHONPATH"] = original_pythonpath

print(f"RESULT={result!r}")
