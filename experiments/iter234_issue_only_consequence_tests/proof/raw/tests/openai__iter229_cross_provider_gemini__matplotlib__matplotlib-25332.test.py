import copy
import matplotlib

try:
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.plot([0, 1, 2, 3, 4], [40000, 4300, 4500, 4700, 4800])
    ax2.plot([0, 1, 2, 3, 4], [10, 11, 12, 13, 14])
    ax1.set_ylabel("speed")
    ax2.set_ylabel("acc")
    fig.align_labels()

    copied = copy.deepcopy(fig)
    assert copied is not fig, "copy"
    assert len(copied.axes) == 2, "axes"
    assert [ax.get_ylabel() for ax in copied.axes] == ["speed", "acc"], "labels"

    copied.align_labels()
    copied.canvas.draw()
    plt.close(fig)
    plt.close(copied)
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc) or 'assertion')!r}")
except BaseException as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
