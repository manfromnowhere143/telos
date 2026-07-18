import enum
import re

try:
    import django
    from django.conf import settings
    from django.db import models
    from django.db.migrations import AddField, Migration
    from django.db.migrations.writer import MigrationWriter
    from django.utils.translation import gettext_lazy

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            USE_I18N=True,
            INSTALLED_APPS=[],
        )
        django.setup()

    class Status(enum.Enum):
        GOOD = gettext_lazy("Good")
        BAD = gettext_lazy("Bad")

        def __str__(self):
            return self.name

    migration = Migration("0001_initial", "example")
    migration.operations = [
        AddField(
            model_name="item",
            name="status",
            field=models.CharField(max_length=128, default=Status.GOOD),
        )
    ]
    rendered = MigrationWriter(migration).as_string()

    if "Status['GOOD']" not in rendered:
        raise AssertionError("enum-default")
    if re.search(r"Status\(", rendered):
        raise AssertionError("enum-value")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
