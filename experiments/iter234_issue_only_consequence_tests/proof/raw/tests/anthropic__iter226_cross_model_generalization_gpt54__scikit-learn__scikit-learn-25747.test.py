try:
    import pandas as pd
    from sklearn.base import BaseEstimator, TransformerMixin
    from sklearn import set_config
    from sklearn.pipeline import make_union

    index = pd.date_range(
        start="2020-01-01", end="2020-01-05", inclusive="left", freq="H"
    )
    data = pd.DataFrame(index=index, data=[10] * len(index), columns=["value"])
    data["date"] = index.date

    class MyTransformer(BaseEstimator, TransformerMixin):
        def fit(self, X, y=None, **kwargs):
            return self

        def transform(self, X, y=None):
            return X["value"].groupby(X["date"]).sum()

        def get_feature_names_out(self, input_features=None):
            return ["value"]

    set_config(transform_output="default")
    expected = make_union(MyTransformer()).fit_transform(data)

    set_config(transform_output="pandas")
    result = make_union(MyTransformer()).fit_transform(data)
    set_config(transform_output="default")

    # aggregated output: 4 unique dates
    if result.shape[0] != 4:
        print(f"RESULT={('FAIL', 'wrong nrows')!r}")
    else:
        import numpy as np
        vals_result = np.asarray(result).ravel().astype(float)
        vals_expected = np.asarray(expected).ravel().astype(float)
        if not np.allclose(sorted(vals_result), sorted(vals_expected)):
            print(f"RESULT={('FAIL', 'values differ')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    try:
        set_config(transform_output="default")
    except Exception:
        pass
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
