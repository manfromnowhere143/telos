try:
    import xarray as xr

    ds = xr.Dataset(
        {"T": (("time", "x"), [[0, 1], [2, 3], [4, 5], [6, 7]])},
        coords={
            "time": [0, 1, 2, 3],
            "x": ["a", "b"],
            "day": ("time", [0, 365, 730, 1095]),
            "grid": (("time", "x"), [[10, 11], [12, 13], [14, 15], [16, 17]]),
            "label": "example",
        },
    )
    before = tuple(ds.coords)
    result = ds.coarsen(time=2).construct(time=("year", "month"))
    summary = tuple((name, name in result.coords, result[name].dims) for name in before)
    print("RESULT=" + repr(summary))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
