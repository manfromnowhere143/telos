import warnings

warnings.filterwarnings("ignore")

try:
    import matplotlib
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt
    from matplotlib.backend_bases import MouseEvent
    from matplotlib.widgets import SpanSelector

    def event(ax, name, xdata, ydata, button=1):
        xpix, ypix = ax.transData.transform((xdata, ydata))
        return MouseEvent(name, ax.figure.canvas, xpix, ypix, button=button)

    def unchanged(before, after):
        return before == after

    ok = True
    for direction in ("horizontal", "vertical"):
        fig, ax = plt.subplots()
        ax.plot([-90, -70], [-190, -150])
        fig.canvas.draw()

        x_before = ax.get_xbound()
        y_before = ax.get_ybound()

        selector = SpanSelector(
            ax, lambda *args: None, direction, interactive=True, useblit=False
        )

        expected_handles = list(
            x_before if direction == "horizontal" else y_before
        )
        ok &= unchanged(x_before, ax.get_xbound())
        ok &= unchanged(y_before, ax.get_ybound())
        ok &= selector._edge_handles.positions == expected_handles

        selector.press(event(ax, "button_press_event", -88, -180))
        selector.onmove(event(ax, "motion_notify_event", -80, -170))

        ok &= unchanged(x_before, ax.get_xbound())
        ok &= unchanged(y_before, ax.get_ybound())

        plt.close(fig)

    print("PROP_PASS" if ok else "PROP_FAIL")
except Exception:
    print("PROP_FAIL")
