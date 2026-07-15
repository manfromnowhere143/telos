import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1], label="line")
legend = ax.legend()
draggable = legend.set_draggable(True)

callbacks = fig.canvas.callbacks.callbacks
events = tuple(
    next(
        event
        for event, registered in callbacks.items()
        if cid in registered
    )
    for cid in draggable.cids
)

print(f"RESULT={events!r}")
