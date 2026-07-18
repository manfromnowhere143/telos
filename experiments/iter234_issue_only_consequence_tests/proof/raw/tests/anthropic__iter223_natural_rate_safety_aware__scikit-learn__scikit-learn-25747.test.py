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
    expected = make_union(MyTransformer()).fit_transform(data)

    set_config(transform_output="pandas")
    result = make_union(MyTransformer()).fit_transform(data)

    # The aggregated result has a different index than the original input.
    # A correct implementation must NOT force the original index onto it.
    n_groups = len(set(index.date))
    if result.shape[0] != n_groups:
        print(f"RESULT={('FAIL', f'wrong rows {result.shape[0]}')!r}")
    else:
        import numpy as np

        vals = np.asarray(result).ravel()
        exp_vals = np.asarray(expected).ravel()
        if not np.allclose(vals, exp_vals):
            print(f"RESULT={('FAIL', 'values differ')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
finally:
    try:
        set_config(transform_output="default")
    except Exception:
        pass
