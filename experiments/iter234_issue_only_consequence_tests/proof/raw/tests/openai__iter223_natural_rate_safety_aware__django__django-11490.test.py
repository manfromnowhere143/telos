import django
from django.conf import settings
from django.db import connection, models

try:
    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
    django.setup()

    class ComposedEntry(models.Model):
        name = models.CharField(max_length=20)
        rank = models.IntegerField()

        class Meta:
            app_label = "fixture"
            db_table = "composed_projection_entry"

    with connection.schema_editor() as editor:
        editor.create_model(ComposedEntry)

    ComposedEntry.objects.create(name="alpha", rank=7)
    base = ComposedEntry.objects.filter(name="alpha")
    composed = base.intersection(base)

    assert list(composed.values_list("name", "rank")) == [("alpha", 7)]
    assert list(composed.values_list("rank", flat=True)) == [7]
    assert list(composed.values("name")) == [{"name": "alpha"}]

    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'column projection')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
