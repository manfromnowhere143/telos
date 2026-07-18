try:
    import numpy as np
    import pandas as pd
    import sklearn
    import sklearn.pipeline as pipeline
    from sklearn.base import BaseEstimator, TransformerMixin

    if not hasattr(sklearn, "set_config") or not hasattr(pipeline, "make_union"):
        raise RuntimeError("required public API unavailable")

    class Aggregator(BaseEstimator, TransformerMixin):
        def fit(self, X, y=None):
            return self

        def transform(self, X):
            return X[["value"]].groupby(X["date"]).sum()

        def get_feature_names_out(self, input_features=None):
            return np.asarray(["value"], dtype=object)

    index = pd.date_range("2020-01-01", periods=48, freq="h")
    data = pd.DataFrame({"value": 1, "date": index.date}, index=index)

    sklearn.set_config(transform_output="pandas")
    union = pipeline.make_union(Aggregator())
    if not hasattr(union, "fit_transform"):
        raise RuntimeError("fit_transform unavailable")

    output = union.fit_transform(data)
    result = (
        type(output).__name__,
        tuple(str(value) for value in output.index),
        tuple(str(column) for column in output.columns),
        tuple(int(value) for value in output.iloc[:, 0]),
    )
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
