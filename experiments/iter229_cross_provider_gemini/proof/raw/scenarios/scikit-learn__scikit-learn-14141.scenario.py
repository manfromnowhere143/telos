import sklearn.utils._show_versions as show_versions

calls = []
original_import_module = show_versions.importlib.import_module

def tracked_import_module(name, *args, **kwargs):
    if name in ("Cython", "pandas", "matplotlib", "joblib"):
        calls.append(name)
    return original_import_module(name, *args, **kwargs)

show_versions.importlib.import_module = tracked_import_module
try:
    show_versions._get_deps_info()
finally:
    show_versions.importlib.import_module = original_import_module

result = tuple((name, calls.count(name)) for name in ("Cython", "pandas", "matplotlib", "joblib"))
print("RESULT=" + repr(result))
