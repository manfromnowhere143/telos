import matplotlib

matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

fig = Figure(figsize=(4, 3), dpi=100)
FigureCanvasAgg(fig)
ax = fig.add_subplot(111)

inset = inset_axes(ax, width="30%", height="40%", loc="upper right")
locator = inset.get_axes_locator()
bbox = locator(inset, None)

print(f"RESULT={tuple(round(value, 6) for value in bbox.bounds)!r}")
