import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

with matplotlib.rc_context({"axes.grid": True, "axes.grid.which": "both"}):
    fig, ax = plt.subplots()
    ax.clear()
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    fig.canvas.draw()
    result = ax.xaxis.get_minor_ticks(1)[0].gridline.get_visible()

print("RESULT=" + repr(result))
