import matplotlib

matplotlib.use("Agg")

from matplotlib.cbook import Grouper


class Item:
    pass


item = Item()
grouper = Grouper([item])
original_dict = grouper.__dict__
state = grouper.__getstate__()
grouper.__setstate__(state)

print(f"RESULT={original_dict is grouper.__dict__!r}")
