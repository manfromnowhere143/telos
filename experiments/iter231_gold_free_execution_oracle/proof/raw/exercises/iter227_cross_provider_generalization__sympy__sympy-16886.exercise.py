try:
    from sympy.crypto.crypto import encode_morse

    result = tuple((text, encode_morse(text)) for text in ("1", "01", "10", "a1z"))
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
