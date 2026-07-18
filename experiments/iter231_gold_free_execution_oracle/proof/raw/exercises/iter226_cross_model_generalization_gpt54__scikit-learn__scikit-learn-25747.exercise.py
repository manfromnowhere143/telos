import pandas as pd
from sklearn import set_config
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_union

try:
    class DailySum(BaseEstimator, TransformerMixin):
        def fit(self, X, y=None):
            return self

        def transform(self, X):
            return X["value"].groupby(X["date"]).sum()

    index = pd.date_range("2020-01-01", periods=48, freq="h")
    data = pd.DataFrame({"value": [10] * len(index), "date": index.date}, index=index)

    set_config(transform_output="pandas")
    output = make_union(DailySum()).fit_transform(data)
    result = (
        type(output).__name__,
        getattr(output, "shape", None),
        tuple(map(str, getattr(output, "index", ()))),
        getattr(output, "to_numpy", lambda: output)().ravel().tolist(),
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
