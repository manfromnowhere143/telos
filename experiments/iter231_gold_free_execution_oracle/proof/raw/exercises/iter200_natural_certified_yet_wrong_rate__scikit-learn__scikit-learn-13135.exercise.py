import warnings

from sklearn.preprocessing import KBinsDiscretizer

try:
    X = [[0], [0.5], [2], [3], [9], [10]]
    results = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for n_bins in (4, 5):
            estimator = KBinsDiscretizer(
                n_bins=n_bins, strategy="kmeans", encode="ordinal"
            )
            transformed = estimator.fit_transform(X)
            edges = estimator.bin_edges_[0].tolist()
            results.append((
                n_bins,
                all(left <= right for left, right in zip(edges, edges[1:])),
                transformed.ravel().tolist(),
            ))
    print("RESULT=" + repr(tuple(results)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
