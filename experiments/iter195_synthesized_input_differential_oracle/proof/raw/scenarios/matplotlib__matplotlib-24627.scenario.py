import matplotlib
matplotlib.use("Agg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

figure = Figure()
FigureCanvasAgg(figure)
axes = figure.add_subplot(111)

collection = axes.scatter([0], [0])
axes.clear()

print("RESULT=" + repr((collection.axes is None, collection.figure is None)))
