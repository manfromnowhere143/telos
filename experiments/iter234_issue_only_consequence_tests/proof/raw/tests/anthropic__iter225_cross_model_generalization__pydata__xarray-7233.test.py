try:
    import numpy as np
    import xarray as xr

    da = xr.DataArray(np.arange(24), dims=["time"])
    da = da.assign_coords(day=365 * da)
    ds = da.to_dataset(name="T")

    result = ds.coarsen(time=12).construct(time=("year", "month"))

    # 'day' was a non-dimensional coordinate; it must remain a coordinate
    assert "day" in result.coords, "day not in coords"
    assert "day" not in result.data_vars, "day demoted to data var"

    # Check DataArray path too
    da_result = da.coarsen(time=12).construct(time=("year", "month"))
    assert "day" in da_result.coords, "day not in coords (DataArray)"

    # Check values preserved and reshaped
    expected = (365 * np.arange(24)).reshape(2, 12)
    assert np.array_equal(result["day"].values, expected), "day values wrong"
    assert result["day"].dims == ("year", "month"), "day dims wrong"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
