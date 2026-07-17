import xarray as xr

ds = xr.Dataset(
    {"a": ("x", [1, 2])},
    coords={"label": ("x", [10, 20])},
)

original_set_coords = xr.Dataset.set_coords
calls = []

def tracked_set_coords(self, names, *args, **kwargs):
    calls.append(tuple(sorted(names)))
    return original_set_coords(self, names, *args, **kwargs)

xr.Dataset.set_coords = tracked_set_coords
try:
    ds.rolling(x=2).construct("window")
    print(f"RESULT={len(calls)!r}")
finally:
    xr.Dataset.set_coords = original_set_coords
