import xarray as xr

try:
    class LazyArray:
        def __init__(self, shape, chunks=None):
            self.shape = shape
            self.ndim = len(shape)
            self.dtype = "int64"
            self._chunks = chunks
            self.accesses = 0

        @property
        def chunks(self):
            return self._chunks

        def __array__(self, *args, **kwargs):
            self.accesses += 1
            raise AssertionError("lazy data was loaded")

        def __getitem__(self, key):
            self.accesses += 1
            raise AssertionError("lazy data was indexed")

        def __array_function__(self, *args, **kwargs):
            return NotImplemented

        def __array_ufunc__(self, *args, **kwargs):
            return NotImplemented

    chunked = LazyArray((5, 4), ((2, 2, 1), (3, 1)))
    unchunked = LazyArray((5, 4))
    ds = xr.Dataset(
        {
            "stored": xr.Variable(
                ("row", "column"), chunked, encoding={"chunks": (2, 3)}
            ),
            "other": xr.Variable(("row", "column"), unchunked),
        }
    )

    actual = dict(ds.chunks)
    expected = {"row": (2, 2, 1), "column": (3, 1)}
    assert actual == expected, "incorrect chunk mapping"
    assert chunked.accesses == 0 and unchunked.accesses == 0, "data accessed"
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
