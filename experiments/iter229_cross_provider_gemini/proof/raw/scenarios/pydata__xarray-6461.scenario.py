import xarray as xr

cond = xr.DataArray([True], attrs={"condition_attr": "present"})
result = xr.where(cond, 1, 0, keep_attrs=True)
print(f"RESULT={result.attrs!r}")
