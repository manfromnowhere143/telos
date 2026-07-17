import matplotlib

matplotlib.use("Agg", force=True)

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

matplotlib.rcParams["axes.grid"] = False
matplotlib.rcParams["axes.grid.which"] = "major"

figure = Figure()
FigureCanvasAgg(figure)
axes = figure.add_subplot(111)

matplotlib.rcParams["axes.grid"] = True
matplotlib.rcParams["axes.grid.which"] = "minor"

axes.xaxis.clear()
result = axes.xaxis.get_minor_ticks(1)[0].gridline.get_visible()

print(f"RESULT={result!r}")
