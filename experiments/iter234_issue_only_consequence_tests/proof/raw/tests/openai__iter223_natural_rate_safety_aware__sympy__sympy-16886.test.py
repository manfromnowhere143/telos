import sympy
from sympy.crypto.crypto import decode_morse, encode_morse

try:
    assert encode_morse("1") == ".----"
    assert decode_morse(".----") == "1"
    assert decode_morse("----") != "1"
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "morse-one"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
