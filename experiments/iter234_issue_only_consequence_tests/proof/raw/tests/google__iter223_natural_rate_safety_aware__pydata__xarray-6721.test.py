import xarray as xr

class LazyExplodingArray:
    shape = (10,)
    ndim = 1

    @property
    def dtype(self):
        return xr.DataArray([1]).dtype

    def __array__(self, *args, **kwargs):
        raise RuntimeError("DATA_LOADED")

    def __getitem__(self, key):
        raise RuntimeError("DATA_LOADED")

def main():
    try:
        ds = xr.Dataset()
        var = xr.Variable(["x"], [1.0] * 10)
        # Bypassing constructor to simulate a custom backend array
        # lacking __array_function__, which previously triggered 
        # a fallback to memory-loading during .chunks access.
        var._data = LazyExplodingArray()
        ds["a"] = var
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")
        return

    try:
        # The core assertion: this should not trigger __array__
        _ = ds.chunks
        print(f"RESULT={('PASS',)!r}")
    except RuntimeError as e:
        if str(e) == "DATA_LOADED":
            print(f"RESULT={('FAIL', 'Accessing chunks loaded data into memory')!r}")
        else:
            print(f"RESULT={('ERROR', type(e).__name__)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
