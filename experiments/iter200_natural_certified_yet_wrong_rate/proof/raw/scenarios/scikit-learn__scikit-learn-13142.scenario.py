from sklearn.mixture import GaussianMixture
import numpy as np


class ProbeGaussianMixture(GaussianMixture):
    def _set_parameters(self, params):
        self.set_parameter_calls_ = getattr(self, "set_parameter_calls_", 0) + 1
        return super()._set_parameters(params)


X = np.array([[0.0], [1.0], [2.0]], dtype=float)
model = ProbeGaussianMixture(
    n_components=1,
    n_init=2,
    max_iter=0,
    random_state=0,
)
labels = model.fit_predict(X)

print("RESULT=" + repr((labels.tolist(), model.set_parameter_calls_)))
