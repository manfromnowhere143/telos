import matplotlib

matplotlib.use("Agg")

from matplotlib.cbook import Grouper


class Item:
    pass


item = Item()
grouper = Grouper([item])
state = grouper.__getstate__()

print(f"RESULT={type(state['_mapping']).__name__!r}")
