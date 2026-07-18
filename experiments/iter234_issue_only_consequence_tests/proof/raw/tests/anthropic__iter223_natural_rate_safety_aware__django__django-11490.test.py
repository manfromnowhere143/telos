import django
from django.conf import settings

try:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    )
    django.setup()

    from django.db import models, connection
    from django.apps import apps

    class ReservedName(models.Model):
        name = models.CharField(max_length=100)
        order = models.IntegerField()

        class Meta:
            app_label = 'testapp'

    with connection.schema_editor() as se:
        se.create_model(ReservedName)

    ReservedName.objects.create(name='a', order=2)
    qs1 = ReservedName.objects.all()

    both = qs1.union(qs1).values_list('name', 'order').get()
    single = qs1.union(qs1).values_list('order').get()

    if both != ('a', 2):
        print(f"RESULT={('FAIL', f'both={both!r}')!r}")
    elif single != (2,):
        print(f"RESULT={('FAIL', f'single={single!r}')!r}")
    else:
        print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
