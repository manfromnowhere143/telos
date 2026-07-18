import django
from django.conf import settings

try:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
            'other': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()

    from django.core.management import call_command
    from django.contrib.contenttypes.management import RenameContentType
    from django.contrib.contenttypes.models import ContentType
    from django.db import connections

    # Migrate ONLY the 'other' database; leave 'default' without tables.
    call_command('migrate', 'contenttypes', database='other', verbosity=0, run_syncdb=True)

    # Create a content type on 'other' only.
    ContentType.objects.using('other').create(app_label='myapp', model='oldname')

    # Build a fake schema_editor pointing at 'other'.
    class FakeSchemaEditor:
        connection = connections['other']

    op = RenameContentType('myapp', 'oldname', 'newname')
    # This should operate on 'other' db, not touch 'default' (which has no tables).
    op._rename(None, FakeSchemaEditor(), 'oldname', 'newname')

    ct = ContentType.objects.using('other').get(app_label='myapp')
    if ct.model != 'newname':
        print(f"RESULT={('FAIL', 'model not renamed on other db')!r}")
    else:
        # Confirm default db was never touched (no such table would raise otherwise).
        exists_default = ContentType.objects.using('default').filter(app_label='myapp').exists()
        # If we get here without error, save used correct db.
        print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
