import warnings

import numpy as np
import matplotlib

matplotlib.use("Agg", force=True)

from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

warnings.simplefilter("ignore")
np.seterr(all="ignore")

fig = Figure(figsize=(1, 1), dpi=16)
canvas = FigureCanvasAgg(fig)
ax = fig.add_axes((0, 0, 1, 1))
ax.set_axis_off()

ax.imshow(
    np.array([[1e-30, 1.0], [1e-30, 1.0]], dtype=np.float32),
    norm=LogNorm(vmin=1e-50, vmax=1.0),
    interpolation="bilinear",
    interpolation_stage="data",
)

canvas.draw()

print("RESULT=" + repr("completed"))
