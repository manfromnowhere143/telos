try:
    import django
    from enum import Enum
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    if not hasattr(django, "setup"):
        raise AttributeError("setup")
    django.setup()

    from django.db.migrations.serializer import EnumSerializer

    if not hasattr(EnumSerializer, "serialize"):
        raise AttributeError("serialize")

    Status = Enum("Status", {'A"B': "value"})
    result = EnumSerializer(Status['A"B']).serialize()
    print(f"RESULT={result!r}")
except BaseException as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
