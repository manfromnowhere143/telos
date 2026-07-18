try:
    import numpy as np
    import xarray as xr

    da = xr.DataArray(np.arange(24), dims=["time"])
    da = da.assign_coords(day=365 * da)
    ds = da.to_dataset(name="T")

    result = ds.coarsen(time=12).construct(time=("year", "month"))

    detail = None
    # day must remain a coordinate
    if "day" not in result.coords:
        detail = "day not in coords"
    elif "day" in result.data_vars:
        detail = "day demoted to data var"
    elif result["day"].dims != ("year", "month"):
        detail = f"unexpected dims {result['day'].dims}"
    elif "T" not in result.data_vars:
        detail = "T not in data_vars"
    else:
        # also test DataArray.coarsen.construct keeps coords
        da_res = da.coarsen(time=12).construct(time=("year", "month"))
        if "day" not in da_res.coords:
            detail = "da: day not in coords"

    if detail is None:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
