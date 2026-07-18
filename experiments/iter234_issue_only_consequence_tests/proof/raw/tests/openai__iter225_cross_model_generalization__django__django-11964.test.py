from django.conf import settings
import django
from django.db import connection, models

detail = "enum field coercion"
try:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
    django.setup()

    class TextValue(models.TextChoices):
        FIRST = "first", "First"

    class IntegerValue(models.IntegerChoices):
        SEVEN = 7, "Seven"

    class Sample(models.Model):
        text = models.CharField(max_length=10, choices=TextValue.choices)
        number = models.IntegerField(choices=IntegerValue.choices)

        class Meta:
            app_label = "enum_fixture"

    with connection.schema_editor() as editor:
        editor.create_model(Sample)

    created = Sample.objects.create(text=TextValue.FIRST, number=IntegerValue.SEVEN)
    assert isinstance(created.text, str)
    assert isinstance(created.number, int)
    assert str(created.text) == "first"
    assert str(created.number) == "7"

    retrieved = Sample.objects.get(pk=created.pk)
    assert type(retrieved.text) is str
    assert type(retrieved.number) is int
    assert retrieved.text == "first"
    assert retrieved.number == 7
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
