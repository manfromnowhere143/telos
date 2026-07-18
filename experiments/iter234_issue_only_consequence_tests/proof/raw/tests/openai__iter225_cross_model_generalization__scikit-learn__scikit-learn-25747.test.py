from sklearn import set_config
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_union
from sklearn.preprocessing import StandardScaler
import math

try:
    class AggregateToOneRow(BaseEstimator, TransformerMixin):
        def fit(self, X, y=None):
            return self

        def transform(self, X):
            result = X.iloc[[0]].copy()
            result.iloc[0, 0] = X.iloc[:, 0].sum()
            result.index = ["all"]
            return result

    X = StandardScaler().set_output(transform="pandas").fit_transform(
        [[1], [2], [3], [4]]
    )
    set_config(transform_output="pandas")
    result = make_union(AggregateToOneRow()).fit_transform(X)

    assert result.shape == (1, 1), "aggregation shape changed"
    assert list(result.index) == ["all"], "aggregated index not preserved"
    assert math.isclose(float(result.iloc[0, 0]), 0.0, abs_tol=1e-12), "wrong aggregate"
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
