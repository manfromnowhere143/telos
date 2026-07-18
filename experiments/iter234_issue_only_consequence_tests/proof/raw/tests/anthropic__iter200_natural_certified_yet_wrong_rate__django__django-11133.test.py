try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEFAULT_CHARSET='utf-8')
    django.setup()
    from django.http import HttpResponse

    detail = None

    # memoryview at construction
    r = HttpResponse(memoryview(b"My Content"))
    if r.content != b"My Content":
        detail = f"construct: {r.content!r}"

    # memoryview assigned to content
    if detail is None:
        r2 = HttpResponse()
        r2.content = memoryview(b"Other Data")
        if r2.content != b"Other Data":
            detail = f"assign: {r2.content!r}"

    # memoryview over a bytearray slice
    if detail is None:
        mv = memoryview(bytearray(b"abcdef"))[1:4]
        r3 = HttpResponse(mv)
        if r3.content != b"bcd":
            detail = f"slice: {r3.content!r}"

    # empty memoryview
    if detail is None:
        r4 = HttpResponse(memoryview(b""))
        if r4.content != b"":
            detail = f"empty: {r4.content!r}"

    if detail is None:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
