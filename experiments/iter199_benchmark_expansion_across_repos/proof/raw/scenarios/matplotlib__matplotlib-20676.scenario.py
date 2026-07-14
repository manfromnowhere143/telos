import matplotlib
matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib.widgets import SpanSelector

fig, ax = plt.subplots()
ax.set_xlim(20, 10)
ax.set_ylim(200, 100)

selector = SpanSelector(ax, lambda *_: None, "horizontal", interactive=True)
positions = tuple(
    float(line.get_xdata()[0]) for line in selector._edge_handles.artists
)

print("RESULT=" + repr(positions))
