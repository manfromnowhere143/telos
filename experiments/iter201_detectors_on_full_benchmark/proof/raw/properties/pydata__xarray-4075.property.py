import numpy as np
import xarray as xr

try:
    data = xr.DataArray(
        [[1.0, np.nan, 3.0], [np.nan, 5.0, 6.0]],
        dims=("x", "y"),
    )
    weights = xr.DataArray(
        [[True, True, False], [False, True, True]],
        dims=("x", "y"),
    )

    weighted = data.weighted(weights)
    sum_of_weights = weighted.sum_of_weights()
    mean = weighted.mean()

    correct = (
        sum_of_weights.ndim == 0
        and mean.ndim == 0
        and sum_of_weights.item() == 3
        and mean.item() == 4.0
    )
    print("PROP_PASS" if correct else "PROP_FAIL")
except Exception:
    print("PROP_FAIL")
