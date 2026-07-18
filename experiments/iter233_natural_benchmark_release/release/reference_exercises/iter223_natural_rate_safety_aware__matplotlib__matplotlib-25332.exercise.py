import copy
import matplotlib.pyplot as plt

try:
    fig, axes = plt.subplots(2, 2)
    for index, ax in enumerate(axes.flat):
        ax.plot([0, 1, 2], [index, index + 1, index + 2])
        ax.set_xlabel(f"x{index}")
        ax.set_ylabel(f"y{index}")

    fig.align_labels()
    cloned = copy.deepcopy(fig)
    cloned.align_labels()
    cloned.canvas.draw()

    observed = (
        "deepcopy",
        len(cloned.axes),
        tuple((ax.get_xlabel(), ax.get_ylabel()) for ax in cloned.axes),
    )
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
