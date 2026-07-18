import matplotlib

try:
    matplotlib.use("Agg")
    from matplotlib.collections import Collection
    from matplotlib.path import Path

    collection = Collection()
    collection.stale = False
    paths = [Path.unit_rectangle()]
    collection.set_paths(paths)
    result = (
        len(collection.get_paths()),
        collection.get_paths() is paths,
        bool(collection.stale),
    )
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
