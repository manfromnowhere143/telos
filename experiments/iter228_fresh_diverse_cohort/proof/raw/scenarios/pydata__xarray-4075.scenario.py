import xarray as xr

data = xr.DataArray([1.0, 2.0], dims="x")
weights = xr.DataArray([True, True], dims="x")

result = data.weighted(weights).sum_of_weights(dim="x")
print(f"RESULT={result.item()!r}")
