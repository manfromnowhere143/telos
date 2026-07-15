import matplotlib
matplotlib.use("Agg")

import numpy as np
from matplotlib.colors import ListedColormap

cmap = ListedColormap(["red", "blue"])
result = cmap(np.array([0.5]))
print(f"RESULT={result.tolist()!r}")
