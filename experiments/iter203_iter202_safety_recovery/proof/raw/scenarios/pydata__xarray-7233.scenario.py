import xarray as xr

da = xr.DataArray(range(24), dims="time").assign_coords(
    day=("time", [365 * i for i in range(24)])
)
ds = da.to_dataset(name="T")

calls = [0]
original_set_coords = xr.Dataset.set_coords


def counted_set_coords(self, *args, **kwargs):
    calls[0] += 1
    return original_set_coords(self, *args, **kwargs)


xr.Dataset.set_coords = counted_set_coords
try:
    result = ds.coarsen(time=12).construct(time=("year", "month"))
finally:
    xr.Dataset.set_coords = original_set_coords

print(
    "RESULT="
    + repr(
        (
            calls[0],
            tuple(result.coords),
            tuple(result.data_vars),
            tuple(result.sizes.items()),
        )
    )
)
