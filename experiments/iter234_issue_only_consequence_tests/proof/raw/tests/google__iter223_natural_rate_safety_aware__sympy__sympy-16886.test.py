try:
    from sympy.crypto.crypto import encode_morse, decode_morse
    
    # Check that '1' encodes to the correct Morse code sequence
    encoded = encode_morse('1')
    if encoded != '.----':
        raise AssertionError(f"encode_morse('1') returned {encoded!r}, expected '.----'")
        
    # Check that the correct Morse code sequence decodes back to '1'
    decoded = decode_morse('.----')
    if decoded != '1':
        raise AssertionError(f"decode_morse('.----') returned {decoded!r}, expected '1'")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as e:
    print(f"RESULT={('FAIL', str(e))!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
