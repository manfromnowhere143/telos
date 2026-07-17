from sympy.tensor.array.dense_ndim_array import MutableDenseNDimArray

array = MutableDenseNDimArray._new(7, ())
print("RESULT=" + repr(array._loop_size))
