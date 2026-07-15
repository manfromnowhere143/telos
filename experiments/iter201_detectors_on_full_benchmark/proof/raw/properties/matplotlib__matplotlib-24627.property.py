import sys

try:
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.artist import Artist
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
except Exception:
    print("PROP_PASS")
    sys.exit(0)


def make_children(ax):
    line = Line2D([0, 1], [0, 1])
    ax.add_line(line)

    collection = LineCollection([[(0, 0), (1, 1)]])
    ax.add_collection(collection)

    patch = Rectangle((0.1, 0.1), 0.2, 0.2)
    ax.add_patch(patch)

    text = ax.text(0.5, 0.5, "child")
    image = ax.imshow([[1, 2], [3, 4]])

    generic = Artist()
    ax.add_artist(generic)

    return [line, collection, patch, text, image, generic]


def children_are_deparented(children):
    return all(
        child.axes is None and child.figure is None
        for child in children
    )


try:
    fig1, ax1 = plt.subplots()
    children1 = make_children(ax1)
    if not all(child.axes is ax1 and child.figure is fig1 for child in children1):
        raise RuntimeError("artists were not parented before cla")
    ax1.cla()
    cla_ok = children_are_deparented(children1)
    plt.close(fig1)

    fig2, ax2 = plt.subplots()
    children2 = make_children(ax2)
    if not all(child.axes is ax2 and child.figure is fig2 for child in children2):
        raise RuntimeError("artists were not parented before clf")
    fig2.clf()
    clf_ok = children_are_deparented(children2)
    plt.close(fig2)

    print("PROP_PASS" if cla_ok and clf_ok else "PROP_FAIL")
except Exception:
    print("PROP_FAIL")
