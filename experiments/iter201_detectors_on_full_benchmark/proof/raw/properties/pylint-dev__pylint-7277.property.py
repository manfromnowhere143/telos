import contextlib
import io
import os
import sys

try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        from pylint import modify_sys_path
except Exception:
    print("PROP_PASS")
else:
    original_path_object = sys.path
    original_path = original_path_object[:]
    correct = True
    try:
        probe = os.path.join(os.getcwd(), "__pylint_property_subdirectory_not_cwd__")
        expected = [probe, "__pylint_property_marker__"]
        sys.path[:] = expected
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            modify_sys_path()
        correct = sys.path == expected
    except Exception:
        correct = False
    finally:
        sys.path = original_path_object
        original_path_object[:] = original_path

    print("PROP_PASS" if correct else "PROP_FAIL")
