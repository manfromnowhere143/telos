try:
    import sympy
    import sympy.tensor.array as array_api

    if hasattr(sympy, "MutableDenseNDimArray"):
        Base = getattr(sympy, "MutableDenseNDimArray")
    elif hasattr(array_api, "MutableDenseNDimArray"):
        Base = getattr(array_api, "MutableDenseNDimArray")
    else:
        raise AttributeError("MutableDenseNDimArray")

    assignments = []

    class Probe(Base):
        def __setattr__(self, name, value):
            assignments.append(1)
            object.__setattr__(self, name, value)

    Probe([1], (1,))
    print(f"RESULT={len(assignments)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
