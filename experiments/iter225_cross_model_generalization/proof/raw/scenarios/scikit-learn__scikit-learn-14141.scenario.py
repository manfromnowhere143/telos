import sklearn.utils._show_versions as show_versions

counts = {}


def fake_version(module):
    counts[module] = counts.get(module, 0) + 1
    return f"{module}:{counts[module]}"


if hasattr(show_versions, "version"):
    show_versions.version = fake_version
if hasattr(show_versions, "metadata"):
    show_versions.metadata.version = fake_version
if hasattr(show_versions, "importlib") and hasattr(show_versions.importlib, "metadata"):
    show_versions.importlib.metadata.version = fake_version
if hasattr(show_versions, "importlib_metadata"):
    show_versions.importlib_metadata.version = fake_version

print(f"RESULT={show_versions._get_deps_info()!r}")
