import uuid

import django
from django.conf import settings
from django.db import connection, models

try:
    settings.configure(
        SECRET_KEY="consequence-test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
    django.setup()

    class Sample(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4)
        name = models.CharField(blank=True, max_length=100)

        class Meta:
            app_label = "consequence_test"

    with connection.schema_editor() as editor:
        editor.create_model(Sample)

    original = Sample.objects.create()
    replacement = Sample(pk=original.pk, name="updated")
    replacement.save()

    assert Sample.objects.count() == 1, "duplicate row"
    assert Sample.objects.get(pk=original.pk).name == "updated", "existing pk not updated"

    new_pk = uuid.uuid4()
    Sample(pk=new_pk, name="new").save()
    assert Sample.objects.get(pk=new_pk).name == "new", "new explicit pk not inserted"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion failed"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
