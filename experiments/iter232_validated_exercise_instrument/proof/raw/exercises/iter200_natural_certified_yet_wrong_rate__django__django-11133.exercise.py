try:
    from django.conf import settings

    if not settings.configured:
        settings.configure(DEFAULT_CHARSET="utf-8")

    from django.http import HttpResponse

    values = (
        memoryview(b"My Content"),
        memoryview(bytearray(b"My Content")),
        memoryview(b"xxMy Contentyy")[2:-2],
    )
    print("RESULT=" + repr(tuple(HttpResponse(value).content for value in values)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
