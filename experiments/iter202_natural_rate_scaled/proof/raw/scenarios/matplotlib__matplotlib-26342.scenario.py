import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib.path import Path

fig, ax = plt.subplots()
cs = ax.contour([[0.0, 1.0], [1.0, 0.0]], levels=[0.5])

replacement = Path([[2.0, 3.0], [4.0, 5.0]])
cs.set_paths([replacement])

result = (
    len(cs.get_paths()),
    cs.get_paths()[0].vertices.tolist(),
    bool(cs.stale),
)
print(f"RESULT={result!r}")
