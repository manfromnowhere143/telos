import math
from sklearn.svm import SVR
from sklearn.feature_extraction.text import CountVectorizer

try:
    X = CountVectorizer().fit_transform([
        "alpha beta", "delta", "gamma", "delta"
    ])
    y = [0.04, 0.04, 0.10, 0.16]

    model = SVR(
        C=316.227766017, cache_size=200, coef0=0.0, degree=3,
        epsilon=0.1, gamma=1.0, kernel="linear", max_iter=15000,
        shrinking=True, tol=0.001, verbose=False,
    ).fit(X, y)

    assert model.support_vectors_.shape[0] == 0
    assert model.dual_coef_.shape == (1, 0)
    assert model.dual_coef_.nnz == 0

    predictions = model.predict(X)
    assert len(predictions) == len(y)
    assert all(math.isfinite(value) for value in predictions)
    assert all(abs(prediction - target) <= 0.1 + 1e-12
               for prediction, target in zip(predictions, y))

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc) or 'assertion failed')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
