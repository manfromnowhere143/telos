import django
from django.conf import settings

try:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    )
    django.setup()

    from uuid import uuid4
    from django.db import models, connection

    class Sample(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid4)
        name = models.CharField(blank=True, max_length=100)

        class Meta:
            app_label = 'testapp'

    with connection.schema_editor() as se:
        se.create_model(Sample)

    s0 = Sample.objects.create()
    # Now saving a new instance with explicit existing pk should UPDATE, not INSERT
    s1 = Sample(pk=s0.pk, name='Test 1')
    s1.save()

    count = Sample.objects.count()
    if count != 1:
        print(f"RESULT={('FAIL', f'expected 1 row, got {count}')!r}")
    else:
        obj = Sample.objects.get(pk=s0.pk)
        if obj.name != 'Test 1':
            print(f"RESULT={('FAIL', f'name={obj.name!r}')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
