import matplotlib

matplotlib.use("Agg", force=True)

import numpy as np
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(2, 2), dpi=50, facecolor="white")
ax = fig.add_axes([0, 0, 1, 1], projection="3d")
ax.scatter([0], [0], [0], c=[(1, 0, 0, 1)], s=100)
ax.set_visible(False)

fig.canvas.draw()
pixels = np.asarray(fig.canvas.buffer_rgba())
visible_red = bool(np.any(
    (pixels[..., 0] > 200) & (pixels[..., 1] < 100) & (pixels[..., 2] < 100)
))
print(f"RESULT={visible_red!r}")
