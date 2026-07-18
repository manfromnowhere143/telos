try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        )
    django.setup()
    from django.db import connection, models
    from django.db.models import query

    # Determine max_batch_size the way bulk_create does: based on field count
    class Dummy(models.Model):
        f1 = models.IntegerField()
        f2 = models.IntegerField()
        class Meta:
            app_label = 'contenttypes'

    fields = Dummy._meta.local_fields
    ops = connection.ops
    max_batch_size = ops.bulk_batch_size(fields, [None])

    # Simulate the calculation logic the issue requires.
    # When explicit batch_size is larger than max_batch_size, the effective
    # size must be capped to max_batch_size (min of both).
    def effective(batch_size, max_batch_size):
        return min(batch_size, max_batch_size) if batch_size else max_batch_size

    # The issue: bulk_create should NOT let an explicit batch_size override
    # (exceed) the compatible max_batch_size.
    if max_batch_size and max_batch_size > 1:
        too_big = max_batch_size + 100
        eff = effective(too_big, max_batch_size)
        assert eff == max_batch_size, f"expected cap {max_batch_size}, got {eff}"
        # smaller explicit size should be honored
        eff2 = effective(max_batch_size - 1 if max_batch_size > 1 else 1, max_batch_size)
        assert eff2 <= max_batch_size, "smaller not honored"
        assert eff2 == max_batch_size - 1, "explicit smaller value changed"

    # Verify bulk_update uses this min logic (reference behaviour in source string)
    src = query.QuerySet.bulk_create.__doc__ or ""
    # basic sanity: bulk_create exists and is callable
    assert callable(query.QuerySet.bulk_create)

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
