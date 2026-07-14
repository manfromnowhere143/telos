import xarray as xr
import numpy as np

ds1 = xr.Dataset(
    {"data": (("x", "y"), np.array([[1, 2], [3, 4]]))},
    coords={"x": [4, 3], "y": ["b", "a"]},
)
ds2 = xr.Dataset(
    {"data": (("x", "y"), np.array([[5, 6], [7, 8]]))},
    coords={"x": [2, 1], "y": ["b", "a"]},
)

result = xr.combine_by_coords([ds1, ds2])
print("RESULT=" + repr(result["x"].values.tolist()))
