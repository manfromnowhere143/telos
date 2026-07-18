import sympy
from sympy.tensor.array import (
    MutableDenseNDimArray, ImmutableDenseNDimArray,
    MutableSparseNDimArray, ImmutableSparseNDimArray
)

def test():
    try:
        x = sympy.Symbol('x')
        
        # Test various rank-0 arrays (scalars)
        arrays_to_test = [
            sympy.Array(3),
            sympy.Array(x),
            MutableDenseNDimArray(3.14),
            ImmutableDenseNDimArray(x),
            MutableSparseNDimArray(100),
            ImmutableSparseNDimArray(x),
        ]
        
        for i, a in enumerate(arrays_to_test):
            if len(a) != 1:
                return "FAIL", f"len of rank-0 array (type {type(a).__name__}) is {len(a)}, expected 1"
            
            # The issue also mentions that the length of the iterator is 1
            if len(list(a)) != 1:
                return "FAIL", f"len of list(a) (type {type(a).__name__}) is {len(list(a))}, expected 1"
                
            # Verify it is indeed rank 0
            if a.rank() != 0:
                return "FAIL", f"Array is not rank 0, rank is {a.rank()}"
                
        return "PASS",
    except Exception as e:
        return "ERROR", type(e).__name__

if __name__ == "__main__":
    result = test()
    if len(result) == 1:
        print(f"RESULT={result!r}")
    else:
        print(f"RESULT={result!r}")
