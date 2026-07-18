try:
    import numpy as np
    from scipy import sparse
    from sklearn.svm import SVR

    calls = [0]
    original_tile = np.tile

    def counted_tile(*args, **kwargs):
        calls[0] += 1
        return original_tile(*args, **kwargs)

    X = sparse.csr_matrix(np.array([[0.0], [1.0], [2.0]]))
    y = np.array([0.0, 1.0, 0.0])
    model = SVR(kernel="linear", C=1.0, epsilon=0.0)

    np.tile = counted_tile
    try:
        model.fit(X, y)
    finally:
        np.tile = original_tile

    result = ("tile_calls", calls[0])
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
