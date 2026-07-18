import matplotlib

matplotlib.use("Agg")

try:
    from matplotlib.collections import PathCollection
    from matplotlib.path import Path

    original = Path([[0.0, 0.0], [1.0, 1.0]])
    replacement = Path([[2.0, 3.0], [4.0, 5.0]])
    collection = PathCollection([original])

    if not hasattr(collection, "set_paths") or not hasattr(collection, "get_paths"):
        raise AttributeError("paths_api")

    collection.set_paths([replacement])
    paths = collection.get_paths()
    point = tuple(float(value) for value in paths[0].vertices[0])
    print(f"RESULT={repr((len(paths), point, bool(collection.stale)))}")
except Exception as exc:
    print(f"RESULT={repr(('ERROR', type(exc).__name__))}")
