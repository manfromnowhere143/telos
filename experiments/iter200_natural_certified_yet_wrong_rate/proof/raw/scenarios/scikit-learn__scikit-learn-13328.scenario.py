import warnings
import numpy as np
from sklearn.linear_model import HuberRegressor

X = np.array(
    [[False, False], [False, True], [True, False], [True, True]] * 5,
    dtype=bool,
)
y = np.array([1.0, 0.2, 3.1, 2.3] * 5)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    model = HuberRegressor(max_iter=1000).fit(X, y)

print("RESULT=" + repr(model.coef_.dtype.name))
