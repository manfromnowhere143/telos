import uuid
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
            INSTALLED_APPS=['__main__'],
            TIME_ZONE='UTC',
            USE_TZ=True,
        )
        django.setup()

        class Sample(models.Model):
            id = models.UUIDField(primary_key=True, default=uuid.uuid4)
            name = models.CharField(blank=True, max_length=100)

            class Meta:
                app_label = '__main__'

        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(Sample)

        # Create the initial record
        s0 = Sample.objects.create()
        
        # Instantiate a new object with the same explicitly set primary key
        s1 = Sample(pk=s0.pk, name='Test 1')
        
        # Save should perform an UPDATE rather than trying to INSERT (which would raise IntegrityError)
        s1.save()

        # Retrieve and verify it was updated
        s_from_db = Sample.objects.get(pk=s0.pk)
        if s_from_db.name == 'Test 1':
            print(f"RESULT={('PASS',)!r}")
        else:
            print(f"RESULT={('FAIL', 'Instance was not updated correctly.')!r}")

    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == '__main__':
    main()
