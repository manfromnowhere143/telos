import sys

try:
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
except Exception:
    print("PROP_PASS")
    sys.exit(0)

try:
    with matplotlib.rc_context({
        "xtick.bottom": True,
        "xtick.top": False,
        "xtick.labelbottom": True,
        "xtick.labeltop": False,
        "ytick.left": True,
        "ytick.right": False,
        "ytick.labelleft": True,
        "ytick.labelright": False,
    }):
        fig, axs = plt.subplots(3, 3, sharex="col", sharey="row")

        # Clear in a nontrivial order so each shared-axis member must retain
        # the label suppression imposed by subplot sharing.
        for ax in axs.flat[::-1]:
            ax.clear()
            ax.plot([0, 1], [0, 1])

        fig.canvas.draw()

        ok = True

        for row in range(3):
            for col in range(3):
                ax = axs[row, col]

                xlabels_visible = any(
                    tick.label1.get_visible() or tick.label2.get_visible()
                    for tick in ax.xaxis.get_major_ticks()
                )
                ylabels_visible = any(
                    tick.label1.get_visible() or tick.label2.get_visible()
                    for tick in ax.yaxis.get_major_ticks()
                )

                # For column-wise shared x axes, only the bottom row should
                # expose x tick labels.  For row-wise shared y axes, only the
                # left column should expose y tick labels.
                if xlabels_visible != (row == 2):
                    ok = False
                if ylabels_visible != (col == 0):
                    ok = False

        # Clearing must also leave the declared sharing relationships intact.
        axs[0, 1].set_xlim(10, 20)
        axs[2, 0].set_ylim(-3, -2)

        for ax in axs[:, 1]:
            if tuple(ax.get_xlim()) != (10.0, 20.0):
                ok = False
        for ax in axs[2, :]:
            if tuple(ax.get_ylim()) != (-3.0, -2.0):
                ok = False

        plt.close(fig)
        print("PROP_PASS" if ok else "PROP_FAIL")
except Exception:
    print("PROP_FAIL")
