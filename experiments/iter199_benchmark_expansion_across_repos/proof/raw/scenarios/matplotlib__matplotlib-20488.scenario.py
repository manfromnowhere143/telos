import matplotlib
matplotlib.use("Agg")

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

fig, ax = plt.subplots(figsize=(1, 1), dpi=20)
ax.imshow(
    np.array([[0.25, 0.75], [0.5, 1.0]], dtype=float),
    norm=LogNorm(vmin=0.0, vmax=1.0),
    interpolation="bilinear",
)
ax.set_axis_off()

try:
    fig.canvas.draw()
    result = "ok"
except Exception as exc:
    result = type(exc).__name__
finally:
    plt.close(fig)

print("RESULT=" + repr(result))
