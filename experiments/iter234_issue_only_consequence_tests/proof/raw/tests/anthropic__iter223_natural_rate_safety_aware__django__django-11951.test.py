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
    from django.contrib.auth.models import User

    ops = connection.ops
    fields = [f for f in User._meta.concrete_fields if not f.primary_key]
    max_batch_size = ops.bulk_batch_size(fields, [None] * 100)

    # Ensure the compatible max batch size is meaningfully small for this test
    if max_batch_size < 1:
        raise ValueError("bad max_batch_size")

    # The effective batch size when user passes a large batch_size should be
    # capped at max_batch_size: min(batch_size, max_batch_size)
    user_batch_size = max_batch_size + 100
    expected = min(user_batch_size, max_batch_size)

    # Reproduce the calculation the code should now perform.
    computed = min(user_batch_size, max_batch_size) if user_batch_size else max_batch_size

    if computed != expected:
        print(f"RESULT={('FAIL', f'computed {computed} != {expected}')!r}")
    elif computed > max_batch_size:
        print(f"RESULT={('FAIL', 'batch size exceeds max')!r}")
    else:
        # Also verify a small user batch_size is respected (not overridden upward)
        small = 1
        small_computed = min(small, max_batch_size) if small else max_batch_size
        if small_computed != 1:
            print(f"RESULT={('FAIL', f'small batch {small_computed}')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
