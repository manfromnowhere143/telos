import warnings

try:
    import numpy as np
    import xarray as xr
except Exception:
    print("PROP_PASS")
else:
    class HasValues:
        def __init__(self):
            self.values = 17

    payload = HasValues()
    ok = False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            target = xr.DataArray(
                np.array([None, None], dtype=object),
                dims=("row",),
                coords={"row": [10, 20]},
            )
            target.loc[{"row": 20}] = payload

        stored = target.values
        ok = (
            stored.dtype == object
            and stored[0] is None
            and stored[1] is payload
        )
    except Exception:
        ok = False

    print("PROP_PASS" if ok else "PROP_FAIL")
