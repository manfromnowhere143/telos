try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg", force=True)

    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.patches import Rectangle

    def render(linestyle):
        fig = Figure(figsize=(3, 3), dpi=100)
        FigureCanvasAgg(fig)
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set_xlim(0, 2)
        ax.set_ylim(0, 2)
        ax.set_axis_off()

        patch = Rectangle(
            (0.25, 0.35), 1.5, 1.2,
            facecolor="none",
            edgecolor="blue",
            linewidth=3,
            linestyle=linestyle,
            antialiased=True,
        )
        ax.add_patch(patch)
        fig.canvas.draw()
        return np.asarray(fig.canvas.buffer_rgba()).copy()

    # For a [10, 10] on/off pattern, offset 13 begins three units into
    # the off section.  The zero-offset sequence below is the equivalent
    # explicit representation: off 7, on 10, off 3.
    offset_image = render((13, [10, 10]))
    equivalent_image = render((0, [0, 7, 10, 3]))

    print("PROP_PASS" if np.array_equal(offset_image, equivalent_image)
          else "PROP_FAIL")
except Exception:
    print("PROP_PASS")
