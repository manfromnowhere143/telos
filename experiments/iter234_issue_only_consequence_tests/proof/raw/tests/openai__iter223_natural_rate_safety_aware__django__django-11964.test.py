import django
from django.conf import settings
from django.db import connection, models

try:
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
    django.setup()

    class TextChoice(models.TextChoices):
        FIRST = "first", "First"

    class IntegerChoice(models.IntegerChoices):
        SEVEN = 7, "Seven"

    class Fixture(models.Model):
        text = models.CharField(max_length=10, choices=TextChoice.choices)
        number = models.IntegerField(choices=IntegerChoice.choices)

        class Meta:
            app_label = "consequence_fixture"

    with connection.schema_editor() as editor:
        editor.create_model(Fixture)

    created = Fixture.objects.create(
        text=TextChoice.FIRST,
        number=IntegerChoice.SEVEN,
    )
    retrieved = Fixture.objects.get(pk=created.pk)

    for obj in (created, retrieved):
        assert isinstance(obj.text, str)
        assert isinstance(obj.number, int)
        assert str(obj.text) == "first"
        assert str(obj.number) == "7"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "choice string value"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
