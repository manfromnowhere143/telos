import xarray as xr

class DerivedDataArray(xr.DataArray):
    pass

dataset = xr.Dataset({"a": 0})
other = DerivedDataArray(1, name="b")
merged = dataset.merge(other)

print("RESULT=" + repr(tuple((name, merged[name].item()) for name in merged.data_vars)))
