import django
from django.conf import settings


class ForceContentTypeWritesToDefault:
    def db_for_write(self, model, **hints):
        if model._meta.app_label == "contenttypes":
            return "default"
        return None


try:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes"],
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
            "target": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        },
        DATABASE_ROUTERS=[ForceContentTypeWritesToDefault()],
        SECRET_KEY="test",
    )
    django.setup()

    from django.apps import apps
    from django.contrib.contenttypes.management import RenameContentType
    from django.contrib.contenttypes.models import ContentType
    from django.db import connections
    from django.db.migrations.state import ProjectState

    with connections["target"].schema_editor() as editor:
        editor.create_model(ContentType)
        ContentType.objects.using("target").create(
            app_label="widgets", model="oldthing"
        )
        state = ProjectState.from_apps(apps)
        RenameContentType("widgets", "oldthing", "newthing").database_forwards(
            "widgets", editor, state, state
        )

    renamed = ContentType.objects.using("target").get(app_label="widgets")
    assert renamed.model == "newthing"
    assert not ContentType.objects.using("target").filter(
        app_label="widgets", model="oldthing"
    ).exists()
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'content type not renamed on target')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
