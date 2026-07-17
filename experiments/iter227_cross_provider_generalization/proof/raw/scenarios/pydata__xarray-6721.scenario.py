from xarray.core.common import get_chunksizes


class Data:
    chunks = ((1,),)


class VariableLike:
    def __init__(self):
        self._data = Data()
        self.calls = 0

    @property
    def chunksizes(self):
        self.calls += 1
        return {"x": (self.calls,)}


try:
    result = get_chunksizes([VariableLike()])
except Exception as exc:
    result = type(exc).__name__

print(f"RESULT={result!r}")
