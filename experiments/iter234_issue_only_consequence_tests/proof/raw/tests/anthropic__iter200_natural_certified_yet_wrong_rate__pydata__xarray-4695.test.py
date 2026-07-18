try:
    import numpy as np
    from xarray import DataArray, Dataset

    empty = np.zeros((2, 2))
    D2 = DataArray(empty, dims=['dim1', 'method'],
                   coords={'dim1': ['x', 'y'], 'method': ['a', 'b']})

    # .loc with dict selecting on dim named "method"
    r = D2.loc[dict(dim1='x', method='a')]
    assert r.values == 0.0, "value mismatch"
    assert r.coords['dim1'].item() == 'x', "dim1 coord wrong"
    assert r.coords['method'].item() == 'a', "method coord wrong"

    # also test other reserved-name dims like "tolerance"
    D3 = DataArray(np.arange(4).reshape(2, 2), dims=['tolerance', 'method'],
                   coords={'tolerance': [10, 20], 'method': ['a', 'b']})
    r3 = D3.loc[dict(tolerance=20, method='b')]
    assert r3.item() == 3, "tolerance/method selection wrong"

    # .sel should also work with such dim names
    r4 = D2.sel(dim1='y', method='b')
    assert r4.item() == 0.0, "sel value wrong"
    assert r4.coords['method'].item() == 'b', "sel method coord wrong"

    # Dataset case
    ds = Dataset({'v': (['dim1', 'method'], empty)},
                 coords={'dim1': ['x', 'y'], 'method': ['a', 'b']})
    rds = ds.loc[dict(method='a')]
    assert list(rds['method'].values) == ['a'] or rds['method'].item() == 'a', "ds loc wrong"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
