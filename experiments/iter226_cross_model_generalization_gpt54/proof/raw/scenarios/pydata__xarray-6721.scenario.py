from xarray.core.common import get_chunksizes


class ChunkedData:
    chunks = ((2,),)


class Variable:
    _data = ChunkedData()

    def __init__(self):
        self.calls = 0

    @property
    def data(self):
        raise AssertionError("data should not be accessed")

    @property
    def chunksizes(self):
        self.calls += 1
        if self.calls == 1:
            return {"x": (2,)}
        return {"x": (3,)}


print(f"RESULT={get_chunksizes([Variable()])!r}")
