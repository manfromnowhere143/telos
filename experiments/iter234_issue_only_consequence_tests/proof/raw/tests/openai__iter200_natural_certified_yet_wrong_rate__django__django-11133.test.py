from django.http import HttpResponse

try:
    source = bytearray(b"0Mxy Czoqnet9")
    view = memoryview(source)[1:-1:2]
    response = HttpResponse(view)

    if response.content != b"My Content":
        raise AssertionError("sliced memoryview was not converted to its bytes")

    source[1] = ord("X")
    if response.content != b"My Content":
        raise AssertionError("response content did not preserve memoryview bytes")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion failed"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
