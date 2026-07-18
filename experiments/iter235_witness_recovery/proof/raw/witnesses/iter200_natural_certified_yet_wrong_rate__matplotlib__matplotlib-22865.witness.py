try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colorbar import ColorbarBase
    from matplotlib.colors import BoundaryNorm, ListedColormap

    fig, ax = plt.subplots(figsize=(2, 1))
    cmap = ListedColormap(["navy", "gold"])
    norm = BoundaryNorm([0, 1, 2], cmap.N)
    cbar = ColorbarBase(
        ax, cmap=cmap, norm=norm, orientation="horizontal",
        extend="both", drawedges=True,
    )

    if not hasattr(cbar, "dividers") or not hasattr(cbar.dividers, "get_segments"):
        result = ("ERROR", "AttributeError")
    else:
        segments = cbar.dividers.get_segments()
        result = (len(segments), tuple(tuple(map(float, s.ravel())) for s in segments))
    plt.close(fig)
    print(f"RESULT={result!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
