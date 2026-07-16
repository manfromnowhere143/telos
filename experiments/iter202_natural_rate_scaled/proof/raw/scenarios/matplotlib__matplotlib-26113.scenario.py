import matplotlib
matplotlib.use("Agg")

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

figure = Figure()
FigureCanvasAgg(figure)
axes = figure.add_subplot()

collection = axes.hexbin(
    [0.0],
    [0.0],
    C=[7.0],
    gridsize=(1, 1),
    extent=(-1.0, 1.0, -1.0, 1.0),
    mincnt=1,
    reduce_C_function=np.mean,
)

print("RESULT=" + repr(np.asarray(collection.get_array()).tolist()))
