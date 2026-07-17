import matplotlib

matplotlib.use("Agg", force=True)

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

figure = Figure(figsize=(4, 3), dpi=100)
FigureCanvasAgg(figure)
parent = figure.add_axes([0.1, 0.1, 0.8, 0.8])
inset = inset_axes(parent, width="50%", height="50%", loc="lower left", borderpad=0)
bbox = inset.get_axes_locator()(inset, None)

print("RESULT=" + repr(tuple(float(value) for value in bbox.bounds)))
