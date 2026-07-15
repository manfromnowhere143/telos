import sys
from types import SimpleNamespace

from _pytest.compat import num_mock_patch_args

saved_mock = sys.modules.pop("mock", None)
saved_unittest_mock = sys.modules.pop("unittest.mock", None)

try:
    function = SimpleNamespace(
        patchings=[SimpleNamespace(attribute_name=None, new=object())]
    )
    result = num_mock_patch_args(function)
finally:
    if saved_mock is not None:
        sys.modules["mock"] = saved_mock
    if saved_unittest_mock is not None:
        sys.modules["unittest.mock"] = saved_unittest_mock

print("RESULT={!r}".format(result))
