import numpy as np
import xarray as xr

x = xr.DataArray([1, 2], dims="x", attrs={"marker": "x"})
result = xr.where(np.array([True, False]), x, 0, keep_attrs=True)
print("RESULT=" + repr(dict(result.attrs)))
