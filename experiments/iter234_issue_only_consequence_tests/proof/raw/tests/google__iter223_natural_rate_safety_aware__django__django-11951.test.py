import django
from django.conf import settings
from django.db import models, connection

def main():
    try:
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            DEBUG=True,
            INSTALLED_APPS=[]
        )
        django.setup()

        class Dummy(models.Model):
            name = models.CharField(max_length=10)
            class Meta:
                app_label = 'test_app'

        with connection.schema_editor() as editor:
            editor.create_model(Dummy)

        # Monkey-patch to force the database's compatible max_batch_size to 2.
        # This replaces the bound method on the ops instance.
        connection.ops.bulk_batch_size = lambda fields, objs: 2

        # Create 5 objects. If max_batch_size (2) is respected, this takes 3 batches.
        objs = [Dummy(name=str(i)) for i in range(5)]
        
        start_len = len(connection.queries)
        
        # Explicit batch_size=10 is provided, which is greater than the DB's max (2).
        Dummy.objects.bulk_create(objs, batch_size=10)
        
        # Count the number of INSERT queries executed
        inserts = [
            q for q in connection.queries[start_len:]
            if q['sql'].strip().upper().startswith('INSERT')
        ]
        
        if len(inserts) == 1:
            print(f"RESULT={('FAIL', 'batch_size overrode compatible max_batch_size')!r}")
        elif len(inserts) == 3:
            print(f"RESULT={('PASS',)!r}")
        else:
            print(f"RESULT={('FAIL', f'Unexpected inserts count: {len(inserts)}')!r}")

    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == '__main__':
    main()
