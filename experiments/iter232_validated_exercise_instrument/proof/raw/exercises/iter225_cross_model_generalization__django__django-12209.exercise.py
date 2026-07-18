import uuid

from django.conf import settings

try:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        SECRET_KEY="test",
    )

    import django
    from django.db import connection, models

    django.setup()

    class Sample(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4)
        name = models.CharField(blank=True, max_length=100)

        class Meta:
            app_label = "fixture"

    with connection.schema_editor() as editor:
        editor.create_model(Sample)

    original = Sample.objects.create()
    replacement = Sample(pk=original.pk, name="Test 1")
    replacement.save()

    stored = Sample.objects.get(pk=original.pk)
    print("RESULT=" + repr((Sample.objects.count(), stored.name)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
