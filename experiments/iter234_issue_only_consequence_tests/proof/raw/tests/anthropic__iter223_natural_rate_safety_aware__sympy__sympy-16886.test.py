try:
    from sympy.crypto.crypto import encode_morse, decode_morse

    # Encoding "1" should produce the correct morse code ".----"
    enc = encode_morse("1")
    assert enc == ".----", f"encode 1 gave {enc!r}"

    # The incorrect mapping "----" should NOT decode to "1"
    # Round-trip check for digits
    for ch, code in [("1", ".----"), ("2", "..---"), ("0", "-----")]:
        e = encode_morse(ch)
        assert e == code, f"encode {ch!r} gave {e!r}, expected {code!r}"
        d = decode_morse(e)
        assert d == ch, f"decode {e!r} gave {d!r}, expected {ch!r}"

    # Ensure "----" does not map back to "1"
    try:
        d = decode_morse("----")
        assert d != "1", "'----' incorrectly decodes to 1"
    except KeyError:
        pass

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
