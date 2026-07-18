import django
from django.conf import settings
from django.apps import apps
from django.db import connections
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import RenameContentType

try:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=["django.contrib.contenttypes"],
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
            "other": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        },
    )
    django.setup()

    with connections["other"].schema_editor() as editor:
        editor.create_model(ContentType)

    ContentType.objects.using("other").create(
        app_label="contenttypes",
        model="oldname",
    )

    with connections["other"].schema_editor() as editor:
        RenameContentType(
            "contenttypes", "oldname", "newname"
        ).rename_contenttypes(apps, editor)

    observed = ContentType.objects.using("other").get(
        app_label="contenttypes"
    ).model
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
