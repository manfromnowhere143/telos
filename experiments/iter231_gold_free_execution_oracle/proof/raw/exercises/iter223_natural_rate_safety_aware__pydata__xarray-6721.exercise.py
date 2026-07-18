import xarray as xr
from xarray.core.indexing import BackendArray, LazilyIndexedArray


class ProbeArray(BackendArray):
    shape = (4,)
    dtype = "float64"

    def __init__(self):
        self.reads = 0

    def _raw_indexing_method(self, key):
        self.reads += 1
        raise RuntimeError("backend data was read")


probe = ProbeArray()

try:
    ds = xr.Dataset({"v": xr.Variable(("x",), LazilyIndexedArray(probe))})
    result = (dict(ds.chunks), probe.reads)
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
