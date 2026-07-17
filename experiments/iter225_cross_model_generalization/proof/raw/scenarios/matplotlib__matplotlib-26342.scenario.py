import matplotlib

matplotlib.use("Agg")

from matplotlib.collections import PathCollection
from matplotlib.path import Path

collection = PathCollection([Path.unit_rectangle()])
print("RESULT=" + repr((len(collection.get_paths()), collection.stale)))
