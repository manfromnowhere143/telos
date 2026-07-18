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

    set_config(transform_output="default")
    default_out = make_union(MyTransformer()).fit_transform(data)

    set_config(transform_output="pandas")
    pandas_out = make_union(MyTransformer()).fit_transform(data)
    set_config(transform_output="default")

    # Aggregated result has one row per unique date (4 days)
    n_days = len(set(data["date"]))
    if pandas_out.shape[0] != n_days:
        print(f"RESULT={('FAIL', f'rows {pandas_out.shape[0]} != {n_days}')!r}")
    else:
        # Values should match the aggregated sums (each day: 24 * 10 = 240)
        vals = pandas_out.to_numpy().ravel()
        expected = default_out.ravel() if hasattr(default_out, "ravel") else default_out.to_numpy().ravel()
        if not (vals == expected).all():
            print(f"RESULT={('FAIL', 'values mismatch')!r}")
        elif not (vals == 240).all():
            print(f"RESULT={('FAIL', 'unexpected sums')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
