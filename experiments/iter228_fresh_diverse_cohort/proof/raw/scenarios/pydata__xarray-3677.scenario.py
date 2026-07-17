import warnings
import xarray as xr

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    xr.Dataset().merge(xr.DataArray(0, name="value"), inplace=False)

print("RESULT=" + repr(len(caught)))
