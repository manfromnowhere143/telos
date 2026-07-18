import numpy as np
import xarray as xr

try:
    class UnsignedArray:
        def __init__(self, values):
            self.values = np.asarray(values, dtype=np.uint8)
            self.shape = self.values.shape
            self.ndim = self.values.ndim
            self.size = self.values.size
            self.dtype = self.values.dtype

        def __array__(self, dtype=None):
            return np.asarray(self.values, dtype=dtype)

        def __array_function__(self, func, types, args, kwargs):
            return NotImplemented

        def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
            return NotImplemented

    source = UnsignedArray([255, 0, 127])
    variable = xr.Variable(
        ("x",), source, attrs={"_Unsigned": "false"}
    )
    decoded = xr.decode_cf(xr.Dataset({"v": variable}))
    output = (str(decoded["v"].dtype), tuple(decoded["v"].values.tolist()))
    print(f"RESULT={output!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
