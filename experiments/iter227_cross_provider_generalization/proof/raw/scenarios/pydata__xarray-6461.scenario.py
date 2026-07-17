import numpy as np
import xarray as xr

cond = xr.DataArray([True, False], dims="d")
x = np.array([1, 2])
y = xr.DataArray([3, 4], dims="d", attrs={"source": "y"})

result = xr.where(cond, x, y, keep_attrs=True)

print(f"RESULT={dict(result.attrs)!r}")
