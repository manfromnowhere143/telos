from sklearn.base import BaseEstimator, clone
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

try:
    class EstimatorClassHolder(BaseEstimator):
        def __init__(self, transformer=StandardScaler, predictor=LinearRegression):
            self.transformer = transformer
            self.predictor = predictor

    original = EstimatorClassHolder(
        transformer=StandardScaler,
        predictor=LinearRegression,
    )
    copied = clone(original)

    assert copied is not original
    assert copied.transformer is StandardScaler
    assert copied.predictor is LinearRegression
    assert copied.get_params(deep=False) == original.get_params(deep=False)

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "cloned estimator classes were not preserved"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
