import numpy as np
from xarray.coding.variables import UnsignedIntegerCoder
from xarray.core import indexing


class UnsignedBackend(indexing.BackendArray):
    def __init__(self):
        self._values = np.array([255, 0, 127], dtype=np.uint8)

    @property
    def dtype(self):
        return self._values.dtype

    @property
    def shape(self):
        return self._values.shape

    def _raw_indexing_method(self, key):
        if hasattr(key, "tuple"):
            key = key.tuple
        return self._values[key]


class Source:
    dims = ("x",)
    attrs = {"_Unsigned": "false", "_FillValue": np.uint8(255)}
    encoding = {}

    def __init__(self):
        self.data = indexing.LazilyIndexedArray(UnsignedBackend())


decoded = UnsignedIntegerCoder().decode(Source())
result = (decoded.values.tolist(), decoded.attrs["_FillValue"].item(), str(decoded.dtype))
print("RESULT=" + repr(result))
