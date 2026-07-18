import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

try:
    X = np.array([0, 0.5, 2, 3, 9, 10]).reshape(-1, 1)
    est = KBinsDiscretizer(n_bins=5, strategy='kmeans', encode='ordinal')
    Xt = est.fit_transform(X)

    # bin_edges must be monotonically increasing for each feature
    edges = est.bin_edges_[0]
    if not np.all(np.diff(edges) >= 0):
        raise AssertionError("bin_edges not sorted")

    # transformed values must be valid ordinal bins within range
    Xt = Xt.ravel()
    if not np.all((Xt >= 0) & (Xt <= est.n_bins_[0] - 1)):
        raise AssertionError("ordinal values out of range")

    # monotone input should give monotone (non-decreasing) ordinal output
    if not np.all(np.diff(Xt) >= 0):
        raise AssertionError("ordinal output not monotone for sorted input")

    # inverse_transform should be within data range and monotone
    Xinv = est.inverse_transform(Xt.reshape(-1, 1)).ravel()
    if not np.all(np.diff(Xinv) >= 0):
        raise AssertionError("inverse not monotone")
    if Xinv.min() < X.min() - 1e-6 or Xinv.max() > X.max() + 1e-6:
        raise AssertionError("inverse out of data range")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
