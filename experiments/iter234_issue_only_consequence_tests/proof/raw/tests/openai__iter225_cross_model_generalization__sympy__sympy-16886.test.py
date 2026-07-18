try:
    from sympy.crypto import encode_morse, decode_morse

    message = "1901"
    expected = ".---- ----. ----- .----"
    encoded = encode_morse(message)

    if encoded != expected:
        raise AssertionError("incorrect digit encoding")
    if decode_morse(expected) != message:
        raise AssertionError("correct Morse one does not decode")
    if decode_morse(encoded) != message:
        raise AssertionError("digit round trip failed")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion failed"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
