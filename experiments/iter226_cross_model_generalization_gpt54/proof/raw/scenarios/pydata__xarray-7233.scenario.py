import xarray as xr

obj = xr.Dataset(
    {"value": ("x", [1, 2, 3])},
    coords={"label": ("x", ["a", "b", "c"])},
)

result = obj.rolling(x=2).construct("window")
print(f"RESULT={repr(('label' in result.coords, 'label' in result.data_vars, result['label'].dims))}")
