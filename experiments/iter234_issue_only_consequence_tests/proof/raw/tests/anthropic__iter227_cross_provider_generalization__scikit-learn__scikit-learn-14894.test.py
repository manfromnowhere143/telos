try:
    import numpy as np
    import scipy.sparse
    from sklearn.svm import SVR

    x_train = np.array([[0, 1, 0, 0],
                        [0, 0, 0, 1],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    y_train = np.array([0.04, 0.04, 0.10, 0.16])

    model = SVR(C=316.227766017, cache_size=200, coef0=0.0, degree=3,
                epsilon=0.1, gamma=1.0, kernel='linear', max_iter=15000,
                shrinking=True, tol=0.001, verbose=False)

    xtrain = scipy.sparse.csr_matrix(x_train)
    model.fit(xtrain, y_train)

    fails = []
    # support vectors should be empty
    if model.support_vectors_.shape[0] != 0:
        fails.append("support_vectors not empty")

    # dual_coef_ should be a sparse matrix and empty
    if not scipy.sparse.issparse(model.dual_coef_):
        fails.append("dual_coef_ not sparse")
    if model.dual_coef_.nnz != 0:
        fails.append("dual_coef_ not empty")

    # predict should still work and be finite
    preds = model.predict(xtrain)
    if preds.shape[0] != x_train.shape[0]:
        fails.append("pred shape wrong")
    if not np.all(np.isfinite(preds)):
        fails.append("pred not finite")

    if fails:
        print(f"RESULT={('FAIL', '; '.join(fails))!r}")
    else:
        print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
