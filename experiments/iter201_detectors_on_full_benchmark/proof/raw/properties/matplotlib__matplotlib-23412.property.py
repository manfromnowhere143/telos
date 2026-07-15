import matplotlib
matplotlib.use("Agg", force=True)

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.patches import Rectangle


def render(linestyle):
    fig = Figure(figsize=(3, 3), dpi=100, facecolor="white")
    FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    ax.add_patch(Rectangle(
        (0.17, 0.21), 0.65, 0.57,
        facecolor="none", edgecolor="black",
        linewidth=4, linestyle=linestyle,
        antialiased=True,
    ))
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba()).copy()


# A phase offset of 3 through (8 on, 5 off) starts with 5 on, 5 off,
# then 3 on; the trailing zero gap joins that 3-unit dash to the next
# 5-unit dash, yielding the original 8-unit dash period.
offset_image = render((3, (8, 5)))
equivalent_zero_offset_image = render((0, (5, 5, 3, 0)))

difference = np.abs(
    offset_image.astype(np.int16) - equivalent_zero_offset_image.astype(np.int16)
)
significant_pixels = np.count_nonzero(np.max(difference[:, :, :3], axis=2) > 2)

print("PROP_PASS" if significant_pixels == 0 else "PROP_FAIL")
