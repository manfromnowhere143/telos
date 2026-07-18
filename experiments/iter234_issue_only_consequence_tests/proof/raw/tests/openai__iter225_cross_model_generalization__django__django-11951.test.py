try:
    import django
    from django.conf import settings
    from django.db import connection, models
    from django.test.utils import CaptureQueriesContext

    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

    class MixedBatchModel(models.Model):
        first = models.IntegerField()
        second = models.IntegerField()

        class Meta:
            app_label = "consequence"
            db_table = "consequence_mixed_batch_model"

    with connection.schema_editor() as editor:
        editor.create_model(MixedBatchModel)

    objects = [
        MixedBatchModel(id=index, first=index, second=-index)
        for index in range(1, 1001)
    ]
    objects += [
        MixedBatchModel(first=index, second=-index)
        for index in range(1001, 2001)
    ]

    with CaptureQueriesContext(connection) as queries:
        MixedBatchModel.objects.bulk_create(objects, batch_size=1000)

    inserts = sum("INSERT" in query["sql"].upper() for query in queries)
    assert inserts == 7, "batch-count"
    assert MixedBatchModel.objects.count() == 2000, "object-count"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
