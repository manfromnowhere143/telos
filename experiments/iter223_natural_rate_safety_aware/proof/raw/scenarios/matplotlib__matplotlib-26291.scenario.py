import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

fig, ax = plt.subplots(figsize=(5.5, 2.8))
axins = inset_axes(ax, width=1.3, height=0.9)
fig.canvas.draw()

locator = axins.get_axes_locator()
bbox = locator(axins, None)

print("RESULT=" + repr(tuple(round(value, 6) for value in bbox.bounds)))
