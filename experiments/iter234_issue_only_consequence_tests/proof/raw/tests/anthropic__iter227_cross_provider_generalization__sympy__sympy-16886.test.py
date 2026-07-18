try:
    from sympy.crypto.crypto import encode_morse, decode_morse

    # "1" should encode to ".----"
    encoded = encode_morse("1")
    assert encoded == ".----", f"encode 1 -> {encoded}"

    # ".----" should decode to "1"
    decoded = decode_morse(".----")
    assert decoded == "1", f"decode .---- -> {decoded}"

    # Round trip for all digits
    digits = "1234567890"
    enc = encode_morse(digits)
    dec = decode_morse(enc)
    assert dec == digits, f"roundtrip digits -> {dec}"

    # "----" should not decode to "1"
    try:
        bad = decode_morse("----")
        assert bad != "1", f"---- wrongly decodes to 1"
    except (KeyError, ValueError):
        pass

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
