import xarray as xr
import numpy as np

try:
    class TrackingArray:
        """Lazy array that records if its data is ever accessed."""
        def __init__(self, arr):
            self.arr = arr
            self.shape = arr.shape
            self.dtype = arr.dtype
            self.ndim = arr.ndim
            self.accessed = False

        def __array__(self, dtype=None):
            self.accessed = True
            return np.asarray(self.arr, dtype=dtype)

        def __getitem__(self, key):
            self.accessed = True
            return self.arr[key]

    raw = np.arange(24, dtype=float).reshape(4, 6)
    tracker = TrackingArray(raw)
    lazy = xr.core.indexing.LazilyIndexedArray(tracker)
    var = xr.Variable(("x", "y"), lazy)
    ds = xr.Dataset({"foo": var})

    # Accessing chunks should NOT load the data into memory
    chunks = ds.chunks

    if tracker.accessed:
        print(f"RESULT={('FAIL', 'chunks loaded data into memory')!r}")
    else:
        # data is not dask-backed, so chunks should be empty
        assert dict(chunks) == {}, f"expected empty chunks, got {dict(chunks)}"
        # Also test on DataArray
        da = ds["foo"]
        _ = da.chunks
        assert not tracker.accessed, "DataArray.chunks loaded data"
        print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
