import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

X = np.array([0, 0.5, 2, 3, 9, 10], dtype=float).reshape(-1, 1)
est = KBinsDiscretizer(n_bins=5, strategy="kmeans", encode="ordinal")
est.fit(X)
print("RESULT=" + repr(est.bin_edges_[0].tolist()))
