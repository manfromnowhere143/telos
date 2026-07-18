import warnings
import numpy as np
from sklearn.mixture import GaussianMixture

try:
    class TrackingGaussianMixture(GaussianMixture):
        def __setattr__(self, name, value):
            if name == "weights_":
                count = getattr(self, "weight_assignment_count", 0)
                object.__setattr__(self, "weight_assignment_count", count + 1)
            object.__setattr__(self, name, value)

    X = np.array([
        [-2.0, -2.0],
        [-1.8, -2.1],
        [-2.2, -1.9],
        [2.0, 2.0],
        [2.2, 1.9],
        [1.8, 2.1],
    ])

    model = TrackingGaussianMixture(
        n_components=2, n_init=2, max_iter=1, random_state=0
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if hasattr(model, "fit_predict"):
            model.fit_predict(X)
        elif hasattr(model, "fit") and hasattr(model, "predict"):
            model.fit(X)
            model.predict(X)
        else:
            raise AttributeError("no public fitting entry point")

    result = getattr(model, "weight_assignment_count", 0)
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print("RESULT=" + repr(result))
