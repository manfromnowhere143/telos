import uuid

try:
    import django
    from django.conf import settings
    from django.db import connection, models
    from django.test.utils import CaptureQueriesContext

    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            INSTALLED_APPS=[],
            SECRET_KEY="test",
        )
    django.setup()

    table_name = "bulk_limit_" + uuid.uuid4().hex
    attributes = {
        "__module__": __name__,
        "Meta": type("Meta", (), {"app_label": "tests", "db_table": table_name}),
    }
    for index in range(10):
        attributes[f"field{index}"] = models.IntegerField()
    Thing = type("BulkLimitThing", (models.Model,), attributes)

    with connection.schema_editor() as editor:
        editor.create_model(Thing)

    objects = [
        Thing(**{f"field{field}": row + field for field in range(10)})
        for row in range(100)
    ]
    fields = [field for field in Thing._meta.concrete_fields if not field.primary_key]
    maximum = connection.ops.bulk_batch_size(fields, objects)
    assert maximum < len(objects)

    with CaptureQueriesContext(connection) as captured:
        Thing.objects.bulk_create(objects, batch_size=len(objects))

    inserts = [
        query for query in captured.captured_queries
        if query["sql"].lstrip().upper().startswith("INSERT")
    ]
    expected = (len(objects) + maximum - 1) // maximum
    assert len(inserts) == expected
    assert Thing.objects.count() == len(objects)
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    detail = "batch limit"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
