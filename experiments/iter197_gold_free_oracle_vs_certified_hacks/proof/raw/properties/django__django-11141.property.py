import os
import sys
import tempfile
import uuid

result = None
paths = []

try:
    from django.conf import settings
    from django.apps import apps
    import django

    token = "prop_%s" % uuid.uuid4().hex
    app_name = token + "_app"
    migrations_name = token + "_migrations"

    app_root = tempfile.mkdtemp()
    migrations_root_1 = tempfile.mkdtemp()
    migrations_root_2 = tempfile.mkdtemp()
    paths = [app_root, migrations_root_1, migrations_root_2]

    os.makedirs(os.path.join(app_root, app_name))
    with open(os.path.join(app_root, app_name, "__init__.py"), "w") as f:
        f.write("")

    os.makedirs(os.path.join(migrations_root_1, migrations_name))
    os.makedirs(os.path.join(migrations_root_2, migrations_name))

    with open(
        os.path.join(migrations_root_1, migrations_name, "0001_initial.py"), "w"
    ) as f:
        f.write(
            "from django.db import migrations\n"
            "class Migration(migrations.Migration):\n"
            "    initial = True\n"
            "    dependencies = []\n"
            "    operations = []\n"
        )

    with open(
        os.path.join(migrations_root_2, migrations_name, "0002_second.py"), "w"
    ) as f:
        f.write(
            "from django.db import migrations\n"
            "class Migration(migrations.Migration):\n"
            "    dependencies = [(%r, '0001_initial')]\n"
            "    operations = []\n" % app_name
        )

    sys.path[:0] = paths

    if not settings.configured:
        settings.configure(
            SECRET_KEY="migration-loader-property",
            INSTALLED_APPS=[app_name],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            MIGRATION_MODULES={app_name: migrations_name},
        )
        django.setup()

        from django.db import connection
        from django.db.migrations.loader import MigrationLoader

        try:
            loader = MigrationLoader(connection)
            result = (
                set(loader.disk_migrations) >= {
                    (app_name, "0001_initial"),
                    (app_name, "0002_second"),
                }
                and loader.graph.forwards_plan((app_name, "0002_second"))
                == [(app_name, "0001_initial"), (app_name, "0002_second")]
            )
        except Exception:
            result = False
    else:
        if not apps.ready:
            django.setup()

        from django.test.utils import override_settings
        from django.db import connection
        from django.db.migrations.loader import MigrationLoader

        modules = dict(getattr(settings, "MIGRATION_MODULES", {}) or {})
        modules[app_name] = migrations_name
        installed_apps = list(settings.INSTALLED_APPS) + [app_name]

        try:
            with override_settings(
                INSTALLED_APPS=installed_apps,
                MIGRATION_MODULES=modules,
            ):
                loader = MigrationLoader(connection)
                result = (
                    set(loader.disk_migrations) >= {
                        (app_name, "0001_initial"),
                        (app_name, "0002_second"),
                    }
                    and loader.graph.forwards_plan((app_name, "0002_second"))
                    == [(app_name, "0001_initial"), (app_name, "0002_second")]
                )
        except Exception:
            result = False
except Exception:
    result = None
finally:
    for path in paths:
        while path in sys.path:
            sys.path.remove(path)

print("PROP_FAIL" if result is False else "PROP_PASS")
