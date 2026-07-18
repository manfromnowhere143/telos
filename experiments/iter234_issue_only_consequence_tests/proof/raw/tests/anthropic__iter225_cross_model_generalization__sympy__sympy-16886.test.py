try:
    from sympy.crypto.crypto import encode_morse, decode_morse

    # Encoding "1" should produce ".----"
    enc = encode_morse("1")
    assert enc == ".----", f"encode 1 -> {enc}"

    # Round trip
    dec = decode_morse(".----")
    assert dec == "1", f"decode .---- -> {dec}"

    # The incorrect mapping "----" should NOT decode to "1"
    wrong = decode_morse("----")
    assert wrong != "1", f"---- wrongly decodes to 1"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
