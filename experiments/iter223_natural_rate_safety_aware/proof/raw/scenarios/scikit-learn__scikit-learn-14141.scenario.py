import types

import sklearn.utils._show_versions as show_versions

calls = []
original_import_module = show_versions.importlib.import_module
stub_module = types.SimpleNamespace(__version__="stub")

def import_module(name, *args, **kwargs):
    calls.append(name)
    return stub_module

show_versions.importlib.import_module = import_module
try:
    info = show_versions._get_deps_info()
finally:
    show_versions.importlib.import_module = original_import_module

result = (
    tuple(info.items()),
    tuple((name, calls.count(name)) for name in ("Cython", "pandas", "matplotlib", "joblib")),
)
print("RESULT=" + repr(result))
