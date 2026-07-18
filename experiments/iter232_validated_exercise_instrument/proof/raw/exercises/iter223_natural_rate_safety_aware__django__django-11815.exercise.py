try:
    from enum import Enum
    import django
    from django.conf import settings
    from django.db.migrations.writer import MigrationWriter
    from django.utils.translation import gettext_lazy

    if not settings.configured:
        settings.configure(
            SECRET_KEY="fixture",
            USE_I18N=True,
            LANGUAGE_CODE="en",
            INSTALLED_APPS=[],
        )
    django.setup()

    class Status(Enum):
        GOOD = gettext_lazy("Good")
        BAD = gettext_lazy("Bad")

    Quoted = Enum(
        "Quoted",
        {"O'HARE": gettext_lazy("O'Hare")},
        module="fixture_enums",
    )
    observed = (
        MigrationWriter.serialize(Status.GOOD)[0],
        MigrationWriter.serialize(Quoted["O'HARE"])[0],
    )
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
