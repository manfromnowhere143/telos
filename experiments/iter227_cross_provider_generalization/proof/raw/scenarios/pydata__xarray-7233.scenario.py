import xarray as xr

obj = xr.Dataset(
    data_vars={"value": ("x", [1, 2])},
    coords={"metadata": 1},
)

result = obj.rolling(x=2).construct("window")

print(f"RESULT={repr((tuple(result.coords), tuple(result.data_vars)))}")
