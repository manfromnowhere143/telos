import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import VotingClassifier


class SupportsSampleWeight(BaseEstimator, ClassifierMixin):
    def fit(self, X, y, sample_weight=None):
        self.classes_ = np.unique(y)
        return self

    def predict(self, X):
        return np.full(len(X), self.classes_[0])


model = VotingClassifier(
    estimators=[("supported", SupportsSampleWeight()), ("removed", None)]
)
model.fit(
    np.array([[0.0], [1.0]]),
    np.array([0, 1]),
    sample_weight=np.array([1.0, 1.0]),
)

print("RESULT=" + repr("ok"))
