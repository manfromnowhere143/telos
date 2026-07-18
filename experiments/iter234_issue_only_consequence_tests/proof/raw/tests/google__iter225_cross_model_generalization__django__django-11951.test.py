import django
from django.conf import settings
from django.db import models

try:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=['django.contrib.contenttypes'],
    )
    django.setup()

    class TestModel(models.Model):
        name = models.CharField(max_length=10)

        class Meta:
            app_label = 'contenttypes'
            db_table = 'test_model'

    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(TestModel)

    # Monkey patch bulk_batch_size to return a small number (2).
    # This simulates a strict database limit to test if the explicit
    # batch_size provided to bulk_create correctly respects max_batch_size.
    original_bulk_batch_size = connection.ops.bulk_batch_size
    connection.ops.bulk_batch_size = lambda fields, objs: 2

    objs = [TestModel(name=str(i)) for i in range(5)]

    with CaptureQueriesContext(connection) as ctx:
        TestModel.objects.bulk_create(objs, batch_size=10)

    connection.ops.bulk_batch_size = original_bulk_batch_size

    # Filter out transaction queries (like SAVEPOINT or COMMIT) 
    # to only count the actual batched INSERTs.
    insert_queries = [q['sql'] for q in ctx.captured_queries if 'INSERT INTO' in q['sql'].upper()]
    num_inserts = len(insert_queries)

    if num_inserts == 1:
        print(f"RESULT={('FAIL', 'batch_size overrode max_batch_size')!r}")
    elif num_inserts == 3:
        # Expected: batch_size is min(10, 2) = 2.
        # 5 items / 2 items per batch = 3 batches total.
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', f'Unexpected number of insert queries: {num_inserts}')!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
