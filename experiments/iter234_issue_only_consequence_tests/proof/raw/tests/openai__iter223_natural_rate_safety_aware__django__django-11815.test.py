from enum import Enum

try:
    from django.conf import settings
    from django.db import migrations, models
    from django.db.migrations.writer import MigrationWriter
    from django.utils.translation import gettext_lazy

    if not settings.configured:
        settings.configure(SECRET_KEY="fixture", USE_I18N=True)

    class Status(Enum):
        GOOD = gettext_lazy("Good")
        BAD = gettext_lazy("Bad")

        def __str__(self):
            return self.name

    migration = migrations.Migration("enum_default", "fixture")
    migration.operations = [
        migrations.CreateModel(
            name="Item",
            fields=[
                ("status", models.CharField(default=Status.GOOD, max_length=128)),
            ],
        ),
    ]
    rendered = MigrationWriter(migration).as_string()
    assert "Status['GOOD']" in rendered
    assert "Status('Good')" not in rendered
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    detail = "enum-name"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
