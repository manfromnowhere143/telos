try:
    from sympy import Quaternion, sqrt

    q = Quaternion(sqrt(2) / 2, sqrt(2) / 2, 0, 0)
    if not hasattr(q, "to_rotation_matrix"):
        raise AttributeError("to_rotation_matrix")
    result = q.to_rotation_matrix().tolist()
    print(f"RESULT={repr(result)}")
except Exception as exc:
    print(f"RESULT={repr(('ERROR', type(exc).__name__))}")
