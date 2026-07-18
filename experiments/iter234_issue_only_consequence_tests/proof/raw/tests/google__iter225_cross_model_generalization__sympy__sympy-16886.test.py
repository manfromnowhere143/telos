try:
    from sympy.crypto.crypto import encode_morse, decode_morse
    
    enc = encode_morse("1")
    if enc != ".----":
        raise AssertionError(f"encode_morse('1') returned {enc!r} instead of '.----'")
        
    dec = decode_morse(".----")
    if dec != "1":
        raise AssertionError(f"decode_morse('.----') returned {dec!r} instead of '1'")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as e:
    print(f"RESULT={('FAIL', str(e))!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
