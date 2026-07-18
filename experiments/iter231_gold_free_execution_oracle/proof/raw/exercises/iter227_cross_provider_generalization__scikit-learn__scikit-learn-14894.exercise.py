from sklearn.svm import SVR
from sklearn.svm import _base

try:
    X = [
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
    y = [0.04, 0.04, 0.10, 0.16]
    model = SVR(
        C=316.227766017,
        cache_size=200,
        coef0=0.0,
        degree=3,
        epsilon=0.1,
        gamma=1.0,
        kernel="linear",
        max_iter=15000,
        shrinking=True,
        tol=0.001,
    )
    model.fit(_base.sp.csr_matrix(X), y)
    print(
        "RESULT=%r"
        % (
            "OK",
            tuple(model.support_vectors_.shape),
            tuple(model.dual_coef_.shape),
            model.dual_coef_.nnz,
            model.predict(_base.sp.csr_matrix(X)).tolist(),
        )
    )
except Exception as exc:
    print("RESULT=%r" % (("ERROR", type(exc).__name__),))
