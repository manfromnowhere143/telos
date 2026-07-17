import sklearn.utils._show_versions as show_versions

counts = {}
metadata = show_versions.importlib.metadata
original_version = metadata.version


def version(name):
    counts[name] = counts.get(name, 0) + 1
    return f"{name}:{counts[name]}"


metadata.version = version
try:
    result = show_versions._get_deps_info()
finally:
    metadata.version = original_version

print(f"RESULT={result!r}")
