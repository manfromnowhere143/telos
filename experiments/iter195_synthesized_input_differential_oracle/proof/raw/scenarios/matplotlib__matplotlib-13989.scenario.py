import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

fig, ax = plt.subplots()
counts, _, _ = ax.hist([0.1, 0.2, 2.1], bins=[0.0, 1.0, 3.0], density=True)
print("RESULT=" + repr(counts.tolist()))
