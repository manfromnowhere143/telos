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
    data = pd.DataFrame({"value": [10] * len(index)}, index=index)
    data["date"] = index.date

    set_config(transform_output="pandas")
    result = make_union(DailySum()).fit_transform(data)
    print(
        "RESULT="
        + repr(
            (
                type(result).__name__,
                getattr(result, "shape", None),
                tuple(str(value) for value in result.index),
                tuple(result.iloc[:, 0]),
            )
        )
    )
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
