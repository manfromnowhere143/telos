from sklearn import set_config
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.datasets import load_iris
from sklearn.pipeline import make_union

try:
    class DailyLikeAggregate(BaseEstimator, TransformerMixin):
        def fit(self, X, y=None):
            return self

        def transform(self, X):
            return X["sepal length (cm)"].groupby(X["target"]).sum()

    data = load_iris(as_frame=True).frame
    set_config(transform_output="pandas")
    result = make_union(DailyLikeAggregate()).fit_transform(data)

    if len(result) != 3:
        raise AssertionError("aggregated_row_count")
    if tuple(result.index) != (0, 1, 2):
        raise AssertionError("aggregate_index_not_preserved")
    if tuple(result.iloc[:, 0]) != (250.3, 296.5, 329.4):
        raise AssertionError("aggregate_values_changed")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc) or 'assertion')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
