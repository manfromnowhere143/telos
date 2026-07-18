import django
from django.conf import settings

def test():
    if not settings.configured:
        settings.configure(
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes'],
            DEBUG=True
        )
    django.setup()

    from django.db import models, connection

    class MyModel(models.Model):
        name = models.CharField(max_length=100)

        class Meta:
            app_label = 'auth'
            db_table = 'my_model'

    with connection.schema_editor() as editor:
        editor.create_model(MyModel)

    # We mock the database operations' bulk_batch_size calculation.
    # The fix ensures that if an explicit batch_size is provided, bulk_create 
    # uses min(batch_size, max_batch_size). 
    # The bug allowed the explicit batch_size to override max_batch_size completely.
    def mock_bulk_batch_size(*args, **kwargs):
        return 2

    connection.ops.bulk_batch_size = mock_bulk_batch_size

    objs = [MyModel(name=f"obj{i}") for i in range(5)]

    initial_len = len(connection.queries)
    
    # We pass an explicit batch_size of 10.
    # Buggy behaviour: ignores mock_bulk_batch_size(2) and tries to insert all 5 items in 1 query.
    # Fixed behaviour: uses min(10, 2) = 2, and splits the 5 items into 3 queries (2, 2, 1).
    MyModel.objects.bulk_create(objs, batch_size=10)

    new_queries = connection.queries[initial_len:]
    queries = [q for q in new_queries if "INSERT" in q['sql'].upper()]
    
    if len(queries) == 3:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', f'Expected 3 queries, got {len(queries)}')!r}")

try:
    test()
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
