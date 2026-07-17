from sympy.tensor.array.dense_ndim_array import ImmutableDenseNDimArray

array = ImmutableDenseNDimArray._new([0], (True,))
print("RESULT=" + repr(array._loop_size))
