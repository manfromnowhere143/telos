import warnings
import numpy as np

from sklearn.linear_model.logistic import _log_reg_scoring_path

warnings.filterwarnings("ignore")

X = np.array([
    [-2.0, -1.0],
    [-1.5, -2.0],
    [2.0, -1.0],
    [1.5, -2.0],
    [0.0, 2.0],
    [0.5, 1.5],
])
y = np.array([0, 0, 1, 1, 2, 2])
indices = np.arange(y.size)


def probabilistic_scorer(estimator, X_test, y_test):
    estimator.predict_proba(X_test)
    return float(estimator.fit_intercept)


result = _log_reg_scoring_path(
    X,
    y,
    train=indices,
    test=indices,
    Cs=[1.0],
    scoring=probabilistic_scorer,
    solver="lbfgs",
    multi_class="multinomial",
    fit_intercept=False,
    max_iter=100,
)

score = float(np.asarray(result[2]).ravel()[0])
print("RESULT=" + repr(score))
