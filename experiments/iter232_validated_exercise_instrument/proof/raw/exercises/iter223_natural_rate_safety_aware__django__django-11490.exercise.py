try:
    import django
    from django.conf import settings
    from django.db import connection, models

    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        SECRET_KEY="fixture",
    )
    django.setup()

    class ReservedName(models.Model):
        name = models.CharField(max_length=20)
        order = models.IntegerField()

        class Meta:
            app_label = "fixture"

    with connection.schema_editor() as editor:
        editor.create_model(ReservedName)

    ReservedName.objects.create(name="a", order=2)
    base = ReservedName.objects.all()
    combined = base.union(base)

    result = (
        combined.values_list("name", "order").get(),
        combined.values_list("order").get(),
        base.union(base).values("order").get(),
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
