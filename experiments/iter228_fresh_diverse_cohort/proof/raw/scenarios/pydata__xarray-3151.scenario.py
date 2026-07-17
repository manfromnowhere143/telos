import xarray as xr

left = xr.Dataset({"value": ("x", [1])}, coords={"x": [0]})
right = xr.Dataset({"value": ("x", [2])}, coords={"x": [1]})

combined = xr.combine_by_coords([left, right])
print("RESULT={!r}".format(combined["value"].values.tolist()))
