import xarray as xr

cond = xr.DataArray([True], dims="i")
y = xr.DataArray([2], dims="i", attrs={"marker": "y"})
result = xr.where(cond, 1, y, keep_attrs=True)

print("RESULT=" + repr(dict(result.attrs)))
