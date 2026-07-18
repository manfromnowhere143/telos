import copy

try:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1)
    axes[0].plot([0, 1, 2], [40000, 4300, 4500])
    axes[1].plot([0, 1, 2], [10, 11, 12])
    axes[0].set_ylabel("speed")
    axes[1].set_ylabel("acc")
    fig.align_labels()

    cloned = copy.deepcopy(fig)
    cloned.align_labels()
    observed = (
        "OK",
        len(cloned.axes),
        tuple(ax.get_ylabel() for ax in cloned.axes),
    )
except Exception as exc:
    observed = ("ERROR", type(exc).__name__)

print(f"RESULT={observed!r}")
