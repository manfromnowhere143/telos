try:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.svm import SVR

    X = CountVectorizer(
        vocabulary={"aa": 0, "bb": 1, "cc": 2, "dd": 3}
    ).transform(["bb", "dd", "cc", "dd"])
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
        verbose=False,
    ).fit(X, y)
    observed = (
        model.support_vectors_.shape,
        model.dual_coef_.shape,
        model.dual_coef_.nnz,
        tuple(model.predict(X)),
    )
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
