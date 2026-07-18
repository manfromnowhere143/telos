import copy
import matplotlib

try:
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1)
    axes[0].plot([0, 1, 2], [0, 1, 2])
    axes[1].plot([0, 1, 2], [0, 1, 2])
    axes[0].set_ylabel("small")
    axes[1].set_ylabel("large")
    fig.align_labels()

    replica = copy.deepcopy(fig)
    assert replica is not fig
    assert len(replica.axes) == 2
    assert all(ax.figure is replica for ax in replica.axes)

    replica.axes[1].set_ylim(-100000, 100000)
    replica.canvas.draw()
    x0 = replica.axes[0].yaxis.label.get_position()[0]
    x1 = replica.axes[1].yaxis.label.get_position()[0]
    assert abs(x0 - x1) < 1e-7

    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'alignment')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
