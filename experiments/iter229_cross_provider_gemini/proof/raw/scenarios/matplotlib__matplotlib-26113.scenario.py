import matplotlib
matplotlib.use("Agg")

import numpy as np
from matplotlib.figure import Figure

figure = Figure()
axes = figure.add_subplot()

collection = axes.hexbin(
    [0.25],
    [0.25],
    C=[7.0],
    gridsize=2,
    extent=(0.0, 1.0, 0.0, 1.0),
    mincnt=1,
    reduce_C_function=np.sum,
)

values = np.asarray(collection.get_array(), dtype=float)
result = tuple(float(value) for value in values if np.isfinite(value))
print("RESULT=" + repr(result))
