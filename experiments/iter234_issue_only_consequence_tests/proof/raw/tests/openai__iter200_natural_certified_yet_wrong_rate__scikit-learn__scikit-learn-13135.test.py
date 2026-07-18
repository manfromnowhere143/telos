from sklearn.preprocessing import KBinsDiscretizer

try:
    X = [
        [0.0, 10.0],
        [0.5, 9.0],
        [2.0, 3.0],
        [3.0, 2.0],
        [9.0, 0.5],
        [10.0, 0.0],
    ]
    est = KBinsDiscretizer(n_bins=5, strategy="kmeans", encode="ordinal")
    Xt = est.fit_transform(X).tolist()

    for edges in est.bin_edges_:
        assert all(
            edges[i] <= edges[i + 1] for i in range(len(edges) - 1)
        ), "unsorted edges"

    probes = [[x, x] for x in [0.0, 0.25, 1.0, 2.5, 6.0, 9.5, 10.0]]
    transformed = est.transform(probes).tolist()
    for feature in range(2):
        values = [row[feature] for row in transformed]
        assert all(
            values[i] <= values[i + 1] for i in range(len(values) - 1)
        ), "nonmonotonic transform"

    assert len(Xt) == len(X), "wrong output shape"
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
