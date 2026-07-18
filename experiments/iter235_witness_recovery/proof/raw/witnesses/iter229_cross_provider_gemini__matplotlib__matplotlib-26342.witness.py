try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path

    fig, ax = plt.subplots()
    if not hasattr(ax, "contour"):
        raise AttributeError("contour")
    cs = ax.contour([[0, 1], [1, 0]], levels=[0.5])

    if not hasattr(cs, "set_paths") or not hasattr(cs, "get_paths"):
        raise AttributeError("paths")
    if not hasattr(cs, "stale"):
        raise AttributeError("stale")

    replacement = [
        Path([[0.0, 0.0], [1.0, 1.0]]),
        Path([[0.0, 1.0], [1.0, 0.0]]),
    ]
    cs.stale = False
    cs.set_paths(replacement)
    result = (len(cs.get_paths()), cs.get_paths()[0] is replacement[0], cs.stale)
    print(f"RESULT={result!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
