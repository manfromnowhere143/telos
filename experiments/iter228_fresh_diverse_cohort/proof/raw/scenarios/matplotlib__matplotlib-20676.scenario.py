import matplotlib

matplotlib.use("Agg", force=True)

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector

figure = Figure()
FigureCanvasAgg(figure)
axes = figure.add_subplot()
axes.set_xlim(11, 17)

selector = SpanSelector(
    axes,
    lambda vmin, vmax: None,
    "horizontal",
    interactive=True,
    useblit=False,
)

positions = tuple(float(line.get_xdata()[0]) for line in selector._edge_handles.artists)
print("RESULT=" + repr(positions))
