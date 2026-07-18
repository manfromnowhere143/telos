import django
from django.conf import settings

try:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()

    from django.db import connection, models
    from django.db.models.sql.compiler import SQLInsertCompiler

    class Thing(models.Model):
        name = models.CharField(max_length=10)
        class Meta:
            app_label = 'contenttypes'

    with connection.schema_editor() as se:
        se.create_model(Thing)

    # compute max_batch_size like the framework
    fields = Thing._meta.local_fields
    max_batch_size = connection.ops.bulk_batch_size(fields, [Thing() for _ in range(10)])

    # request a batch_size larger than max; effective must be min(batch_size, max)
    requested = max_batch_size + 100
    effective = min(requested, max_batch_size) if requested else max_batch_size

    captured = []
    orig = SQLInsertCompiler.execute_sql
    def patched(self, *a, **k):
        captured.append(len(self.query.objs))
        return orig(self, *a, **k)
    SQLInsertCompiler.execute_sql = patched

    try:
        objs = [Thing(name=str(i)) for i in range(effective + 5)]
        Thing.objects.bulk_create(objs, batch_size=requested)
    finally:
        SQLInsertCompiler.execute_sql = orig

    if not captured:
        print(f"RESULT={('FAIL', 'no inserts captured')!r}")
    else:
        biggest = max(captured)
        if biggest > max_batch_size:
            print(f"RESULT={('FAIL', f'batch {biggest} exceeds max {max_batch_size}')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
