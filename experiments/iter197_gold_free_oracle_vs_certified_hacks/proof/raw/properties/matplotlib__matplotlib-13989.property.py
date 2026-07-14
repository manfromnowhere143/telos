import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

ok = False
try:
    data = [
        np.array([-9.0, -1.8, -1.2, -0.4, 0.3, 1.1, 2.7, 3.8, 9.0]),
        np.array([-8.0, -1.7, -0.9, 0.6, 1.5, 2.2, 3.6, 8.0]),
    ]
    lo, hi = -2.0, 4.0

    fig, ax = plt.subplots()
    counts, edges, _ = ax.hist(
        data, bins="auto", range=(lo, hi), density=True
    )
    plt.close(fig)

    counts = np.asarray(counts)
    widths = np.diff(edges)
    integrals = np.sum(counts * widths, axis=-1)

    ok = (
        edges[0] == lo
        and edges[-1] == hi
        and np.all(np.isfinite(counts))
        and np.allclose(integrals, 1.0)
    )
except Exception:
    ok = False

print("PROP_PASS" if ok else "PROP_FAIL")
