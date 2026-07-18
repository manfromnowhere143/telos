import django
from django.conf import settings
from django.db import models

def test_composed_queries_values():
    try:
        settings.configure(
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            INSTALLED_APPS=['django.contrib.contenttypes'],
        )
        django.setup()

        class ReservedName(models.Model):
            name = models.CharField(max_length=255)
            order = models.IntegerField()

            class Meta:
                app_label = 'contenttypes'

        from django.db import connection
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(ReservedName)

        ReservedName.objects.create(name='a', order=2)

        qs1 = ReservedName.objects.all()
        
        # Issue mentions this specific sequence of operations
        res1 = qs1.union(qs1).values_list('name', 'order').get()
        if res1 != ('a', 2):
            print(f"RESULT={('FAIL', f'Initial values_list failed: {res1}')!r}")
            return

        res2 = qs1.union(qs1).values_list('order').get()
        if res2 != (2,):
            print(f"RESULT={('FAIL', f'values_list returned incorrect columns: {res2}')!r}")
            return

        res3 = qs1.union(qs1).values('order').get()
        if res3 != {'order': 2}:
            print(f"RESULT={('FAIL', f'values returned incorrect columns: {res3}')!r}")
            return

        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == '__main__':
    test_composed_queries_values()
