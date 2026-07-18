import xarray as xr

try:
    class LazyChunkedArray:
        shape = (4,)
        ndim = 1
        dtype = "float64"
        chunks = ((2, 2),)

        def __array__(self, dtype=None):
            raise RuntimeError("chunks access materialized lazy data")

        def __array_function__(self, func, types, args, kwargs):
            return NotImplemented

        def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
            return NotImplemented

        def __getitem__(self, key):
            raise RuntimeError("chunks access indexed lazy data")

    ds = xr.Dataset({"value": (("x",), LazyChunkedArray())})
    observed = tuple(sorted(ds.chunks.items()))
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
