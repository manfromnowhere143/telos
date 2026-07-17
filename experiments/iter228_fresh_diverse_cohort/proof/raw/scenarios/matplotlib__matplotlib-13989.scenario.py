import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

fig, ax = plt.subplots()
n, bins, _ = ax.hist(
    [0.25, 0.75, 10.0],
    bins=2,
    range=(0.0, 1.0),
    density=True,
)
print("RESULT=" + repr((n.tolist(), bins.tolist())))
