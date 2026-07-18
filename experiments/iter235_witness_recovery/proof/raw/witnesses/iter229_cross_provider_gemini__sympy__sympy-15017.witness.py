try:
    from sympy.tensor.array import ImmutableDenseNDimArray

    class FalsyShape(list):
        def __bool__(self):
            return False

    shape = FalsyShape([2])
    array = ImmutableDenseNDimArray([10, 20], shape=shape)
    result = len(array)
    print(f"RESULT={result!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
