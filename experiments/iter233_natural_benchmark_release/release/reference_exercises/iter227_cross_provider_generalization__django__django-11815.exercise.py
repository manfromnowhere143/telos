try:
    from enum import Enum
    import django
    from django.conf import settings
    from django.db.migrations.writer import MigrationWriter
    from django.utils.translation import gettext_lazy

    if not settings.configured:
        settings.configure(
            SECRET_KEY="fixture",
            INSTALLED_APPS=[],
            USE_I18N=True,
        )
    django.setup()

    class Status(Enum):
        GOOD = gettext_lazy("Good")
        BAD = gettext_lazy("Bad")

    OddStatus = Enum("OddStatus", {"GOOD'QUOTE": gettext_lazy("Good")})

    normal, normal_imports = MigrationWriter.serialize(Status.GOOD)
    odd, odd_imports = MigrationWriter.serialize(OddStatus["GOOD'QUOTE"])
    observed = (
        (normal, tuple(sorted(normal_imports))),
        (odd, tuple(sorted(odd_imports))),
    )
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
