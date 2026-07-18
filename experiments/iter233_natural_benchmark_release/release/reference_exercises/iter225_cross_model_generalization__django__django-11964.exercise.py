try:
    from django.conf import settings
    import django
    from django.apps import apps
    from django.db import connection, models

    if not settings.configured:
        settings.configure(
            SECRET_KEY="fixture",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    if not apps.ready:
        django.setup()

    class TextValue(models.TextChoices):
        FIRST = "first", "First"
        SECOND = "second", "Second"

    class IntegerValue(models.IntegerChoices):
        ONE = 1, "One"
        TWO = 2, "Two"

    class ChoiceFixture(models.Model):
        text = models.CharField(max_length=10, choices=TextValue.choices)
        number = models.IntegerField(choices=IntegerValue.choices)

        class Meta:
            app_label = "choice_fixture"

    with connection.schema_editor() as editor:
        editor.create_model(ChoiceFixture)

    created = ChoiceFixture.objects.create(
        text=TextValue.FIRST,
        number=IntegerValue.ONE,
    )
    retrieved = ChoiceFixture.objects.get(pk=created.pk)

    result = (
        (
            type(created.text).__name__,
            str(created.text),
            type(retrieved.text).__name__,
            str(retrieved.text),
        ),
        (
            type(created.number).__name__,
            str(created.number),
            type(retrieved.number).__name__,
            str(retrieved.number),
        ),
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
