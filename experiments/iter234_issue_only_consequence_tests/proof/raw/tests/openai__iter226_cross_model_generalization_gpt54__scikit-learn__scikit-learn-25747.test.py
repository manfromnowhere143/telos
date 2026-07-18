from sklearn import set_config
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.datasets import load_iris
from sklearn.pipeline import make_union

try:
    class AggregateByTarget(BaseEstimator, TransformerMixin):
        def fit(self, X, y=None):
            return self

        def transform(self, X):
            return X["sepal length (cm)"].groupby(X["target"]).sum()

    data = load_iris(as_frame=True).frame
    set_config(transform_output="pandas")
    result = make_union(AggregateByTarget()).fit_transform(data)

    if result.shape != (3, 1):
        raise AssertionError("unexpected shape")
    if list(result.index) != [0, 1, 2]:
        raise AssertionError("group index not preserved")
    expected = [250.3, 296.8, 329.4]
    if any(abs(a - b) > 1e-9 for a, b in zip(result.iloc[:, 0], expected)):
        raise AssertionError("wrong aggregates")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
