import numpy as np
import xarray as xr

data = xr.DataArray(np.ones((2, 2)), dims=("x", "y"))
weights = xr.DataArray(np.ones((2, 2), dtype=bool), dims=("x", "y"))

print("RESULT=" + repr(data.weighted(weights).mean().item()))
