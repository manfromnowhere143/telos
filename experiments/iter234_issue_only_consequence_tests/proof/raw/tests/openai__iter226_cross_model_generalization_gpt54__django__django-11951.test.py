import uuid

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
            SECRET_KEY="test",
        )
    django.setup()

    table_name = "bulk_batch_" + uuid.uuid4().hex

    class BatchItem(models.Model):
        first = models.IntegerField()
        second = models.IntegerField()
        third = models.IntegerField()
        fourth = models.IntegerField()

        class Meta:
            app_label = "bulk_batch_test"
            db_table = table_name

    with connection.schema_editor() as editor:
        editor.create_model(BatchItem)

    inserts = []

    def capture(execute, sql, params, many, context):
        if sql.lstrip().upper().startswith("INSERT"):
            inserts.append(len(params or ()))
        return execute(sql, params, many, context)

    objects = [
        BatchItem(first=n, second=n, third=n, fourth=n)
        for n in range(300)
    ]
    with connection.execute_wrapper(capture):
        BatchItem.objects.bulk_create(objects, batch_size=len(objects))

    limit = connection.features.max_query_params
    assert limit is not None
    assert len(inserts) > 1
    assert all(count <= limit for count in inserts)
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'insert batch exceeded parameter limit')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
