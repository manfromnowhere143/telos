from sympy.tensor.array.dense_ndim_array import DenseNDimArray


class Probe(DenseNDimArray):
    def __setattr__(self, name, value):
        self.__dict__.setdefault("_writes", []).append(name)
        object.__setattr__(self, name, value)


obj = Probe._new([1], ())
print("RESULT=" + repr(tuple(obj._writes)))
