from sympy.tensor.array.dense_ndim_array import ImmutableDenseNDimArray

class FalseShape(tuple):
    def __bool__(self):
        return False

a = ImmutableDenseNDimArray._new([1, 2], FalseShape((2,)))
print("RESULT=" + repr(len(a)))
