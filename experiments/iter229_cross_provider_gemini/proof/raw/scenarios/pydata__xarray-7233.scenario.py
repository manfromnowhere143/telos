import xarray as xr

data = xr.DataArray([1, 2], dims=("x",), coords={"marker": 7})
result = data.rolling(x=2).construct("window")

print("RESULT=" + repr((tuple(result.coords), result.coords["marker"].item(), result.dims, result.shape)))
