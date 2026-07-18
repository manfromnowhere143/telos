try:
    import xarray as xr

    data = xr.DataArray(
        [[10, 11, 12], [20, 21, 22]],
        dims=("row", "method"),
        coords={"row": ["first", "second"], "method": ["a", "b", "c"]},
    )

    selected = data.loc[{"method": slice("b", "c"), "row": "second"}]

    assert selected.dims == ("method",)
    assert selected["method"].values.tolist() == ["b", "c"]
    assert selected.isel({"method": 0}).item() == 21
    assert selected.isel({"method": 1}).item() == 22
except AssertionError:
    print(f"RESULT={('FAIL', 'method dimension loc selection')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
