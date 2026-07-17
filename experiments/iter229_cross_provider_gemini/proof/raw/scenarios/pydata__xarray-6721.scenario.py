from xarray.core.common import get_chunksizes


class Data:
    chunks = ((2,),)


class Variable:
    _data = Data()
    chunks = None
    chunksizes = {"x": (2,)}


print(f"RESULT={get_chunksizes([Variable()])!r}")
