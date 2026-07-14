import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.patches import Circle

fig, ax = plt.subplots()

generic = Artist()
patch = Circle((0.5, 0.5), 0.2)
text = ax.text(0.2, 0.3, "orphan me")
collection = ax.scatter([0.1, 0.9], [0.2, 0.8])

ax.add_artist(generic)
ax.add_patch(patch)

artists = [generic, patch, text, collection]
before = all(artist.axes is ax and artist.figure is fig for artist in artists)

ax.clear()

after = all(artist.axes is None and artist.figure is None for artist in artists)

plt.close(fig)
print("PROP_PASS" if before and after else "PROP_FAIL")
