import numpy as np
import xarray as xr

arr = xr.DataArray(np.arange(3), coords=[("x", [0, 1, 2])])
stacked = xr.Dataset({"a": arr, "b": arr}).to_stacked_array("y", sample_dims=["x"])
unstacked = stacked.to_unstacked_dataset("y")

result = (
    tuple(unstacked.data_vars),
    tuple(unstacked.coords),
    tuple(
        (name, tuple(unstacked[name].dims), tuple(unstacked[name].values.tolist()))
        for name in unstacked.data_vars
    ),
)
print("RESULT=" + repr(result))
